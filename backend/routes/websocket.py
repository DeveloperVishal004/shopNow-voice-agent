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
    create_session, get_session, add_turn, update_session, end_session,
    get_conversation_history, record_intent_classification
)
from backend.services.sentiment import score_sentiment
from backend.services.escalation import check_escalation
from backend.services.intent import classify_intent
from backend.services.llm import generate_response
from backend.services.translate import needs_translation, translate_text
from backend.utils.call_logger import save_call_to_folder, save_escalation_log

router = APIRouter()
aclient = AsyncOpenAI(api_key=settings.openai_api_key)

# Languages the bulbul:v2 TTS voice can actually synthesize. Sarvam STT may
# detect a language outside this set (or return an unexpected code), so we
# guard the TTS target: an unsupported language falls back to English rather
# than failing synthesis and leaving the caller with silence.
TTS_SUPPORTED_LANGUAGES = {
    "en-IN", "hi-IN", "bn-IN", "gu-IN", "kn-IN", "ml-IN",
    "mr-IN", "od-IN", "pa-IN", "ta-IN", "te-IN",
}
TTS_FALLBACK_LANGUAGE = "en-IN"


def safe_tts_language(lang_code: str) -> str:
    """Return a TTS-supported language code, falling back if unsupported."""
    if lang_code and lang_code in TTS_SUPPORTED_LANGUAGES:
        return lang_code
    logger.warning(
        f"TTS language '{lang_code}' not supported — "
        f"falling back to {TTS_FALLBACK_LANGUAGE}"
    )
    return TTS_FALLBACK_LANGUAGE

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
        tts_lang = safe_tts_language(lang_code)
        payload = {
            "text": text,
            "target_language_code": tts_lang,
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

        # Normalize the detected language ONCE, up front, to one the voice model
        # supports. Using this same value for both the LLM reply and the TTS
        # keeps the spoken language and the generated text in agreement (avoids
        # e.g. Assamese text spoken by a Hindi voice).
        reply_lang = safe_tts_language(detected_lang)

        # Decide HOW to reach the reply language: for languages the LLM writes
        # fluently, generate directly in reply_lang. For low-resource languages,
        # generate in English and translate with Mayura afterwards (gen_lang is
        # what we ask the LLM to write in).
        gen_lang = "en-IN" if needs_translation(reply_lang) else reply_lang
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
        record_intent_classification(session, intent)

        add_turn(
            call_id=call_id,
            role="customer",
            text=transcript,
            intent=intent,
            sentiment=sentiment["label"]
        )
        update_session(call_id, current_intent=intent, language=reply_lang)

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
            await save_escalation_log(escalation["brief"])
            session_data = end_session(call_id, "escalated")
            if session_data:
                asyncio.create_task(save_call_to_folder(call_id, session_data))
            return

        # Use the generate_response from llm.py (tone adapts to sentiment)
        response_text = await generate_response(
            call_id=call_id,
            user_text=transcript,
            intent=intent,
            entities=entities,
            lang_code=gen_lang,
            sentiment=sentiment["label"]
        )

        # Re-check escalation after the data lookup ran, so the
        # "Data Not Found" rule can hand off the same turn it fails.
        session = get_session(call_id)
        escalation = check_escalation(session)
        if escalation["should_escalate"]:
            await websocket.send_text(json.dumps({
                "type": "escalation",
                "message": escalation["message"],
                "escalation_brief": escalation["brief"]
            }))
            await save_escalation_log(escalation["brief"])
            session_data = end_session(call_id, "escalated")
            if session_data:
                asyncio.create_task(save_call_to_folder(call_id, session_data))
            return

        # If we generated in English for a low-resource target, translate the
        # final reply into the caller's language before speaking it. (No-op /
        # returns source text unchanged when translation isn't needed or fails.)
        if gen_lang != reply_lang:
            response_text = await translate_text(
                response_text, target_lang_code=reply_lang, source_lang_code="en-IN"
            )

        await send_agent_response(websocket, call_id, response_text, reply_lang)

    except Exception as e:
        logger.error(f"Error processing turn: {e}")
        traceback.print_exc()
