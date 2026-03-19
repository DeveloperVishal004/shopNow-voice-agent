from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    # OpenAI
    openai_api_key: str

    # Sarvam AI
    sarvam_api_key: str

    # Database
    database_url: str = "./shopnow.db"

    # RAG
    faiss_index_path: str = "./rag_store/index/faiss.index"

    # LLM
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    max_tokens: int = 200

    # TTS
    tts_model: str = "tts-1"
    tts_voice: str = "nova"

    # Escalation thresholds
    escalation_negative_turns: int = 4
    escalation_sentiment_threshold: float = -0.7
    escalation_min_turns: int = 3


    class Config:
        env_file = ".env"

settings = Settings()
