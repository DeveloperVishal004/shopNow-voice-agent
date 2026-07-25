import os
import json
import asyncio
from loguru import logger
from datetime import datetime

# We will use the existing openai client from llm
from backend.services.llm import client
from backend.config import settings

# For DB logging
from backend.db.database import AsyncSessionLocal
from backend.db.models import CallLog, EscalationLog
from backend.services.sentiment import get_average_sentiment

CALL_LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "call_logs"))
os.makedirs(CALL_LOGS_DIR, exist_ok=True)

# Whole-call purpose categories the post-call classifier may choose from.
# The 6 live intents + positive_feedback (praise/thanks, no request) + other.
CALL_CATEGORIES = [
    "order_status", "return_refund", "payment_issue", "delivery_complaint",
    "product_query", "positive_feedback", "general_or_unrelated", "other",
]


async def summarize_and_categorize_call(transcript_text: str, fallback_category: str = "other"):
    """
    Single LLM call that both summarizes the transcript AND classifies the
    call's *overall purpose* from the full conversation (not one utterance).

    Whole-call context is what makes this reliable for reporting — e.g. a
    call whose only purpose is to thank the company is classified
    'positive_feedback', which a per-utterance intent classifier (focused on
    routing to a handler) has no dedicated category for.

    Returns (summary, category). Falls back gracefully on any failure so the
    call still logs.
    """
    if not transcript_text.strip():
        return "No conversation occurred.", fallback_category

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You summarize and categorize a completed customer support call. "
                        "Return ONLY a JSON object with two keys:\n"
                        '  "summary": a brief 1-3 sentence summary of the customer\'s issue and how it was handled.\n'
                        '  "category": the call\'s PRIMARY purpose, exactly one of: '
                        + ", ".join(CALL_CATEGORIES) + ".\n"
                        "Use 'positive_feedback' when the customer's main purpose was to "
                        "thank, praise, or express satisfaction with no other request. "
                        "Use 'other' only if nothing else fits. "
                        "Judge the call as a whole, not just the first message."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Here is the call transcript:\n\n{transcript_text}",
                },
            ],
            max_tokens=200,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)
        summary = (data.get("summary") or "Summary could not be generated.").strip()
        category = (data.get("category") or fallback_category).strip()
        if category not in CALL_CATEGORIES:
            category = fallback_category
        return summary, category
    except Exception as e:
        logger.error(f"Failed to summarize/categorize call: {e}")
        return "Summary could not be generated.", fallback_category

async def save_escalation_log(brief: dict):
    """
    Persist an escalation hand-off brief to the escalation_logs table.

    Without this, the EscalationLog table was defined and read by
    /report/escalation/{call_id} (as the fallback for a call that already
    ended) but never written — so that fallback always 404'd and there was
    no durable audit trail of why calls escalated. We key the row on call_id
    (one escalation per call, since the call ends on hand-off) so a repeated
    trigger can't create duplicate rows.
    """
    if not brief:
        return
    try:
        call_id = brief.get("call_id")
        if not call_id:
            return

        reason  = brief.get("escalation_reason", "")
        snippet = brief.get("conversation_snippet", "")
        issue_summary = (
            f"{reason}\n\nRecent conversation:\n{snippet}" if snippet else reason
        )

        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            existing = await db.execute(
                select(EscalationLog).where(EscalationLog.id == call_id)
            )
            if existing.scalar_one_or_none():
                return  # already persisted for this call

            row = EscalationLog(
                id                = call_id,
                call_id           = call_id,
                customer_name     = brief.get("customer_name", "Unknown"),
                issue_summary     = issue_summary,
                sentiment_history = json.dumps(brief.get("sentiment_history", [])),
                recommended_tone  = brief.get("recommended_tone", ""),
                resolved          = "no",  # just handed off; human hasn't resolved yet
            )
            db.add(row)
            await db.commit()
            logger.info(f"Escalation persisted to DB | call: {call_id}")
    except Exception as e:
        logger.error(f"Failed to persist escalation log for brief: {e}")


async def save_call_to_folder(call_id: str, session: dict):
    """Saves the call details, transcript, and a generated summary to a JSON file."""
    try:
        turns = session.get("turns", [])
        transcript_text = ""
        for t in turns:
            role = "Customer" if t.get("role") == "customer" else "Agent Priya"
            transcript_text += f"{role}: {t.get('text', '')}\n"
        
        # Whole-call summary + purpose category, in one LLM call.
        # Fall back to the last live intent if categorization can't decide.
        fallback_category = session.get("current_intent") or "other"
        summary, call_category = await summarize_and_categorize_call(
            transcript_text, fallback_category=fallback_category
        )

        data = {
            "call_id": call_id,
            "started_at": session.get("started_at"),
            "ended_at": session.get("ended_at") or datetime.now().isoformat(),
            "customer_phone": session.get("customer_id"),
            "summary": summary,
            "call_category": call_category,
            "transcript": turns,
            "raw_transcript_text": transcript_text
        }
        
        filepath = os.path.join(CALL_LOGS_DIR, f"{call_id}.json")
        
        # We can also save a human-readable text file
        txt_filepath = os.path.join(CALL_LOGS_DIR, f"{call_id}.txt")
        with open(txt_filepath, "w", encoding="utf-8") as f:
            f.write(f"Call ID: {call_id}\n")
            f.write(f"Started At: {data['started_at']}\n")
            f.write(f"Ended At: {data['ended_at']}\n")
            f.write(f"Customer Phone: {data['customer_phone']}\n")
            f.write(f"Category: {call_category}\n")
            f.write("-" * 40 + "\n")
            f.write("SUMMARY:\n")
            f.write(summary + "\n")
            f.write("-" * 40 + "\n")
            f.write("TRANSCRIPT:\n")
            f.write(transcript_text)
            
        # Optional: Save json as well
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        # ---------------------------------------------------------
        # ALSO LOG TO THE SQLITE DATABASE FOR THE DASHBOARD
        # ---------------------------------------------------------
        avg_sent = get_average_sentiment(session.get("sentiment_history", []))
        
        # Determine outcome based on the boolean flags set by end_session
        outcome = "escalated" if session.get("escalated") else "resolved"

        async with AsyncSessionLocal() as db:
            # Check if this call_id is already logged (avoid dupes if both API and WS trigger it)
            from sqlalchemy import select
            existing = await db.execute(select(CallLog).where(CallLog.id == call_id))
            if not existing.scalar_one_or_none():
                call_log = CallLog(
                    id            = call_id,
                    customer_id   = session.get("customer_id") or "Unknown",
                    language      = session.get("language", "en"),
                    intent        = session.get("current_intent", "unknown"),
                    call_category = call_category,
                    outcome       = outcome,
                    duration_secs = 0, # we don't have accurate duration here unless we compute it
                    sentiment_avg = avg_sent,
                    transcript    = json.dumps(turns)
                )
                db.add(call_log)
                await db.commit()
                logger.info(f"Call {call_id} successfully persisted to SQLite DB.")
    except Exception as e:
        logger.error(f"Failed to save call log for {call_id}: {e}")
