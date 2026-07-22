from backend.handlers.resolve import resolve_identity
from loguru import logger


async def handle_return_refund(entities: dict, session: dict) -> str:
    reason = entities.get("reason", "not specified")

    try:
        status, result = await resolve_identity(entities, session)
    except Exception as e:
        logger.error(f"Return handler failed: {e}")
        return "I am having trouble checking return eligibility. Please try again."

    if status == "ask":
        return result

    order = result

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
