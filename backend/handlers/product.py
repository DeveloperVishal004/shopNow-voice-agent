from backend.handlers.resolve import resolve_order, resolve_identity
from loguru import logger


async def handle_product_query(entities: dict, session: dict) -> str:
    product_name = entities.get("product_name", "the product")
    query_type   = entities.get("query_type", "general information")

    base_context = f"""Product query received:\n- Product : {product_name}\n- Query   : {query_type}\nUse knowledge to answer. If unsure, tell the customer you will check."""

    try:
        # If we're mid-way through an identity-disambiguation dialog (e.g. the
        # customer answered "which product?" with a name that classified as a
        # product query), continue that dialog so it doesn't stall.
        if session.get("resolution_stage"):
            status, result = await resolve_identity(entities, session)
            if status == "ask":
                return result
            order = result
        else:
            # Normal product query: order lookup is best-effort enrichment only,
            # so a miss must NOT count toward escalation.
            order, _ = await resolve_order(entities, session, record_miss=False)
    except Exception as e:
        logger.error(f"Product DB check failed: {e}")
        return base_context

    if order:
        added_context = f"""Order context retrieved to assist with product specifics:\n- Order ID      : {order.id}\n- Item          : {order.item_name}\n- Current status: {order.status}\n- Order date    : {order.order_date}\n- Delivery date : {order.delivery_date or "Not yet delivered"}\n- Price         : {order.price}\n- Units         : {order.units_purchased}\n- Total Cost    : {order.total_cost}\n- Seller        : {order.seller}\n- Payment Stat  : {order.payment_status}\n- Payment Mode  : {order.payment_mode}\n- Refund Stat   : {order.refund_status}"""
        return base_context + "\n" + added_context

    return base_context
