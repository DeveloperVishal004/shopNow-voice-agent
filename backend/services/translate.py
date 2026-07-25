import httpx
from loguru import logger
from backend.config import settings

# Languages gpt-4o-mini generates fluently enough to skip a translation step.
# Anything else that the TTS voice supports (e.g. Odia, Kannada, Malayalam,
# Punjabi) is generated in English by the LLM and then translated to the target
# with Sarvam's Mayura model before TTS — the LLM's *direct* output in these
# low-resource languages is noticeably weaker, whereas a purpose-built Indic
# translation model is reliable. Keys are 2-letter language prefixes.
LLM_DIRECT_LANGUAGES = {"en", "hi", "ta", "te", "bn", "mr", "gu"}

SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"


def needs_translation(target_lang_code: str) -> bool:
    """True when the target language should be produced via translate-after-English
    rather than direct LLM generation."""
    prefix = (target_lang_code or "en").lower()[:2]
    return prefix not in LLM_DIRECT_LANGUAGES


async def translate_text(
    text: str,
    target_lang_code: str,
    source_lang_code: str = "en-IN",
) -> str:
    """
    Translate `text` into `target_lang_code` using Sarvam's Mayura model.

    Fail-safe: returns the original text unchanged on any error, so a
    translation outage degrades to the English reply rather than dropping the
    turn. Responses are short (voice replies), so we stay well under the API's
    per-request character limit.
    """
    if not text or not text.strip():
        return text

    # Nothing to do if the target is already the source language family.
    if not needs_translation(target_lang_code):
        return text

    try:
        payload = {
            "input": text,
            "source_language_code": source_lang_code,
            "target_language_code": target_lang_code,
            "model": "mayura:v1",
            "mode": "formal",
        }
        headers = {
            "api-subscription-key": settings.sarvam_api_key,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                SARVAM_TRANSLATE_URL, json=payload, headers=headers, timeout=15.0
            )
            resp.raise_for_status()
            data = resp.json()

        translated = (data.get("translated_text") or "").strip()
        if not translated:
            logger.warning(f"Empty translation for {target_lang_code} — using source text")
            return text

        logger.info(
            f"Translated en->{target_lang_code} | '{text[:40]}...' -> '{translated[:40]}...'"
        )
        return translated

    except Exception as e:
        logger.error(f"Translation failed ({target_lang_code}): {e} — returning source text")
        return text
