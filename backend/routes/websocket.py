import json
import base64
import asyncio
import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from backend.config import settings
from backend.memory.session import (
    create_session,
    get_session,
    add_turn,
    update_session,
    end_session,
    get_conversation_history
)
from backend.services.sentiment import score_sentiment
from backend.services.escalation import check_escalation
from backend.services.rag import retrieve_context
from backend.handlers import INTENT_HANDLERS
from backend.services.intent import classify_intent

router = APIRouter()

# Use the latest available realtime model
REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview"

AGENT_INSTRUCTIONS = """
You are Priya, ShopNow's friendly and empathetic customer support agent.
ShopNow is a D2C e-commerce brand delivering across India.

Your personality:
- Warm, patient and professional
- Speak in the same language the customer uses
- If customer speaks Hindi respond in Hindi
- If customer speaks Hinglish respond in Hinglish
- Keep responses short and clear — this is a voice call

Your capabilities:
- Check order status
- Initiate returns and refunds
- Resolve payment issues
- Handle delivery complaints
- Answer product queries

Rules:
- Never make up order details
- If you don't have enough information ask one clear question
- Always address the customer by name if you know it
- Be empathetic when the customer is frustrated
- Never say you are an AI unless directly asked
"""


@router.websocket("/ws/{call_id}")
async def realtime_call(websocket: WebSocket, call_id: str):

    await websocket.accept()
    logger.info(f"WebSocket connected | call: {call_id}")

    session = get_session(call_id)
    if not session:
        session = create_session()
        call_id = session["call_id"]

    try:
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "OpenAI-Beta":   "realtime=v1"
        }

        async with websockets.connect(
            REALTIME_URL,
            extra_headers=headers
        ) as openai_ws:

            logger.info(f"Connected to OpenAI Realtime API | call: {call_id}")

            # step 1 — configure session
            await openai_ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "modalities":  ["text", "audio"],
                    "instructions": AGENT_INSTRUCTIONS,
                    "voice":        "shimmer",
                    "input_audio_format":  "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": None,
                    "temperature": 0.7
                }
            }))

            # step 2 — send greeting as text message and request response
            await openai_ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [{
                        "type": "input_text",
                        "text": "Start the call. Greet the customer warmly in English and ask how you can help."
                    }]
                }
            }))

            await openai_ws.send(json.dumps({
                "type": "response.create",
                "response": {
                    "modalities": ["audio", "text"]
                }
            }))

            logger.info("Greeting requested")

            # step 3 — run both directions concurrently
            await asyncio.gather(
                receive_from_browser(websocket, openai_ws, session),
                receive_from_openai(openai_ws, websocket, session),
                return_exceptions=True
            )

    except WebSocketDisconnect:
        logger.info(f"Browser disconnected | call: {call_id}")
        end_session(call_id, "resolved")

    except Exception as e:
        logger.error(f"WebSocket error | call: {call_id} | {e}")
        try:
            await websocket.close()
        except:
            pass


async def receive_from_browser(browser_ws: WebSocket, openai_ws, session: dict):
    """
    Receives audio bytes from browser mic and control messages.
    Does NOT request responses — that is handled in receive_from_openai
    after transcription completes.
    """
    try:
        while True:
            message = await browser_ws.receive()

            # raw audio bytes from mic
            if "bytes" in message:
                audio_base64 = base64.b64encode(message["bytes"]).decode("utf-8")
                await openai_ws.send(json.dumps({
                    "type":  "input_audio_buffer.append",
                    "audio": audio_base64
                }))

            # control messages from frontend JS
            elif "text" in message:
                control  = json.loads(message["text"])
                msg_type = control.get("type")

                if msg_type == "commit_audio":
                    # user stopped speaking — commit buffer
                    # do NOT call response.create here
                    # transcription event will trigger it
                    await openai_ws.send(json.dumps({
                        "type": "input_audio_buffer.commit"
                    }))
                    logger.info(f"Buffer committed | call: {session['call_id']}")

                elif msg_type == "end_call":
                    end_session(session["call_id"], "resolved")
                    await browser_ws.send_text(json.dumps({
                        "type":    "call_ended",
                        "call_id": session["call_id"]
                    }))
                    logger.info(f"Call ended | call: {session['call_id']}")
                    break

    except Exception as e:
        logger.error(f"Browser receive error: {e}")


async def receive_from_openai(openai_ws, browser_ws: WebSocket, session: dict):
    """
    Receives all events from OpenAI Realtime API.
    Streams audio back to browser.
    Runs NLU pipeline after transcription.
    Requests response after context injection.
    """
    try:
        async for raw_message in openai_ws:
            event      = json.loads(raw_message)
            event_type = event.get("type", "")

            logger.info(f"OpenAI event: {event_type}")

            # ── 1. stream audio chunks to browser ────────
            if event_type == "response.audio.delta":
                audio_delta = event.get("delta", "")
                if audio_delta:
                    await browser_ws.send_bytes(
                        base64.b64decode(audio_delta)
                    )

            # ── 2. transcription complete ─────────────────
            elif event_type == "conversation.item.input_audio_transcription.completed":
                transcript = event.get("transcript", "").strip()
                if not transcript:
                    logger.warning("Empty transcript received — skipping")
                    continue

                logger.info(f"Customer said: {transcript}")

                # send transcript to browser for display
                sentiment     = score_sentiment(transcript)
                history       = get_conversation_history(session["call_id"])
                intent_result = classify_intent(transcript, history)
                intent        = intent_result["intent"]
                entities      = intent_result["entities"]

                add_turn(
                    call_id   = session["call_id"],
                    role      = "customer",
                    text      = transcript,
                    intent    = intent,
                    sentiment = sentiment["label"]
                )
                update_session(session["call_id"], current_intent=intent)

                # send to browser immediately so UI updates
                await browser_ws.send_text(json.dumps({
                    "type":      "transcript",
                    "role":      "customer",
                    "text":      transcript,
                    "intent":    intent,
                    "sentiment": sentiment["label"]
                }))

                # check escalation
                current_session = get_session(session["call_id"])
                escalation      = check_escalation(current_session)

                if escalation["should_escalate"]:
                    await browser_ws.send_text(json.dumps({
                        "type":             "escalation",
                        "message":          escalation["message"],
                        "escalation_brief": escalation["brief"]
                    }))
                    end_session(session["call_id"], "escalated")
                    return

                # fetch RAG + DB context
                rag_context = retrieve_context(transcript)
                db_context  = ""
                handler     = INTENT_HANDLERS.get(intent)
                if handler:
                    db_context = await handler(entities, current_session)

                # ── 3. context available but not injected into conversation yet ──
                # TODO: Find better way to inject context that works with Realtime API
                if rag_context or db_context:
                    logger.info(f"Context available | RAG: {len(rag_context)} chars | DB: {len(db_context)} chars")

                # ── 4. NOW request audio response ─────────────────
                await openai_ws.send(json.dumps({
                    "type": "response.create",
                    "response": {
                        "modalities": ["audio", "text"]
                    }
                }))
                logger.info("Response requested — waiting for audio deltas")

            # ── 5. agent finished speaking ────────────────
            elif event_type == "response.audio_transcript.done":
                transcript = event.get("transcript", "")
                if transcript:
                    add_turn(
                        call_id = session["call_id"],
                        role    = "agent",
                        text    = transcript
                    )
                    await browser_ws.send_text(json.dumps({
                        "type": "transcript",
                        "role": "agent",
                        "text": transcript
                    }))
                    logger.info(f"Agent said: {transcript}")

            # ── 6. response completed ─────────────────────
            elif event_type == "response.done":
                full_response = event.get("response", {})
                output = full_response.get("output", [])
                logger.info(f"Response done | output items: {len(output)} | response keys: {full_response.keys()}")
                
                if len(output) == 0:
                    logger.warning("Empty response — no audio was generated")
                    logger.debug(f"Full response object: {json.dumps(full_response, indent=2)}")

            # ── 7. session ready confirmation ─────────────
            elif event_type == "session.updated":
                logger.info("Session configured successfully")

            # ── 8. errors ─────────────────────────────────
            elif event_type == "error":
                error_msg = event.get("error", {}).get("message", "Unknown")
                logger.error(f"OpenAI error: {error_msg}")
                await browser_ws.send_text(json.dumps({
                    "type":    "error",
                    "message": error_msg
                }))

    except Exception as e:
        logger.error(f"OpenAI receive error: {e}")