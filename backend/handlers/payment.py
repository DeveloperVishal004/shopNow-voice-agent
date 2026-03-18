from sqlalchemy import select
from backend.db.database import AsyncSessionLocal
from backend.db.models import Order
from loguru import logger


async def handle_payment_issue(entities: dict, session: dict) -> str:
    order_id   = entities.get("order_id") or (
        session.get("order_context") or {}
    ).get("id")
    issue_type = entities.get("issue_type", "not specified")

    if not order_id:
        return "Could you please share your order ID so I can look into the payment issue?"

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

            context = f"""
Payment issue details:
- Order ID      : {order.id}
- Item          : {order.item_name}
- Order date    : {order.order_date}
- Refund status : {order.refund_status}
- Issue type    : {issue_type}
- Total Cost    : {order.total_cost}
- Payment Stat  : {order.payment_status}
- Payment Mode  : {order.payment_mode}
"""
            logger.info(f"Payment issue for order: {order.id} | type: {issue_type}")
            return context

    except Exception as e:
        logger.error(f"Payment handler failed: {e}")
        return "I am having trouble fetching payment details. Please try again."