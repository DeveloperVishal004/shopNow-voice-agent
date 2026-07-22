from backend.handlers.resolve import resolve_identity
from loguru import logger


async def handle_payment_issue(entities: dict, session: dict) -> str:
    issue_type = entities.get("issue_type", "not specified")

    try:
        status, result = await resolve_identity(entities, session)
    except Exception as e:
        logger.error(f"Payment handler failed: {e}")
        return "I am having trouble fetching payment details. Please try again."

    if status == "ask":
        return result

    order = result
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
