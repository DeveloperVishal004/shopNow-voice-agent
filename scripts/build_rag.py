import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from loguru import logger
from backend.config import settings

DOCUMENTS_DIR  = "./rag_store/documents"
INDEX_DIR      = "./rag_store/index"

def build_rag_index():
    logger.info("Starting RAG index build...")

    # step 1 — load all text files
    documents = []
    for filename in os.listdir(DOCUMENTS_DIR):
        if filename.endswith(".txt"):
            filepath = os.path.join(DOCUMENTS_DIR, filename)
            loader   = TextLoader(filepath, encoding="utf-8")
            docs     = loader.load()

            # tag each doc with its source filename
            for doc in docs:
                doc.metadata["source"] = filename

            documents.extend(docs)
            logger.info(f"Loaded: {filename} ({len(docs)} docs)")

    if not documents:
        logger.error("No documents found in rag_store/documents/")
        return

    logger.info(f"Total documents loaded: {len(documents)}")

    # step 2 — chunk documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = 500,   # characters per chunk
        chunk_overlap = 50,    # overlap to avoid losing context at boundaries
        separators    = ["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"Total chunks created: {len(chunks)}")

    # step 3 — embed chunks using OpenAI
    logger.info("Embedding chunks with OpenAI text-embedding-3-small...")
    embeddings = OpenAIEmbeddings(
        model      = settings.embedding_model,
        api_key    = settings.openai_api_key
    )

    # step 4 — build FAISS index
    vectorstore = FAISS.from_documents(chunks, embeddings)
    logger.info("FAISS index built successfully")

    # step 5 — save index to disk
    os.makedirs(INDEX_DIR, exist_ok=True)
    vectorstore.save_local(INDEX_DIR)
    logger.info(f"FAISS index saved to {INDEX_DIR}")

    # quick test
    logger.info("Running quick retrieval test...")
    results = vectorstore.similarity_search("what is the return policy?", k=2)
    for i, r in enumerate(results):
        logger.info(f"Test result {i+1}: {r.page_content[:100]}...")

    logger.info("RAG index build complete")

if __name__ == "__main__":
    build_rag_index()