"""
SentenceTransformers embedding loader for ParkSense AI RAG pipeline.
"""

from langchain_community.embeddings import HuggingFaceEmbeddings
from config.settings import settings
from utils.logger import logger


def get_embeddings_model() -> HuggingFaceEmbeddings:
    """Initialize and return the SentenceTransformers embedding model wrapper."""
    logger.info(f"Initializing embedding model: '{settings.EMBEDDING_MODEL}'")
    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
