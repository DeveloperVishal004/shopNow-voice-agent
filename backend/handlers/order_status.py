import json
from sqlalchemy import select, text
from backend.db.database import AsyncSessionLocal
from backend.db.models import Order
from loguru import logger


async def handle_order_status(entities: dict, session: dict) -> str:
    """
    Looks up order status from DB.
    Returns a natural language string the LLM will use to respond.
    """
    order_id      = entities.get("order_id")
    customer_phone = session.get("customer_phone")

    try:
        async with AsyncSessionLocal() as db:

            # try by order ID first
            if order_id:
                result = await db.execute(
                    select(Order).where(Order.id == order_id)
                )
                order = result.scalar_one_or_none()

            # fallback — look up by phone number
            elif customer_phone:
                result = await db.execute(
                    select(Order).where(Order.customer_phone == customer_phone)
                )
                order = result.scalars().first()

            else:
                return "I could not find your order. Could you please share your order ID?"

            if not order:
                return f"I could not find any order with ID {order_id}. Please check and try again."

            # store in session for later turns
            session["order_context"] = {
                "id":             order.id,
                "status":         order.status,
                "item_name":      order.item_name,
                "order_date":     order.order_date,
                "delivery_date":  order.delivery_date,
                "return_eligible": order.return_eligible
            }
            session["customer_name"] = order.customer_name

            # build context string for LLM
            context = f"""
Order found:
- Order ID     : {order.id}
- Item         : {order.item_name}
- Status       : {order.status}
- Order date   : {order.order_date}
- Delivery date: {order.delivery_date or 'Not yet delivered'}
- Customer name: {order.customer_name}
"""
            logger.info(f"Order found: {order.id} | status: {order.status}")
            return context

    except Exception as e:
        logger.error(f"Order status handler failed: {e}")
        return "I am having trouble fetching your order details right now. Please try again."