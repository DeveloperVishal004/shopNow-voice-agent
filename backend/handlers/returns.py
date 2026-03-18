from sqlalchemy import select
from backend.db.database import AsyncSessionLocal
from backend.db.models import Order
from loguru import logger


async def handle_return_refund(entities: dict, session: dict) -> str:
    order_id = entities.get("order_id") or (
        session.get("order_context") or {}
    ).get("id")
    reason   = entities.get("reason", "not specified")

    if not order_id:
        return "Could you please share your order ID so I can check return eligibility?"

    try:
        async with AsyncSessionLocal() as db:
            clean_order_id = str(order_id).replace(" ", "").upper()
            if not clean_order_id.startswith("ORD-") and clean_order_id.startswith("ORD"):
                clean_order_id = clean_order_id.replace("ORD", "ORD-")

            result = await db.execute(
                select(Order).where(
                    (Order.id == order_id) |
                    (Order.id == clean_order_id)
                )
            )
            order = result.scalar_one_or_none()

            if not order:
                return f"I could not find order {order_id}. Please verify your order ID."

            if order.return_eligible == "no":
                return f"""
Order {order.id} ({order.item_name}) is not eligible for return.
This could be because it has not been delivered yet or the return window has passed.
"""

            if order.refund_status == "processed":
                return f"Your refund for order {order.id} has already been processed."

            if order.refund_status == "initiated":
                return f"A return for order {order.id} is already in progress."

            context = f"""
Return eligibility check:
- Order ID      : {order.id}
- Item          : {order.item_name}
- Eligible      : Yes
- Reason given  : {reason}
- Refund status : {order.refund_status}
- Total Cost    : {order.total_cost}
- Units         : {order.units_purchased}
The return can be initiated for this order.
"""
            logger.info(f"Return eligible: {order.id}")
            return context

    except Exception as e:
        logger.error(f"Return handler failed: {e}")
        return "I am having trouble checking return eligibility. Please try again."