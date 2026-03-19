import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from loguru import logger
from openai import OpenAI
from backend.services.stt import transcribe_audio
from backend.config import settings

router = APIRouter()
client = OpenAI(api_key=settings.openai_api_key)

TEMP_DIR = "./temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)


def translate_to_english(text: str, source_language: str) -> str:
    """
    Translates text to English using OpenAI API.
    If text is already in English, returns as-is.
    """
    if source_language == "en" or source_language is None:
        return text
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a translator. Translate the user's text to English. Return only the translated text, nothing else."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.3
        )
        
        translated_text = response.choices[0].message.content.strip()
        logger.info(f"Translated from {source_language} to English | original: {text[:50]}... | translated: {translated_text[:50]}...")
        return translated_text
        
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text  # fallback to original text if translation fails


@router.post("/")
async def transcribe(
    audio: UploadFile = File(...),
    language: str = None
):
    """
    Accepts an audio file, returns transcribed text + detected language.
    Supports mp3, wav, m4a, ogg, webm
    """

    # validate file type
    allowed_types = ["audio/mpeg", "audio/wav", "audio/mp4",
                     "audio/ogg", "audio/webm", "audio/x-m4a"]
    if audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {audio.content_type}. Use mp3, wav, m4a, ogg or webm"
        )

    # save uploaded file temporarily
    temp_filename = f"{TEMP_DIR}/{uuid.uuid4()}_{audio.filename}"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        logger.info(f"Audio file saved temporarily: {temp_filename}")

        # call STT service
        result = transcribe_audio(temp_filename, language)

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Transcription failed")
            )
        
        # translate text to English if not already in English
        detected_language = result["language"]
        original_text = result["text"]
        translated_text = translate_to_english(original_text, detected_language)
        
        return {
            "text":        translated_text,
            "original_text": original_text,
            "language":    detected_language,
            "filename":    audio.filename
        }

    finally:
        # always delete temp file after processing
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            logger.info(f"Temp file cleaned up: {temp_filename}")