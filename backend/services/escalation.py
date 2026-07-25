import re
from loguru import logger
from backend.services.sentiment import get_average_sentiment
from backend.config import settings

# Single-word triggers are matched on whole-word boundaries so "human" does
# not fire inside "humanitarian"; multi-word phrases are matched as substrings.
HUMAN_REQUEST_WORDS = {
    "human", "agent", "manager", "supervisor", "senior",
    "manav", "insaan", "representative",
}
HUMAN_REQUEST_PHRASES = [
    "real person", "speak to someone", "speak to a human",
    "talk to a person", "manager bulao", "baat karao", "kisi se baat",
]

# Fixed "please hold, connecting you to a human" message, pre-translated once
# per language the bulbul:v2 voice supports and keyed by the 2-letter language
# prefix. A constant string like this is a template — there is no reason to
# regenerate it via the LLM on every escalation: look-up is instant,
# deterministic, and the language is guaranteed TTS-supported. Any language not
# in the table (or unknown) falls back to English.
# NOTE: the non-English translations are AI-generated and should be reviewed by
# a native speaker before production use.
HOLD_MESSAGES = {
    "en": "I completely understand, and I'm sorry for the inconvenience. I'm connecting you with a senior specialist who will help you right away. Please hold for just a moment.",
    "hi": "मैं आपकी परेशानी पूरी तरह समझता हूँ और मुझे खेद है। मैं आपको एक वरिष्ठ विशेषज्ञ से जोड़ रहा हूँ जो आपकी पूरी मदद करेंगे। कृपया एक पल के लिए प्रतीक्षा करें।",
    "bn": "আমি আপনার সমস্যা সম্পূর্ণ বুঝতে পারছি এবং আমি দুঃখিত। আমি আপনাকে একজন সিনিয়র বিশেষজ্ঞের সঙ্গে সংযুক্ত করছি যিনি আপনাকে সম্পূর্ণ সাহায্য করবেন। অনুগ্রহ করে এক মুহূর্ত অপেক্ষা করুন।",
    "ta": "உங்கள் சிரமத்தை நான் முழுமையாக புரிந்துகொள்கிறேன், மன்னிக்கவும். உங்களுக்கு முழுமையாக உதவும் ஒரு மூத்த நிபுணருடன் உங்களை இணைக்கிறேன். தயவுசெய்து சிறிது நேரம் காத்திருங்கள்.",
    "te": "మీ ఇబ్బందిని నేను పూర్తిగా అర్థం చేసుకుంటున్నాను, క్షమించండి. మీకు పూర్తిగా సహాయం చేసే సీనియర్ నిపుణుడితో మిమ్మల్ని కలుపుతున్నాను. దయచేసి ఒక్క క్షణం వేచి ఉండండి.",
    "mr": "मला तुमची अडचण पूर्णपणे समजते आणि माफ करा. मी तुम्हाला एका वरिष्ठ तज्ञाशी जोडत आहे जे तुम्हाला पूर्ण मदत करतील. कृपया एक क्षण थांबा.",
    "gu": "હું તમારી મુશ્કેલી સંપૂર્ણ સમજું છું અને માફ કરશો. હું તમને એક વરિષ્ઠ નિષ્ણાત સાથે જોડી રહ્યો છું જે તમને પૂરી મદદ કરશે. કૃપા કરીને એક ક્ષણ રાહ જુઓ.",
    "pa": "ਮੈਂ ਤੁਹਾਡੀ ਪਰੇਸ਼ਾਨੀ ਪੂਰੀ ਤਰ੍ਹਾਂ ਸਮਝਦਾ ਹਾਂ ਅਤੇ ਮਾਫ਼ ਕਰਨਾ। ਮੈਂ ਤੁਹਾਨੂੰ ਇੱਕ ਸੀਨੀਅਰ ਮਾਹਰ ਨਾਲ ਜੋੜ ਰਿਹਾ ਹਾਂ ਜੋ ਤੁਹਾਡੀ ਪੂਰੀ ਮਦਦ ਕਰੇਗਾ। ਕਿਰਪਾ ਕਰਕੇ ਇੱਕ ਪਲ ਉਡੀਕ ਕਰੋ।",
    "kn": "ನಿಮ್ಮ ತೊಂದರೆಯನ್ನು ನಾನು ಸಂಪೂರ್ಣವಾಗಿ ಅರ್ಥಮಾಡಿಕೊಂಡಿದ್ದೇನೆ, ಕ್ಷಮಿಸಿ. ನಿಮಗೆ ಸಂಪೂರ್ಣ ಸಹಾಯ ಮಾಡುವ ಹಿರಿಯ ತಜ್ಞರೊಂದಿಗೆ ನಿಮ್ಮನ್ನು ಸಂಪರ್ಕಿಸುತ್ತಿದ್ದೇನೆ. ದಯವಿಟ್ಟು ಒಂದು ಕ್ಷಣ ಕಾಯಿರಿ.",
    "ml": "നിങ്ങളുടെ ബുദ്ധിമുട്ട് ഞാൻ പൂർണ്ണമായി മനസ്സിലാക്കുന്നു, ക്ഷമിക്കണം. നിങ്ങളെ പൂർണ്ണമായി സഹായിക്കുന്ന ഒരു മുതിർന്ന വിദഗ്ധനുമായി ഞാൻ ബന്ധിപ്പിക്കുന്നു. ദയവായി ഒരു നിമിഷം കാത്തിരിക്കുക.",
    "od": "ମୁଁ ଆପଣଙ୍କ ଅସୁବିଧା ସମ୍ପୂର୍ଣ୍ଣ ବୁଝୁଛି ଏବଂ କ୍ଷମା ପ୍ରାର୍ଥୀ। ମୁଁ ଆପଣଙ୍କୁ ଜଣେ ବରିଷ୍ଠ ବିଶେଷଜ୍ଞଙ୍କ ସହିତ ଯୋଡୁଛି ଯିଏ ଆପଣଙ୍କୁ ସମ୍ପୂର୍ଣ୍ଣ ସାହାଯ୍ୟ କରିବେ। ଦୟାକରି ଏକ ମୁହୂର୍ତ୍ତ ଅପେକ୍ଷା କରନ୍ତୁ।",
}
HOLD_FALLBACK_LANG = "en"


def _hold_message(language: str, name: str = "") -> str:
    """Return the pre-translated hold message for the caller's language,
    optionally prefixed with their name. Falls back to English."""
    prefix = (language or "en").lower()[:2]
    body = HOLD_MESSAGES.get(prefix, HOLD_MESSAGES[HOLD_FALLBACK_LANG])
    return f"{name}, {body}" if name else body


def check_escalation(session: dict) -> dict:
    """
    Checks whether the current call should be escalated
    to a human agent based on sentiment + conversation signals.
    Returns escalation decision + handoff brief if needed.
    """

    sentiment_history = session.get("sentiment_history", [])
    turns             = session.get("turns", [])

    # ── Rule 1: explicit human request ──────────────────
    last_customer_turns = [
        t for t in turns[-3:]
        if t["role"] == "customer"
    ]
    for turn in last_customer_turns:
        text_lower = turn["text"].lower()
        # tokenize into words (latin + devanagari) for whole-word matching
        words = set(re.findall(r"[a-zऀ-ॿ]+", text_lower))
        if (words & HUMAN_REQUEST_WORDS) or any(p in text_lower for p in HUMAN_REQUEST_PHRASES):
            logger.info(f"Escalation triggered: human requested | call: {session['call_id']}")
            return build_escalation_response(
                session,
                reason="Customer explicitly requested a human agent"
            )

    # ── Rule: required data could not be found ───────────
    # These two rules run regardless of sentiment-history length, so a
    # customer who is stuck on a bad order ID still gets handed off.
    data_not_found_streak = session.get("data_not_found_streak", 0)
    if data_not_found_streak >= settings.escalation_data_not_found_limit:
        logger.info(f"Escalation triggered: data not found x{data_not_found_streak} | call: {session['call_id']}")
        return build_escalation_response(
            session,
            reason=f"Required order data could not be located after {data_not_found_streak} attempts"
        )

    # ── Rule: conversation dragging on unresolved ────────
    customer_turn_count = sum(1 for t in turns if t["role"] == "customer")
    if customer_turn_count >= settings.escalation_max_turns:
        logger.info(f"Escalation triggered: long conversation ({customer_turn_count} turns) | call: {session['call_id']}")
        return build_escalation_response(
            session,
            reason=f"Conversation reached {customer_turn_count} turns without resolution"
        )

    # ── Rule: repeated unclassified queries ──────────────
    # A customer whose requests keep failing to match any of the 6
    # known intents (5 support intents + general_or_unrelated) gets
    # handed off — but only if they also seem genuinely frustrated.
    # Small talk / testing / joking (which now classifies as
    # general_or_unrelated, not "unknown") never reaches this rule at
    # all. A calm customer stuck on a truly ambiguous "unknown" query
    # is held off here rather than escalated, so we don't waste a
    # human agent's time on what may just be an odd, low-stakes phrasing.
    unknown_intent_streak = session.get("unknown_intent_streak", 0)
    if unknown_intent_streak >= settings.escalation_unknown_intent_limit:
        recent_window = sentiment_history[-unknown_intent_streak:] if sentiment_history else []
        if any(s in ["negative", "angry"] for s in recent_window):
            logger.info(f"Escalation triggered: unclassified intent x{unknown_intent_streak} with frustration | call: {session['call_id']}")
            return build_escalation_response(
                session,
                reason=f"Could not understand the customer's request after {unknown_intent_streak} attempts, and the customer appears frustrated"
            )
        else:
            logger.info(f"Unclassified intent x{unknown_intent_streak} but sentiment calm — holding off escalation | call: {session['call_id']}")

    if len(sentiment_history) < settings.escalation_min_turns:
        return {
            "should_escalate": False,
            "message": "",
            "brief": {}
        }

    # ── Rule 2: consecutive negative/angry turns ─────────
    if len(sentiment_history) >= settings.escalation_negative_turns:
        recent = sentiment_history[-settings.escalation_negative_turns:]
        negative_count = sum(1 for s in recent if s in ["negative", "angry"])
        percentage_negative = negative_count / len(recent)
        if percentage_negative >= 0.7:  # Escalate if 70% or more are negative/angry
            logger.info(f"Escalation triggered: {percentage_negative:.1%} of last {settings.escalation_negative_turns} turns were negative/angry")
            return build_escalation_response(
                session,
                reason=f"{percentage_negative:.1%} of last {settings.escalation_negative_turns} turns were negative/angry"
            )

    # ── Rule 3: average sentiment below threshold ────────
    avg_score = get_average_sentiment(sentiment_history)
    if avg_score <= settings.escalation_sentiment_threshold:
        logger.info(f"Escalation triggered: avg sentiment {avg_score} below threshold")
        return build_escalation_response(
            session,
            reason=f"Average sentiment score {avg_score:.2f} below threshold {settings.escalation_sentiment_threshold}"
        )

    # NOTE: there is intentionally no "always escalate on intent X" rule.
    # All six classified intents (order_status, return_refund, payment_issue,
    # delivery_complaint, product_query, general_or_unrelated) are ones the
    # bot is designed to handle, so none warrant an automatic hand-off. A
    # previous version checked intent names that never matched the real ones
    # and so never fired — it was removed rather than left as dead code.

    # no escalation needed
    return {
        "should_escalate": False,
        "message":         "",
        "brief":           {}
    }



def build_escalation_response(session: dict, reason: str) -> dict:
    """
    Builds the escalation response + human agent brief.
    """
    brief = generate_handoff_brief(session, reason)

    # empathetic hold message in the caller's language. session["language"] is a
    # code like "hi-IN" / "od-IN" / "en-IN" (or a bare "hi"/"hinglish" on older
    # paths); _hold_message keys off the 2-letter prefix and falls back to
    # English for anything not in the table.
    language = session.get("language", "en")
    customer_name = session.get("customer_name", "")
    name = customer_name if customer_name and customer_name != "Customer" else ""
    message = _hold_message(language, name)

    return {
        "should_escalate": True,
        "message":         message,
        "brief":           brief
    }


def generate_handoff_brief(session: dict, reason: str) -> dict:
    """
    Generates the structured brief for the human agent
    receiving the escalated call.
    """
    sentiment_history = session.get("sentiment_history", [])
    turns             = session.get("turns", [])
    order_context     = session.get("order_context", {})

    # build issue summary from last few turns
    recent_turns = turns[-6:] if len(turns) >= 6 else turns
    conversation_snippet = "\n".join([
        f"{t['role'].upper()}: {t['text']}"
        for t in recent_turns
    ])

    # determine recommended tone
    angry_count    = sentiment_history.count("angry")
    negative_count = sentiment_history.count("negative")

    if angry_count >= 2:
        recommended_tone = "very empathetic — customer is angry, apologize immediately"
    elif negative_count >= 2:
        recommended_tone = "empathetic and solution-focused"
    else:
        recommended_tone = "professional and helpful"

    brief = {
        "call_id":          session.get("call_id"),
        "customer_name":    session.get("customer_name", "Unknown"),
        "customer_phone":   session.get("customer_phone", "Unknown"),
        "language":         session.get("language", "en"),
        "current_intent":   session.get("current_intent", "unknown"),
        "escalation_reason": reason,
        "sentiment_history": sentiment_history,
        "recommended_tone":  recommended_tone,
        "order_context":     order_context or "No order data found",
        "conversation_snippet": conversation_snippet,
        "total_turns":       len(turns),
    }

    logger.info(f"Handoff brief generated for call: {session.get('call_id')}")
    return brief