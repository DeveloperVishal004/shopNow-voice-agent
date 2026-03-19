import os
import uuid
import requests
from loguru import logger
from backend.config import settings

AUDIO_OUTPUT_DIR = "./temp_audio/responses"
os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)

# Sarvam language mappings roughly map like this:
VOICE_MAP = {
    "en": "en-IN",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "bn": "bn-IN",
}

def text_to_speech(text: str, language: str = "en") -> dict:
    """
    Takes text + language, returns path to generated audio file
    """
    try:
        url = "https://api.sarvam.ai/text-to-speech/stream"
        headers = {
            "api-subscription-key": settings.sarvam_api_key,
            "Content-Type": "application/json"
        }
        
        target_lang = VOICE_MAP.get(language[:2].lower(), "hi-IN")
        
        payload = {
            "text": text,
            "target_language_code": target_lang,
            "speaker": "anushka",
            "model": "bulbul:v2",
            "pace": 1,
            "speech_sample_rate": 24000,
            "pitch": 0,
            "loudness": 1.5,
            # We use linear16 (PCM) rather than wave base64 now
            "output_audio_codec": "linear16", 
            "enable_preprocessing": True
        }
        
        # When using linear16 locally to file, we may need a wave file.
        # But for websocket test this is skipped. This is left here for completeness.
        # We will stream the bytes directly into the file. Note: This creates raw PCM file, not valid WAV.
        output_filename = f"{AUDIO_OUTPUT_DIR}/{uuid.uuid4()}.pcm"
        
        with requests.post(url, headers=headers, json=payload, stream=True) as response:
            response.raise_for_status()
            with open(output_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        logger.info(f"TTS generated (Sarvam Stream) | language: {language} | text: {text[:60]}...")
        return {
            "audio_path": output_filename,
            "voice":      "anushka",
            "language":   target_lang,
            "success":    True
        }

    except Exception as e:
        logger.error(f"TTS failed: {e}")
        return {
            "audio_path": None,
            "voice":      None,
            "language":   language,
            "success":    False,
            "error":      str(e)
        }

