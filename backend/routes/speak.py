import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from loguru import logger
from backend.services.tts import text_to_speech

router = APIRouter()

class SpeakRequest(BaseModel):
    text:     str
    language: str = "en"

@router.post("/")
async def speak(request: SpeakRequest):
    """
    Accepts text + language, returns audio file (mp3)
    """

    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty"
        )

    if len(request.text) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Text too long — keep under 1000 characters for voice responses"
        )

    result = text_to_speech(request.text, request.language)

    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "TTS failed")
        )

    return FileResponse(
        path=result["audio_path"],
        media_type="audio/mpeg",
        filename="response.mp3",
        background=None
    )