async def handle_general_query(entities: dict, session: dict) -> str:
    """
    Handles small talk, jokes, testing, greetings without a request, or
    anything unrelated to ShopNow orders/returns/payments/delivery/products.
    No DB lookup — just tells the response LLM to politely redirect the
    conversation. Deliberately does not touch order_context or the
    data-not-found streak, since nothing was actually looked up.
    """
    return (
        "The customer's message is small talk, unrelated chatter, or a joke — "
        "not a real ShopNow order-related request. Politely acknowledge it in one "
        "short line and steer the conversation back to how you can help with their "
        "order, return, payment, delivery, or product question."
    )
