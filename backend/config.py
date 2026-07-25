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
    # Whole-call average sentiment at/below which we escalate. On the score
    # scale (angry -1.0, negative -0.5, neutral 0.0, positive +1.0), -0.4 means
    # the call has been predominantly negative overall — a deliberate midpoint
    # between hair-trigger (-0.2 fires on mostly-neutral calls) and near-dead
    # (-0.7, which a fully-"negative" call averaging -0.5 would never reach).
    escalation_sentiment_threshold: float = -0.4
    escalation_min_turns: int = 3
    escalation_max_turns: int = 8               # escalate if a call runs this many customer turns unresolved
    escalation_data_not_found_limit: int = 2    # escalate after this many failed backend data lookups
    escalation_unknown_intent_limit: int = 3    # escalate after this many consecutive unclassified queries


    class Config:
        env_file = ".env"

settings = Settings()
