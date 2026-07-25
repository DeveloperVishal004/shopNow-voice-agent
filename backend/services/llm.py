from openai import OpenAI
from loguru import logger
from backend.config import settings
from backend.handlers import INTENT_HANDLERS
from backend.services.rag import retrieve_context
from backend.services.intent import classify_intent
from backend.memory.session import (
    get_session,
    add_turn,
    update_session,
    get_conversation_history
)

client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """
You are Priya, ShopNow's friendly and empathetic customer support agent.
ShopNow is a D2C e-commerce brand delivering across India.

Your personality:
- Warm, patient, and professional
- You MUST reply directly in the matching language of the user based on the provided language code: {lang_code} (e.g. Odia, Tamil, Telugu, Hindi, Bengali, etc.). Reply purely in that native language.
- Speak in the same language the customer uses
- Keep responses short and clear — this is a voice call, not a chat

Your capabilities:
- Check order status
- Initiate returns and refunds
- Resolve payment issues
- Handle delivery complaints
- Answer product queries

Rules:
- Never make up order details — only use the data provided to you
- If you don't have enough information, ask one clear question
- Always address the customer by name if you know it
- Be empathetic when the customer is frustrated
- Never say you are an AI unless directly asked

Emotional guidance for THIS reply (based on the customer's current sentiment):
{tone_directive}

Context provided to you:
{db_context}
{rag_context}
"""

# Intents whose answers can draw on the policy knowledge base (return windows,
# refund/shipping/cancellation rules, product info). RAG retrieval is skipped
# for the rest — order_status just needs the order row and general_or_unrelated
# needs no policy — so we don't pay for a vector search or bloat the prompt on
# turns that can't use it. Note: 4 of the 5 KB docs are policy (returns,
# payments, shipping, cancellation), so RAG is NOT product-only.
RAG_INTENTS = {"product_query", "return_refund", "payment_issue", "delivery_complaint"}

# tone instructions injected based on the sentiment of the current utterance
TONE_DIRECTIVES = {
    "angry":    "The customer is ANGRY. Before anything else, sincerely apologise and acknowledge their frustration. Stay calm, extra warm, and lead with a concrete reassurance that you will fix this.",
    "negative": "The customer sounds unhappy or dissatisfied. Open with empathy, acknowledge the inconvenience, and reassure them you are here to help.",
    "neutral":  "Maintain a warm, professional, and helpful tone.",
    "positive": "The customer is in a good mood. Keep the tone friendly, upbeat, and appreciative.",
}

async def generate_response(
    call_id:     str,
    user_text:   str,
    intent:      str,
    entities:    dict,
    lang_code:   str = "en-IN",
    rag_context: str = "",
    sentiment:   str = "neutral"
) -> str:
    """
    Core function — takes user input, fetches DB context,
    builds prompt, calls GPT-4o-mini, returns response text
    """
    try:
        session = get_session(call_id)
        if not session:
            return "I am sorry, something went wrong. Please call again."

        # fetch DB context from the right handler
        db_context = ""
        handler = INTENT_HANDLERS.get(intent)
        if handler:
            db_context = await handler(entities, session)
            logger.info(f"Handler executed: {intent}")

        # fetch RAG context — only for intents that can actually use policy
        # knowledge, so order_status / general don't pay for an unused lookup.
        if intent in RAG_INTENTS:
            rag_context = retrieve_context(user_text)
            logger.info(f"RAG context retrieved for: {user_text[:60]}")
        else:
            rag_context = ""
            logger.info(f"RAG skipped for intent '{intent}' (no policy needed)")
        # get full conversation history for multi-turn context
        history = get_conversation_history(call_id)

        # pick tone guidance based on the customer's current sentiment
        tone_directive = TONE_DIRECTIVES.get(sentiment, TONE_DIRECTIVES["neutral"])

        # build system prompt with context injected
        system = SYSTEM_PROMPT.format(
            db_context     = db_context  or "No order data available.",
            rag_context    = rag_context or "No policy context available.",
            lang_code      = lang_code,
            tone_directive = tone_directive
        )

        # build messages list
        messages = [
            {"role": "system", "content": system},
            *history,
            {"role": "user", "content": user_text}
        ]

        # call GPT-4o-mini
        response = client.chat.completions.create(
            model      = settings.llm_model,
            messages   = messages,
            max_tokens = settings.max_tokens,
            temperature= 0.7
        )

        response_text = response.choices[0].message.content

        # update session with customer name if found
        if session.get("order_context") and not session.get("customer_name"):
            update_session(
                call_id,
                customer_name=session["order_context"].get("customer_name")
            )

        logger.info(f"Response generated | call: {call_id} | intent: {intent}")
        return response_text

    except Exception as e:
        logger.error(f"LLM response generation failed: {e}")
        return "I am sorry, I am having trouble right now. Could you please repeat that?"