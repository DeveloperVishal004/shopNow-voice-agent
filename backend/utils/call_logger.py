import os
import json
import asyncio
from loguru import logger
from datetime import datetime

# We will use the existing openai client from llm
from backend.services.llm import client
from backend.config import settings

CALL_LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "call_logs"))
os.makedirs(CALL_LOGS_DIR, exist_ok=True)

async def summarize_call(transcript_text: str) -> str:
    """Uses LLM to summarize the given transcript."""
    if not transcript_text.strip():
        return "No conversation occurred."
        
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that summarizes customer support calls. Provide a brief 1-3 sentence summary of the customer's issue and how the agent resolved it. Do not include extra commentary, just the summary."
                },
                {
                    "role": "user",
                    "content": f"Here is the call transcript:\n\n{transcript_text}"
                }
            ],
            max_tokens=150,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        return "Summary could not be generated."

async def save_call_to_folder(call_id: str, session: dict):
    """Saves the call details, transcript, and a generated summary to a JSON file."""
    try:
        turns = session.get("turns", [])
        transcript_text = ""
        for t in turns:
            role = "Customer" if t.get("role") == "customer" else "Agent Priya"
            transcript_text += f"{role}: {t.get('text', '')}\n"
        
        summary = await summarize_call(transcript_text)
        
        data = {
            "call_id": call_id,
            "started_at": session.get("started_at"),
            "ended_at": session.get("ended_at") or datetime.now().isoformat(),
            "customer_phone": session.get("customer_id"),
            "summary": summary,
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
            f.write("-" * 40 + "\n")
            f.write("SUMMARY:\n")
            f.write(summary + "\n")
            f.write("-" * 40 + "\n")
            f.write("TRANSCRIPT:\n")
            f.write(transcript_text)
            
        # Optional: Save json as well
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Call logs saved successfully for call: {call_id}")
    except Exception as e:
        logger.error(f"Failed to save call log for {call_id}: {e}")
