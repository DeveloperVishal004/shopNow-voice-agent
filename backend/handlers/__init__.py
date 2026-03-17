from backend.handlers.order_status import handle_order_status
from backend.handlers.returns      import handle_return_refund
from backend.handlers.payment      import handle_payment_issue
from backend.handlers.delivery     import handle_delivery_complaint
from backend.handlers.product      import handle_product_query

INTENT_HANDLERS = {
    "order_status":       handle_order_status,
    "return_refund":      handle_return_refund,
    "payment_issue":      handle_payment_issue,
    "delivery_complaint": handle_delivery_complaint,
    "product_query":      handle_product_query,
}