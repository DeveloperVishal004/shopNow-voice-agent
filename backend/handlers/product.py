from sqlalchemy import select
from backend.db.database import AsyncSessionLocal
from backend.db.models import Order
from loguru import logger

async def handle_product_query(entities: dict, session: dict) -> str:
    product_name = entities.get("product_name", "the product")
    query_type   = entities.get("query_type", "general information")
    order_id = entities.get("order_id") or (session.get("order_context") or {}).get("id")

    base_context = f"""Product query received:\n- Product : {product_name}\n- Query   : {query_type}\nUse knowledge to answer. If unsure, tell the customer you will check."""

    if not order_id:
        return base_context

    try:
        async with AsyncSessionLocal() as db:
            clean_order_id = str(order_id).replace(" ", "").upper()
            if not clean_order_id.startswith("ORD-") and clean_order_id.startswith("ORD"):
                clean_order_id = clean_order_id.replace("ORD", "ORD-")

            result = await db.execute(select(Order).where((Order.id == order_id) | (Order.id == clean_order_id)))
            order = result.scalar_one_or_none()

            if order:
                added_context = f"""Order context retrieved to assist with product specifics:\n- Order ID      : {order.id}\n- Item          : {order.item_name}\n- Current status: {order.status}\n- Order date    : {order.order_date}\n- Delivery date : {order.delivery_date or "Not yet delivered"}\n- Price         : {order.price}\n- Units         : {order.units_purchased}\n- Total Cost    : {order.total_cost}\n- Seller        : {order.seller}\n- Payment Stat  : {order.payment_status}\n- Payment Mode  : {order.payment_mode}\n- Refund Stat   : {order.refund_status}"""
                return base_context + "\n" + added_context
    except Exception as e:
        logger.error(f"Product DB check failed: {e}")

    return base_context
