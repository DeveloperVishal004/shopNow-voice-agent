from backend.handlers.resolve import resolve_order
from loguru import logger


async def handle_product_query(entities: dict, session: dict) -> str:
    product_name = entities.get("product_name", "the product")
    query_type   = entities.get("query_type", "general information")

    base_context = f"""Product query received:\n- Product : {product_name}\n- Query   : {query_type}\nUse knowledge to answer. If unsure, tell the customer you will check."""

    # Order lookup here is best-effort enrichment (product answers can come from
    # the knowledge base alone), so a miss must NOT count toward escalation.
    try:
        order, _ = await resolve_order(entities, session, record_miss=False)
    except Exception as e:
        logger.error(f"Product DB check failed: {e}")
        return base_context

    if order:
        added_context = f"""Order context retrieved to assist with product specifics:\n- Order ID      : {order.id}\n- Item          : {order.item_name}\n- Current status: {order.status}\n- Order date    : {order.order_date}\n- Delivery date : {order.delivery_date or "Not yet delivered"}\n- Price         : {order.price}\n- Units         : {order.units_purchased}\n- Total Cost    : {order.total_cost}\n- Seller        : {order.seller}\n- Payment Stat  : {order.payment_status}\n- Payment Mode  : {order.payment_mode}\n- Refund Stat   : {order.refund_status}"""
        return base_context + "\n" + added_context

    return base_context
