from loguru import logger


async def handle_product_query(entities: dict, session: dict) -> str:
    """
    Product queries are answered via RAG in Phase 4.
    For now returns a context string for the LLM to work with.
    """
    product_name = entities.get("product_name", "the product")
    query_type   = entities.get("query_type", "general information")

    logger.info(f"Product query | product: {product_name} | type: {query_type}")

    # RAG will enrich this in Phase 4
    return f"""
Product query received:
- Product : {product_name}
- Query   : {query_type}
Use your knowledge to answer this query. 
If you are unsure, tell the customer you will check and get back to them.
"""