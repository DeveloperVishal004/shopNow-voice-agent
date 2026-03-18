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