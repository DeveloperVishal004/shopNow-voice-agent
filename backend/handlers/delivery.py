from backend.handlers.resolve import resolve_identity
from loguru import logger


async def handle_delivery_complaint(entities: dict, session: dict) -> str:
    complaint_type = entities.get("complaint_type", "not specified")

    try:
        status, result = await resolve_identity(entities, session)
    except Exception as e:
        logger.error(f"Delivery handler failed: {e}")
        return "I am having trouble fetching delivery details. Please try again."

    if status == "ask":
        return result

    order = result
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
