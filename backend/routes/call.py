import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from backend.memory.session import (
    create_session,
    get_session,
    add_turn,
    update_session,
    end_session,
    delete_session
)
from backend.services.intent import classify_intent
from backend.services.llm import generate_response
from backend.services.sentiment import score_sentiment
from backend.services.escalation import check_escalation
from backend.memory.session import get_conversation_history

router = APIRouter()

# ── request/response models ──────────────────────────────

class StartCallRequest(BaseModel):
    customer_phone: str = None

class TurnRequest(BaseModel):
    call_id: str
    text:    str
    language: str = "en"

class EndCallRequest(BaseModel):
    call_id: str
    outcome: str = "resolved"

# ── endpoints ────────────────────────────────────────────

@router.post("/start")
async def start_call(request: StartCallRequest):
    """
    Called when a new call begins.
    Creates session, returns call_id.
    """
    session = create_session(request.customer_phone)

    return {
        "call_id": session["call_id"],
        "message": "Call started. Session created.",
    }


@router.post("/turn")
async def handle_turn(request: TurnRequest):
    """
    Called on every customer utterance.
    Returns agent response text.
    """
    session = get_session(request.call_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 1 — update language in session
    update_session(request.call_id, language=request.language)

    # 2 — score sentiment on this utterance
    sentiment = score_sentiment(request.text)

    # 3 — classify intent
    history = get_conversation_history(request.call_id)
    intent_result = classify_intent(request.text, history)
    intent   = intent_result["intent"]
    entities = intent_result["entities"]

    # 4 — add customer turn to session
    add_turn(
        call_id   = request.call_id,
        role      = "customer",
        text      = request.text,
        intent    = intent,
        sentiment = sentiment["label"]
    )

    # 5 — update current intent in session
    update_session(request.call_id, current_intent=intent)

    # 6 — check escalation BEFORE generating response
    session = get_session(request.call_id)
    escalation = check_escalation(session)
    if escalation["should_escalate"]:
        add_turn(
            call_id = request.call_id,
            role    = "agent",
            text    = escalation["message"]
        )
        end_session(request.call_id, outcome="escalated")
        return {
            "response":        escalation["message"],
            "intent":          intent,
            "sentiment":       sentiment["label"],
            "escalated":       True,
            "escalation_brief": escalation["brief"]
        }

    # 7 — generate LLM response
    response_text = await generate_response(
        call_id  = request.call_id,
        user_text= request.text,
        intent   = intent,
        entities = entities
    )

    # 8 — add agent turn to session
    add_turn(
        call_id = request.call_id,
        role    = "agent",
        text    = response_text
    )

    return {
        "response":  response_text,
        "intent":    intent,
        "sentiment": sentiment["label"],
        "escalated": False
    }


@router.post("/end")
async def end_call(request: EndCallRequest):
    """
    Called when call finishes.
    Logs to DB and cleans up session.
    """
    import json
    from backend.services.sentiment import get_average_sentiment

    session = end_session(request.call_id, request.outcome)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # calculate average sentiment
    avg_sentiment = get_average_sentiment(
        session.get("sentiment_history", [])
    )

    # build transcript string
    transcript = json.dumps(session.get("turns", []))

    # log to DB via report endpoint internally
    async with __import__('backend.db.database', fromlist=['AsyncSessionLocal']).AsyncSessionLocal() as db:
        from backend.db.models import CallLog
        call_log = CallLog(
            id            = request.call_id,
            customer_id   = session.get("customer_id"),
            language      = session.get("language", "en"),
            intent        = session.get("current_intent", "unknown"),
            outcome       = request.outcome,
            duration_secs = 0,
            sentiment_avg = avg_sentiment,
            transcript    = transcript
        )
        db.add(call_log)
        await db.commit()
        logger.info(f"Call logged to DB: {request.call_id}")

    delete_session(request.call_id)

    return {
        "call_id":      request.call_id,
        "outcome":      request.outcome,
        "avg_sentiment": avg_sentiment,
        "message":      "Call ended and logged successfully"
    }


@router.get("/session/{call_id}")
async def get_call_session(call_id: str):
    """
    Debug endpoint — view full session state.
    Useful during testing.
    """
    session = get_session(call_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session