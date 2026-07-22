from loguru import logger
from backend.services.sentiment import get_average_sentiment
from backend.config import settings


def check_escalation(session: dict) -> dict:
    """
    Checks whether the current call should be escalated
    to a human agent based on sentiment + conversation signals.
    Returns escalation decision + handoff brief if needed.
    """

    sentiment_history = session.get("sentiment_history", [])
    turns             = session.get("turns", [])
    current_intent    = session.get("current_intent", "")
    customer_name     = session.get("customer_name", "Customer")

    # ── Rule 1: explicit human request ──────────────────
    last_customer_turns = [
        t for t in turns[-3:]
        if t["role"] == "customer"
    ]
    human_keywords = [
        "human", "agent", "manager", "supervisor",
        "manav", "insaan", "manager bulao", "senior",
        "real person", "speak to someone"
    ]
    for turn in last_customer_turns:
        text_lower = turn["text"].lower()
        if any(kw in text_lower for kw in human_keywords):
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

    # ── Rule 5: specific intents that require escalation ──
    escalation_intents = ["complaint", "refund_request", "escalation"]
    if current_intent and current_intent.lower() in escalation_intents:
        logger.info(f"Escalation triggered: intent '{current_intent}' requires human | call: {session['call_id']}")
        return build_escalation_response(
            session,
            reason=f"Intent '{current_intent}' flagged for escalation"
        )

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

    # empathetic message to customer
    language = session.get("language", "en")
    customer_name = session.get("customer_name", "")
    name = customer_name if customer_name and customer_name != "Customer" else ""
    greeting = f"Hello {name}, " if name else ""
    if language == "hi" or language == "hinglish":
        message = (
            f"{greeting}Main samajh sakta hoon aap pareshan hain. "
            "Main aapko apne senior agent se connect kar raha hoon "
            "jo aapki poori madad karenge. Kripya ek moment hold karein."
        )
    else:
        message = (
            f"{greeting}I completely understand your frustration and I sincerely apologize. "
            "Let me connect you with a senior support specialist right away "
            "who will be able to fully resolve this for you. "
            "Please hold for just a moment."
        )

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