import requests
from loguru import logger
from backend.config import settings

LANGUAGE_MAP = {
    "hindi":    "hi",
    "english":  "en",
    "hinglish": "hi",  
    "tamil":    "ta",
    "telugu":   "te",
    "bengali":  "bn",
}

def transcribe_audio(audio_file_path: str, language: str = None) -> dict:
    try:
        url = "https://api.sarvam.ai/speech-to-text"
        headers = {
            "api-subscription-key": settings.sarvam_api_key
        }
        with open(audio_file_path, "rb") as audio_file:
            files = {
                "file": ("audio.wav", audio_file, "audio/wav")
            }
            data = {
                "model": "saaras:v3"
            }
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            
        transcript_data = response.json()
        transcript = transcript_data.get("transcript", "")
        detected_language = language or "en"
        
        logger.info(f"Transcribed audio (Sarvam) | text: {transcript[:60]}...")
        return {
            "text":     transcript,
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

