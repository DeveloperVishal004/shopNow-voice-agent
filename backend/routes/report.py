import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from loguru import logger

from backend.db.database import AsyncSessionLocal
from backend.db.models import CallLog, EscalationLog, DailyReport
from backend.memory.session import sessions

router = APIRouter()


# ── escalation brief endpoint ────────────────────────────

@router.get("/escalation/{call_id}")
async def get_escalation_brief(call_id: str):
    """
    Returns the escalation brief for a specific call.
    Human agent dashboard calls this when a call is escalated.
    """
    session = sessions.get(call_id)
    if not session:
        # try DB if session already ended
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(EscalationLog).where(EscalationLog.call_id == call_id)
            )
            log = result.scalar_one_or_none()
            if not log:
                raise HTTPException(
                    status_code=404,
                    detail=f"No escalation found for call {call_id}"
                )
            return {
                "call_id":          log.call_id,
                "customer_name":    log.customer_name,
                "issue_summary":    log.issue_summary,
                "sentiment_history": log.sentiment_history,
                "recommended_tone": log.recommended_tone,
                "resolved":         log.resolved,
                "created_at":       log.created_at
            }

    # return from live session
    return {
        "call_id":           call_id,
        "customer_name":     session.get("customer_name", "Unknown"),
        "customer_phone":    session.get("customer_phone", "Unknown"),
        "language":          session.get("language", "en"),
        "current_intent":    session.get("current_intent", "unknown"),
        "sentiment_history": session.get("sentiment_history", []),
        "order_context":     session.get("order_context", {}),
        "total_turns":       len(session.get("turns", [])),
    }


# ── call log endpoint ─────────────────────────────────────

class LogCallRequest(BaseModel):
    call_id:      str
    customer_id:  str = None
    language:     str = "en"
    intent:       str = "unknown"
    outcome:      str = "resolved"
    duration_secs: int = 0
    sentiment_avg: float = 0.0
    transcript:   str = ""

@router.post("/log")
async def log_call(request: LogCallRequest):
    """
    Logs a completed call to the database.
    Called automatically when call ends.
    """
    try:
        async with AsyncSessionLocal() as db:
            call_log = CallLog(
                id            = request.call_id,
                customer_id   = request.customer_id,
                language      = request.language,
                intent        = request.intent,
                outcome       = request.outcome,
                duration_secs = request.duration_secs,
                sentiment_avg = request.sentiment_avg,
                transcript    = request.transcript
            )
            db.add(call_log)
            await db.commit()
            logger.info(f"Call logged: {request.call_id} | outcome: {request.outcome}")
            return {"message": "Call logged successfully"}

    except Exception as e:
        logger.error(f"Failed to log call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── daily report endpoint ─────────────────────────────────

@router.get("/daily")
async def get_daily_report():
    """
    Returns aggregated stats for today's calls.
    Streamlit dashboard reads from this endpoint.
    """
    try:
        async with AsyncSessionLocal() as db:

            # total calls
            total = await db.execute(func.count(CallLog.id))
            total_calls = total.scalar() or 0

            # resolved vs escalated
            resolved = await db.execute(
                select(func.count(CallLog.id)).where(CallLog.outcome == "resolved")
            )
            resolved_calls = resolved.scalar() or 0

            escalated = await db.execute(
                select(func.count(CallLog.id)).where(CallLog.outcome == "escalated")
            )
            escalated_calls = escalated.scalar() or 0

            # average sentiment
            avg_sent = await db.execute(
                select(func.avg(CallLog.sentiment_avg))
            )
            avg_sentiment = round(avg_sent.scalar() or 0.0, 2)

            # calls by intent
            intent_rows = await db.execute(
                select(CallLog.intent, func.count(CallLog.id))
                .group_by(CallLog.intent)
            )
            calls_by_intent = {
                row[0]: row[1] for row in intent_rows.fetchall()
            }

            # calls by language
            lang_rows = await db.execute(
                select(CallLog.language, func.count(CallLog.id))
                .group_by(CallLog.language)
            )
            calls_by_language = {
                row[0]: row[1] for row in lang_rows.fetchall()
            }

            # fcr rate
            fcr = round(
                (resolved_calls / total_calls * 100) if total_calls > 0 else 0, 1
            )

            return {
                "total_calls":      total_calls,
                "resolved_calls":   resolved_calls,
                "escalated_calls":  escalated_calls,
                "fcr_percent":      fcr,
                "avg_sentiment":    avg_sentiment,
                "calls_by_intent":  calls_by_intent,
                "calls_by_language": calls_by_language,
            }

    except Exception as e:
        logger.error(f"Daily report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))