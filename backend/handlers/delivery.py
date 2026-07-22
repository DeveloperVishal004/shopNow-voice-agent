from backend.handlers.resolve import resolve_order
from loguru import logger


async def handle_delivery_complaint(entities: dict, session: dict) -> str:
    complaint_type = entities.get("complaint_type", "not specified")

    try:
        order, order_id = await resolve_order(entities, session)
    except Exception as e:
        logger.error(f"Delivery handler failed: {e}")
        return "I am having trouble fetching delivery details. Please try again."

    if not order:
        if order_id:
            return f"I could not find order {order_id}. Please verify your order ID."
        return "Could you please share your order ID so I can check your delivery status?"

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
