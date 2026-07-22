import re
from sqlalchemy import select
from loguru import logger

from backend.db.database import AsyncSessionLocal
from backend.db.models import Order
from backend.memory.session import record_data_lookup, cache_order_context


def clean_order_id(order_id: str) -> str:
    """Normalize spoken/typed order IDs, e.g. 'ord 1001' -> 'ORD-1001'."""
    cleaned = str(order_id).replace(" ", "").upper()
    if not cleaned.startswith("ORD-") and cleaned.startswith("ORD"):
        cleaned = cleaned.replace("ORD", "ORD-")
    return cleaned


def _digits(phone) -> str:
    """Last 10 digits of a phone, for tolerant matching (+91 98765 01001 == 9876501001)."""
    return re.sub(r"\D", "", phone or "")[-10:]


async def _find_by_id(db, order_id):
    clean = clean_order_id(order_id)
    result = await db.execute(select(Order).where((Order.id == order_id) | (Order.id == clean)))
    return result.scalar_one_or_none()


async def _find_by_phone(db, phone):
    d = _digits(phone)
    if len(d) < 6:
        return []
    result = await db.execute(select(Order))
    return [o for o in result.scalars().all() if _digits(o.customer_phone) == d]


async def _find_by_phone_product(db, phone, product):
    orders = await _find_by_phone(db, phone)
    p = (product or "").lower().strip()
    return [o for o in orders if p and p in (o.item_name or "").lower()]


def _resolve(session, order):
    """A confirmed order: reset the dialog, reset the miss streak, cache it."""
    record_data_lookup(session, found=True)
    cache_order_context(session, order)
    session["resolution_stage"] = None
    session["disambig_phone"] = None
    return ("resolved", order)


async def resolve_identity(entities: dict, session: dict):
    """
    Conversational identity resolution shared by every order handler.

    Progressive ladder (order ID > phone > product), tracked across turns via
    session["resolution_stage"]:
      1. order_id (this turn or cached) -> look up, done.
      2. no id                          -> ask for the order ID.
      3. asked, still no id             -> ask for the phone used to order.
      4. phone -> 1 order  -> use it
                  0 orders  -> couldn't find any
                  many      -> ask "which product?"
      5. product -> 1 match -> use it
                    0        -> ask for exact name / order ID
                    many     -> ask for more info (order ID / date)

    "Customer doesn't have the ID/phone" is inferred from *absence* (they were
    asked and provided none) rather than phrase-detection, which is far more
    robust. Escalation runs in parallel (unchanged), so a stuck or frustrated
    customer still gets handed to a human.

    Returns (status, payload):
      ("resolved", <Order>)   -> handler formats its own fields
      ("ask", <message str>)  -> handler returns this for the LLM to voice
    """
    order_id = entities.get("order_id") or (session.get("order_context") or {}).get("id")

    async with AsyncSessionLocal() as db:
        # --- 1. a concrete order ID (this turn or cached) always wins ---
        if order_id:
            order = await _find_by_id(db, order_id)
            if order:
                return _resolve(session, order)
            # ID supplied but not found -> counts as a data miss (feeds escalation)
            record_data_lookup(session, found=False)
            session["resolution_stage"] = "awaiting_id"
            return ("ask", f"I could not find order {order_id}. Could you double-check the ID, "
                           f"or let me know if you don't have it?")

        stage = session.get("resolution_stage")

        # --- 2. first time with no ID: ask for it ---
        if not stage:
            session["resolution_stage"] = "awaiting_id"
            return ("ask", "Sure — could you please share your order ID?")

        # --- 3. asked for the ID, still none given: ask for the phone ---
        if stage == "awaiting_id":
            session["resolution_stage"] = "awaiting_phone"
            return ("ask", "No problem. What phone number did you use to place the order?")

        # --- 4. asked for the phone ---
        if stage == "awaiting_phone":
            phone = entities.get("customer_phone")
            if not phone:
                session["resolution_stage"] = None
                return ("ask", "I'm sorry — without an order ID or the phone number used for the "
                               "order, I'm not able to locate it.")
            orders = await _find_by_phone(db, phone)
            if len(orders) == 0:
                session["resolution_stage"] = None
                return ("ask", "I couldn't find any orders under that phone number. Could you "
                               "double-check the number, or the order ID?")
            if len(orders) == 1:
                return _resolve(session, orders[0])
            session["resolution_stage"] = "awaiting_product"
            session["disambig_phone"] = phone
            names = ", ".join(sorted({o.item_name for o in orders if o.item_name})[:4])
            return ("ask", f"I can see a few orders under that number. Which product is it about?"
                           + (f" (for example: {names})" if names else ""))

        # --- 5. asked which product ---
        if stage == "awaiting_product":
            product = entities.get("product_name")
            phone = session.get("disambig_phone")
            if not product:
                return ("ask", "Which product is your query about?")
            matches = await _find_by_phone_product(db, phone, product)
            if len(matches) == 1:
                return _resolve(session, matches[0])
            if len(matches) == 0:
                return ("ask", "I couldn't match that product to your orders. Could you share the "
                               "exact product name, or the order ID?")
            # still multiple (same product name on this number) -> need more
            return ("ask", "You have more than one order for that product. Do you have the order "
                           "ID, or roughly the order date?")

    # unreachable safety net
    session["resolution_stage"] = "awaiting_id"
    return ("ask", "Could you please share your order ID?")


async def resolve_order(entities: dict, session: dict, record_miss: bool = True):
    """
    Best-effort, NON-conversational resolution used by product queries, which
    can be answered from the knowledge base without an order. Precedence:
    order_id (this turn or cached) -> unambiguous phone. Never drives the
    ask-for-ID dialog. Returns (order_or_None, order_id_or_None).
    """
    order_id = entities.get("order_id") or (session.get("order_context") or {}).get("id")
    order = None
    async with AsyncSessionLocal() as db:
        if order_id:
            order = await _find_by_id(db, order_id)
        elif session.get("customer_phone"):
            matches = await _find_by_phone(db, session["customer_phone"])
            if len(matches) == 1:
                order = matches[0]
                order_id = order.id
    if order:
        record_data_lookup(session, found=True)
        cache_order_context(session, order)
    elif order_id and record_miss:
        record_data_lookup(session, found=False)
    return order, order_id
