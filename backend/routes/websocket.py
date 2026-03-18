import json
import base64
import asyncio
import io
import wave
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from openai import AsyncOpenAI

from backend.config import settings
from backend.memory.session import (
    create_session, get_session, add_turn, update_session, end_session, get_conversation_history
)
from backend.services.sentiment import score_sentiment
from backend.services.escalation import check_escalation
from backend.services.intent import classify_intent
from backend.services.llm import generate_response

router = APIRouter()
aclient = AsyncOpenAI(api_key=settings.openai_api_key)

@router.websocket("/ws/{call_id}")
async def realtime_call(websocket: WebSocket, call_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected | call: {call_id}")

    session = get_session(call_id)
    if not session:
        session = create_session()
        call_id = session["call_id"]

    audio_buffer = bytearray()

    try:
        greeting_text = "Hello! I am Priya from ShopNow customer support. How can I help you today?"
        await send_agent_response(websocket, call_id, greeting_text)

        while True:
            message = await websocket.receive()

            if "bytes" in message:
                audio_buffer.extend(message["bytes"])
            elif "text" in message:
                control = json.loads(message["text"])
                msg_type = control.get("type")

                if msg_type == "commit_audio":
                    logger.info(f"Buffer committed | call: {call_id} | size: {len(audio_buffer)} bytes")
                    if len(audio_buffer) > 0:
                        # Copy bytes before clearing
                        turn_bytes = bytes(audio_buffer)
                        audio_buffer.clear()
                        # Run turn processing in background
                        asyncio.create_task(process_turn(websocket, call_id, turn_bytes))
                        
                elif msg_type == "end_call":
                    end_session(call_id, "resolved")
                    await websocket.send_text(json.dumps({
                        "type": "call_ended",
                        "call_id": call_id
                    }))
                    logger.info(f"Call ended | call: {call_id}")
                    break

    except WebSocketDisconnect:
        logger.info(f"Browser disconnected | call: {call_id}")
        end_session(call_id, "resolved")

    except Exception as e:
        logger.error(f"WebSocket error | call: {call_id} | {e}")
        try:
            await websocket.close()
        except:
            pass


async def send_agent_response(websocket: WebSocket, call_id: str, text: str):
    add_turn(call_id=call_id, role="agent", text=text)
    
    await websocket.send_text(json.dumps({
        "type": "transcript",
        "role": "agent",
        "text": text
    }))
    
    logger.info(f"Generating TTS for: {text[:40]}...")
    try:
        async with aclient.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="shimmer",
            input=text,
            response_format="pcm"
        ) as response:
            async for chunk in response.iter_bytes(chunk_size=4096):
                if chunk:
                    await websocket.send_bytes(chunk)
                
    except Exception as e:
        logger.error(f"TTS Error: {e}")

async def process_turn(websocket: WebSocket, call_id: str, pcm_bytes: bytes):
    try:
        wav_io = io.BytesIO()
        try:
            with wave.open(wav_io, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(24000)
                wav_file.writeframes(pcm_bytes)
        except Exception as e:
            logger.error(f"Failed to write wav: {e}")
            return
            
        wav_io.name = "audio.wav"
        wav_io.seek(0)

        logger.info("Sending to STT...")
        transcript_response = await aclient.audio.transcriptions.create(
            model="whisper-1",
            file=wav_io,
            response_format="verbose_json"
        )
        
        transcript = transcript_response.text.strip()
        if not transcript:
            logger.warning("Empty transcript received. Skipping turn.")
            return

        logger.info(f"Customer said: {transcript}")

        session = get_session(call_id)
        sentiment = score_sentiment(transcript)
        history = get_conversation_history(call_id)
        
        loop = asyncio.get_event_loop()
        intent_result = await loop.run_in_executor(None, classify_intent, transcript, history)
        intent = intent_result["intent"]
        entities = intent_result["entities"]

        add_turn(
            call_id=call_id,
            role="customer",
            text=transcript,
            intent=intent,
            sentiment=sentiment["label"]
        )
        update_session(call_id, current_intent=intent)

        await websocket.send_text(json.dumps({
            "type": "transcript",
            "role": "customer",
            "text": transcript,
            "intent": intent,
            "sentiment": sentiment["label"]
        }))

        # Handle escalation
        escalation = check_escalation(session)
        if escalation["should_escalate"]:
            await websocket.send_text(json.dumps({
                "type": "escalation",
                "message": escalation["message"],
                "escalation_brief": escalation["brief"]
            }))
            end_session(call_id, "escalated")
            return

        # Use the generate_response from llm.py
        response_text = await generate_response(
            call_id=call_id,
            user_text=transcript,
            intent=intent,
            entities=entities
        )
        
        await send_agent_response(websocket, call_id, response_text)

    except Exception as e:
        logger.error(f"Error processing turn: {e}")
        traceback.print_exc()
