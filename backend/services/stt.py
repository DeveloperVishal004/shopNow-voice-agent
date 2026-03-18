from openai import OpenAI
from loguru import logger
from backend.config import settings

client = OpenAI(api_key=settings.openai_api_key)

LANGUAGE_MAP = {
    "hindi":    "hi",
    "english":  "en",
    "hinglish": "hi",  # whisper treats hinglish as hindi
    "tamil":    "ta",
    "telugu":   "te",
    "bengali":  "bn",
}

def transcribe_audio(audio_file_path: str, language: str = None) -> dict:
    """
    Takes an audio file path, sends to Whisper, returns
    transcribed text + detected language
    """
    try:
        with open(audio_file_path, "rb") as audio_file:

            params = {
                "model": "whisper-1",
                "file":  audio_file,
                "response_format": "verbose_json",  # gives us language detection too
            }

            # if language is known, pass it — improves accuracy
            if language:
                params["language"] = LANGUAGE_MAP.get(language.lower(), "hi")

            transcript = client.audio.transcriptions.create(**params)

        detected_language = transcript.language or "en"

        logger.info(f"Transcribed audio | language: {detected_language} | text: {transcript.text[:60]}...")

        return {
            "text":     transcript.text,
            "language": detected_language,
            "success":  True
        }

    except FileNotFoundError:
        logger.error(f"Audio file not found: {audio_file_path}")
        return {
            "text":    "",
            "language": "en",
            "success": False,
            "error":   "Audio file not found"
        }

    except Exception as e:
        logger.error(f"STT failed: {e}")
        return {
            "text":    "",
            "language": "en",
            "success": False,
            "error":   str(e)
        }