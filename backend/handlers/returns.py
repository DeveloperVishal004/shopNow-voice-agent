from backend.handlers.resolve import resolve_order
from loguru import logger


async def handle_return_refund(entities: dict, session: dict) -> str:
    reason = entities.get("reason", "not specified")

    try:
        order, order_id = await resolve_order(entities, session)
    except Exception as e:
        logger.error(f"Return handler failed: {e}")
        return "I am having trouble checking return eligibility. Please try again."

    if not order:
        if order_id:
            return f"I could not find order {order_id}. Please verify your order ID."
        return "Could you please share your order ID so I can check return eligibility?"

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
