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

Context provided to you:
{db_context}
{rag_context}
"""

async def generate_response(
    call_id:     str,
    user_text:   str,
    intent:      str,
    entities:    dict,
    lang_code:   str = "en-IN",
    rag_context: str = ""
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

        # fetch RAG context based on user query
        rag_context = retrieve_context(user_text)
        logger.info(f"RAG context retrieved for: {user_text[:60]}")
        # get full conversation history for multi-turn context
        history = get_conversation_history(call_id)

        # build system prompt with context injected
        system = SYSTEM_PROMPT.format(
            db_context  = db_context  or "No order data available.",
            rag_context = rag_context or "No policy context available.",
            lang_code   = lang_code
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