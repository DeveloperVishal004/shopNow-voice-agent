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
from backend.utils.call_logger import save_call_to_folder

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
                    session_data = end_session(call_id, "resolved")
                    if session_data:
                        asyncio.create_task(save_call_to_folder(call_id, session_data))
                    await websocket.send_text(json.dumps({
                        "type": "call_ended",
                        "call_id": call_id
                    }))
                    logger.info(f"Call ended | call: {call_id}")
                    break

    except WebSocketDisconnect:
        logger.info(f"Browser disconnected | call: {call_id}")
        session_data = end_session(call_id, "resolved")
        if session_data:
            asyncio.create_task(save_call_to_folder(call_id, session_data))

    except Exception as e:
        logger.error(f"WebSocket error | call: {call_id} | {e}")
        try:
            await websocket.close()
        except:
            pass


async def send_agent_response(websocket: WebSocket, call_id: str, text: str, lang_code: str = "hi-IN"):
    add_turn(call_id=call_id, role="agent", text=text)
    
    await websocket.send_text(json.dumps({
        "type": "transcript",
        "role": "agent",
        "text": text
    }))
    
    logger.info(f"Generating TTS (Streaming) for: {text[:40]}...")
    try:
        import httpx
        payload = {
            "text": text,
            "target_language_code": lang_code,
            "speaker": "anushka",
            "model": "bulbul:v2",
            "pace": 1,
            "speech_sample_rate": 24000,
            "pitch": 0,
            "loudness": 1.5,
            "output_audio_codec": "linear16",
            "enable_preprocessing": True
        }
        headers = {
            "api-subscription-key": settings.sarvam_api_key,
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", "https://api.sarvam.ai/text-to-speech/stream", json=payload, headers=headers, timeout=30.0) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=4096):
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

        logger.info("Sending to Sarvam STT...")
        import httpx
        headers = {
            "api-subscription-key": settings.sarvam_api_key
        }
        wav_io.seek(0)
        files = {
            "file": ("audio.wav", wav_io.read(), "audio/wav")
        }
        data = {
            "model": "saaras:v3"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://api.sarvam.ai/speech-to-text", headers=headers, data=data, files=files, timeout=30.0)
            if resp.status_code != 200:
                logger.error(f"Sarvam STT failed: {resp.text}")
            resp.raise_for_status()
            stt_data = resp.json()
            transcript = stt_data.get("transcript", "").strip()
            detected_lang = stt_data.get("language_code", "hi-IN")
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
            session_data = end_session(call_id, "escalated")
            if session_data:
                asyncio.create_task(save_call_to_folder(call_id, session_data))
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
