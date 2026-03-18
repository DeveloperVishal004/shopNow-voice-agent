import os
import uuid
from openai import OpenAI
from loguru import logger
from backend.config import settings

client = OpenAI(api_key=settings.openai_api_key)

AUDIO_OUTPUT_DIR = "./temp_audio/responses"
os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)

# voice selection based on language
# nova and shimmer sound most natural for support agent
VOICE_MAP = {
    "en": "nova",
    "hi": "shimmer",
    "ta": "shimmer",
    "te": "shimmer",
    "bn": "shimmer",
}

def text_to_speech(text: str, language: str = "en") -> dict:
    """
    Takes text + language, returns path to generated audio file
    """
    try:
        voice = VOICE_MAP.get(language, "nova")

        response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text,
        speed=1.5
        )

        # save to temp file
        output_filename = f"{AUDIO_OUTPUT_DIR}/{uuid.uuid4()}.mp3"
        response.stream_to_file(output_filename)

        logger.info(f"TTS generated | language: {language} | voice: {voice} | text: {text[:60]}...")

        return {
            "audio_path": output_filename,
            "voice":      voice,
            "language":   language,
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