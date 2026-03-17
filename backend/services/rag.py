import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from loguru import logger
from backend.config import settings

vectorstore = None

def load_index():
    """
    Loads FAISS index from disk into memory.
    Called once on startup.
    """
    global vectorstore

    index_path = settings.faiss_index_path.replace("/faiss.index", "")

    if not os.path.exists(index_path):
        logger.warning(f"FAISS index not found at {index_path} — RAG disabled")
        return

    try:
        embeddings  = OpenAIEmbeddings(
            model   = settings.embedding_model,
            api_key = settings.openai_api_key
        )
        vectorstore = FAISS.load_local(
            index_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        logger.info("FAISS index loaded successfully")

    except Exception as e:
        logger.error(f"Failed to load FAISS index: {e}")


def retrieve_context(query: str, k: int = 3) -> str:
    """
    Takes a query string, returns top k relevant chunks
    as a single string to inject into the LLM prompt.
    """
    if not vectorstore:
        logger.warning("RAG vectorstore not loaded — skipping retrieval")
        return ""

    try:
        results = vectorstore.similarity_search(query, k=k)

        if not results:
            return ""

        # combine chunks into one context string
        context_parts = []
        for i, doc in enumerate(results):
            source = doc.metadata.get("source", "unknown")
            context_parts.append(
                f"[Source: {source}]\n{doc.page_content}"
            )

        context = "\n\n".join(context_parts)
        logger.info(f"RAG retrieved {len(results)} chunks for: {query[:60]}...")
        return context

    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return ""