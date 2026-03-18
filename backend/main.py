from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from backend.db.database import init_db
from backend.routes import call, transcribe, speak, report
from backend.config import settings
from backend.services.rag import load_index
from backend.routes import call, transcribe, speak, report, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ShopNow Voice Agent...")
    await init_db()
    logger.info("Database initialized successfully")
    load_index()
    yield
    logger.info("Shutting down ShopNow Voice Agent...")

app = FastAPI(
    title="ShopNow Voice Agent",
    description="AI-powered customer support voice agent",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(call.router,       prefix="/call",       tags=["Call"])
app.include_router(transcribe.router, prefix="/transcribe", tags=["STT"])
app.include_router(speak.router,      prefix="/speak",      tags=["TTS"])
app.include_router(report.router,     prefix="/report",     tags=["Report"])
app.include_router(websocket.router, prefix="", tags=["WebSocket"])

@app.get("/health")
async def health_check():
    return {
        "status":  "ok",
        "service": "ShopNow Voice Agent",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {"message": "ShopNow Voice Agent is running"}