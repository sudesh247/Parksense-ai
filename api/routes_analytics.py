"""
FastAPI route handlers for analytics statistics and system health checks.
"""

from fastapi import APIRouter
from database.connection import get_db
from services.analytics_service import compute_dashboard_statistics
from rag.llm_provider import is_ollama_available
from config.settings import settings
from api.schemas import StatisticsResponse, HealthResponse

router = APIRouter(prefix="/api", tags=["Analytics & Health"])


@router.get("/statistics", response_model=StatisticsResponse)
def get_statistics():
    """Retrieve full analytical payload for dashboard stat cards and Plotly charts."""
    with get_db() as conn:
        return compute_dashboard_statistics(conn)


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Check service health, Ollama availability, and FAISS index status."""
    ollama_ready = is_ollama_available()
    faiss_file = settings.VECTOR_INDEX_PATH / "index.faiss"
    faiss_ready = faiss_file.exists()

    return HealthResponse(
        status="healthy",
        ollama_ready=ollama_ready,
        vector_index_ready=faiss_ready
    )
