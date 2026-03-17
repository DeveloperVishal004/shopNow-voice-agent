import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from loguru import logger
from backend.services.stt import transcribe_audio

router = APIRouter()

TEMP_DIR = "./temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

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

        return {
            "text":     result["text"],
            "language": result["language"],
            "filename": audio.filename
        }

    finally:
        # always delete temp file after processing
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            logger.info(f"Temp file cleaned up: {temp_filename}")