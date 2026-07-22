import uuid
from datetime import datetime
from loguru import logger

# in-memory store — keyed by call_id
# { call_id: { ...session data } }
sessions = {}

def create_session(customer_phone: str = None) -> dict:
    """
    Creates a new session when a call starts.
    Returns the full session object.
    """
    call_id = str(uuid.uuid4())

    session = {
        "call_id":           call_id,
        "customer_phone":    customer_phone,
        "customer_name":     None,
        "customer_id":       None,
        "started_at":        datetime.now().isoformat(),
        "language":          "en",        # updated after first utterance
        "current_intent":    None,
        "turns":             [],          # full conversation history
        "sentiment_history": [],          # sentiment score per customer turn
        "escalated":         False,
        "resolved":          False,
        "order_context":     None,        # DB result stored here after lookup
        "data_not_found_streak": 0,       # consecutive failed backend data lookups
    }

    sessions[call_id] = session
    logger.info(f"Session created: {call_id}")
    return session


def get_session(call_id: str) -> dict:
    """
    Retrieves an existing session by call_id.
    Returns None if not found.
    """
    session = sessions.get(call_id)
    if not session:
        logger.warning(f"Session not found: {call_id}")
    return session


def update_session(call_id: str, **kwargs) -> dict:
    """
    Updates any fields in the session.
    Usage: update_session(call_id, language="hi", current_intent="order_status")
    """
    session = get_session(call_id)
    if not session:
        return None

    for key, value in kwargs.items():
        if key in session:
            session[key] = value
        else:
            logger.warning(f"Unknown session field: {key}")

    sessions[call_id] = session
    return session


def add_turn(call_id: str, role: str, text: str, intent: str = None, sentiment: str = None):
    """
    Appends one conversation turn to the session.
    role = 'customer' or 'agent'
    """
    session = get_session(call_id)
    if not session:
        return

    turn = {
        "role":      role,
        "text":      text,
        "intent":    intent,
        "sentiment": sentiment,
        "timestamp": datetime.now().isoformat()
    }

    session["turns"].append(turn)

    # track sentiment history for customer turns only
    if role == "customer" and sentiment:
        session["sentiment_history"].append(sentiment)

    logger.info(f"Turn added | call: {call_id} | role: {role} | intent: {intent} | sentiment: {sentiment}")


def record_data_lookup(session: dict, found: bool):
    """
    Tracks consecutive failed backend data lookups.
    Resets to 0 on a successful lookup, increments on a miss.
    Feeds the "Data Not Found" escalation criterion so the agent
    hands off when it repeatedly cannot locate the customer's order.
    """
    if not session:
        return
    if found:
        session["data_not_found_streak"] = 0
    else:
        session["data_not_found_streak"] = session.get("data_not_found_streak", 0) + 1
        logger.info(f"Data lookup miss | streak: {session['data_not_found_streak']}")


def cache_order_context(session: dict, order):
    """
    Caches a resolved Order onto the session so ANY handler that looks
    one up — not just handle_order_status — makes it reusable by later
    turns via the `entities.get("order_id") or session["order_context"]["id"]`
    fallback pattern already used across returns/payment/delivery/product.

    Without this, only order_status wrote to order_context, so a call
    that started with e.g. "I want to return ORD-1001" (return_refund
    resolves the order but never cached it) would have an empty
    order_context for a later delivery/payment question in the same
    call, forcing the classifier to re-extract the order_id from
    scratch instead of reusing what was already found.
    """
    if not session or not order:
        return
    session["order_context"] = {
        "id":              order.id,
        "status":          order.status,
        "item_name":       order.item_name,
        "order_date":      order.order_date,
        "delivery_date":   order.delivery_date,
        "return_eligible": order.return_eligible,
    }
    if not session.get("customer_name"):
        session["customer_name"] = order.customer_name


def get_conversation_history(call_id: str) -> list:
    """
    Returns turns formatted for LangChain / OpenAI messages list.
    { role: user/assistant, content: text }
    """
    session = get_session(call_id)
    if not session:
        return []

    history = []
    for turn in session["turns"]:
        role = "user" if turn["role"] == "customer" else "assistant"
        history.append({
            "role":    role,
            "content": turn["text"]
        })

    return history


def end_session(call_id: str, outcome: str = "resolved") -> dict:
    """
    Marks session as ended.
    outcome = 'resolved' or 'escalated'
    Returns the final session for logging to DB.
    """
    session = get_session(call_id)
    if not session:
        return None

    session["ended_at"] = datetime.now().isoformat()
    session["resolved"] = outcome == "resolved"
    session["escalated"] = outcome == "escalated"

    logger.info(f"Session ended | call: {call_id} | outcome: {outcome}")
    return session


def delete_session(call_id: str):
    """
    Removes session from memory after it has been logged to DB.
    """
    if call_id in sessions:
        del sessions[call_id]
        logger.info(f"Session deleted from memory: {call_id}")