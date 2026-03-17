from openai import OpenAI
from loguru import logger
from backend.config import settings

client = OpenAI(api_key=settings.openai_api_key)

SCORE_MAP = {
    "positive": 1.0,
    "neutral":  0.0,
    "negative": -0.5,
    "angry":    -1.0
}

def score_sentiment(text: str) -> dict:
    """
    Uses GPT-4o-mini to detect sentiment.
    Works across English, Hindi and Hinglish naturally.
    Returns label + numeric score.
    """
    try:
        response = client.chat.completions.create(
            model      = settings.llm_model,
            max_tokens = 10,
            temperature= 0,
            messages   = [
                {
                    "role": "system",
                    "content": """You are a sentiment classifier for customer support calls.
Classify the sentiment of the customer's message into exactly one of these labels:
- positive
- neutral  
- negative
- angry

Rules:
- angry = very frustrated, aggressive, using strong words
- negative = unhappy, dissatisfied but calm
- neutral = factual, no strong emotion
- positive = happy, satisfied, appreciative
- Works for English, Hindi, and Hinglish text
- Reply with ONLY the label, nothing else"""
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        label = response.choices[0].message.content.strip().lower()

        # sanitize — make sure it's a valid label
        if label not in SCORE_MAP:
            label = "neutral"

        score = SCORE_MAP[label]
        logger.info(f"Sentiment | label: {label} | score: {score} | text: {text[:60]}")

        return {
            "label":   label,
            "score":   score,
            "success": True
        }

    except Exception as e:
        logger.error(f"Sentiment scoring failed: {e}")
        return {
            "label":   "neutral",
            "score":   0.0,
            "success": False,
            "error":   str(e)
        }


def get_average_sentiment(sentiment_history: list) -> float:
    """
    Takes list of sentiment labels from session history,
    returns average numeric score.
    Used by escalation logic.
    """
    if not sentiment_history:
        return 0.0

    scores = [SCORE_MAP.get(label, 0.0) for label in sentiment_history]
    return sum(scores) / len(scores)


def load_sentiment_model():
    """
    Kept for compatibility with main.py startup.
    Nothing to load since we use the LLM directly.
    """
    logger.info("Sentiment analysis using GPT-4o-mini — no model loading needed")