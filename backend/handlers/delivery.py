from sqlalchemy import select
from backend.db.database import AsyncSessionLocal
from backend.db.models import Order
from loguru import logger


async def handle_delivery_complaint(entities: dict, session: dict) -> str:
    order_id       = entities.get("order_id") or (
        session.get("order_context") or {}
    ).get("id")
    complaint_type = entities.get("complaint_type", "not specified")

    if not order_id:
        return "Could you please share your order ID so I can check your delivery status?"

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
Delivery complaint details:
- Order ID      : {order.id}
- Item          : {order.item_name}
- Current status: {order.status}
- Order date    : {order.order_date}
- Delivery date : {order.delivery_date or 'Not yet delivered'}
- Complaint type: {complaint_type}
- Seller        : {order.seller}
- Units         : {order.units_purchased}
"""
            logger.info(f"Delivery complaint for order: {order.id} | type: {complaint_type}")
            return context

    except Exception as e:
        logger.error(f"Delivery handler failed: {e}")
        return "I am having trouble fetching delivery details. Please try again."