from loguru import logger
from backend.services.sentiment import score_sentiment
from backend.services.voice_sentiment import score_voice_sentiment


def get_final_sentiment(
    transcript:  str,
    audio_bytes: bytes,
    sample_rate: int = 24000
) -> dict:
    """
    Step 1 — run text sentiment
    Step 2 — if text is not neutral trust it directly
    Step 3 — if text is neutral run voice SER
    Step 4 — trust voice result directly no fusion
    """

    # step 1 — text sentiment always runs first
    text_sentiment = score_sentiment(transcript)
    text_label     = text_sentiment.get("label", "neutral")

    logger.info(f"Text sentiment: {text_label}")

    # step 2 — text has clear signal trust it directly
    if text_label != "neutral":
        logger.info(
            f"Strong text signal ({text_label}) — "
            f"skipping voice SER"
        )
        return {
            "label":       text_label,
            "score":       text_sentiment.get("score", 0.0),
            "text_label":  text_label,
            "voice_label": "skipped",
            "source":      "text",
            "reason":      "text signal was strong"
        }

    # step 3 — text is neutral so check voice
    logger.info("Text is neutral — invoking voice SER")

    if not audio_bytes:
        logger.warning("No audio bytes — staying neutral")
        return {
            "label":       "neutral",
            "score":       0.0,
            "text_label":  "neutral",
            "voice_label": "unavailable",
            "source":      "text",
            "reason":      "no audio available"
        }

    voice_sentiment = score_voice_sentiment(audio_bytes, sample_rate)

    # step 4 — trust voice result directly
    if voice_sentiment.get("success"):
        voice_label = voice_sentiment.get("label", "neutral")
        logger.info(
            f"Voice result: {voice_label} | "
            f"source: voice | "
            f"reason: voice overrode neutral text"
        )
        return {
            "label":       voice_label,
            "score":       voice_sentiment.get("score", 0.0),
            "text_label":  "neutral",
            "voice_label": voice_label,
            "source":      "voice",
            "reason":      "voice overrode neutral text"
                           if voice_label != "neutral"
                           else "both signals neutral"
        }

    # fallback — voice failed stay neutral
    logger.warning("Voice SER failed — staying neutral")
    return {
        "label":       "neutral",
        "score":       0.0,
        "text_label":  "neutral",
        "voice_label": "unavailable",
        "source":      "text",
        "reason":      "voice SER failed"
    }