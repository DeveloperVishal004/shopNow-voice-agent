from backend.handlers.resolve import resolve_identity
from loguru import logger


async def handle_order_status(entities: dict, session: dict) -> str:
    """Looks up order status via the shared conversational resolver."""
    try:
        status, result = await resolve_identity(entities, session)
    except Exception as e:
        logger.error(f"Order status handler failed: {e}")
        return "I am having trouble fetching your order details right now. Please try again."

    if status == "ask":
        return result   # a question for the LLM to voice (asking for ID / phone / product)

    order = result
    context = f"""
Order found:
- Order ID     : {order.id}
- Item         : {order.item_name}
- Status       : {order.status}
- Order date   : {order.order_date}
- Delivery date: {order.delivery_date or 'Not yet delivered'}
- Customer name: {order.customer_name}
- Price        : {order.price}
- Units        : {order.units_purchased}
- Total Cost   : {order.total_cost}
- Seller       : {order.seller}
- Payment Stat : {order.payment_status}
- Payment Mode : {order.payment_mode}
- Refund Stat  : {order.refund_status}
"""
    logger.info(f"Order found: {order.id} | status: {order.status}")
    return context
