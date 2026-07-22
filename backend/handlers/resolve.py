from sqlalchemy import select
from loguru import logger

from backend.db.database import AsyncSessionLocal
from backend.db.models import Order
from backend.memory.session import record_data_lookup, cache_order_context


def clean_order_id(order_id: str) -> str:
    """Normalize spoken/typed order IDs to canonical form, e.g. 'ord 1001' -> 'ORD-1001'."""
    cleaned = str(order_id).replace(" ", "").upper()
    if not cleaned.startswith("ORD-") and cleaned.startswith("ORD"):
        cleaned = cleaned.replace("ORD", "ORD-")
    return cleaned


async def resolve_order(entities: dict, session: dict, record_miss: bool = True):
    """
    The single, consistent order-resolution path used by EVERY handler.

    Precedence (identical everywhere):
      1. order_id extracted from this turn's entities,
      2. order_id from the order cached earlier in this call (order_context),
      3. the caller's phone number — but ONLY if it maps to exactly ONE order.
         A phone can belong to many orders, so we never act on an arbitrarily
         picked one; if it's ambiguous (0 or >1 matches) we leave it unresolved
         and let the handler ask for the order ID.

    Side effects, centralized so every handler behaves the same:
      - on a hit  : resets the data-not-found streak and caches the order,
      - on a miss : increments the streak, but only when an order_id was
        actually supplied (a missing ID is "we don't know which order", not
        "your order doesn't exist") and only when record_miss is True
        (product queries pass record_miss=False since their lookup is
        best-effort enrichment, not a required-data check).

    Returns (order_or_None, order_id_or_None) — order_id is the id we tried,
    so handlers can tailor "couldn't find ORD-x" vs "please share your ID".
    """
    order_id = entities.get("order_id") or (session.get("order_context") or {}).get("id")
    order = None

    async with AsyncSessionLocal() as db:
        if order_id:
            clean = clean_order_id(order_id)
            result = await db.execute(
                select(Order).where((Order.id == order_id) | (Order.id == clean))
            )
            order = result.scalar_one_or_none()
        elif session.get("customer_phone"):
            result = await db.execute(
                select(Order).where(Order.customer_phone == session["customer_phone"])
            )
            matches = result.scalars().all()
            if len(matches) == 1:            # unambiguous — safe to use
                order = matches[0]
                order_id = order.id
            elif len(matches) > 1:
                logger.info(
                    f"Phone maps to {len(matches)} orders — ambiguous, will ask for order ID"
                )

    if order:
        record_data_lookup(session, found=True)
        cache_order_context(session, order)
    elif order_id and record_miss:
        record_data_lookup(session, found=False)

    return order, order_id
