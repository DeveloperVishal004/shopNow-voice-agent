from backend.handlers.resolve import resolve_order
from loguru import logger


async def handle_order_status(entities: dict, session: dict) -> str:
    """
    Looks up order status from DB via the shared resolver.
    Returns a natural language string the LLM will use to respond.
    """
    try:
        order, order_id = await resolve_order(entities, session)
    except Exception as e:
        logger.error(f"Order status handler failed: {e}")
        return "I am having trouble fetching your order details right now. Please try again."

    if not order:
        if order_id:
            return f"I could not find any order with ID {order_id}. Please check and try again."
        return "I could not find your order. Could you please share your order ID?"

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
