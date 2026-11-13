"""
FastAPI route handler for the AI Parking Assistant chat endpoint.
"""

from fastapi import APIRouter
from database.connection import get_db
from services.assistant_service import handle_assistant_question
from api.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["AI Assistant"])


@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(body: ChatRequest):
    """Process user natural-language questions through the hybrid router (SQL / RAG / Refusal)."""
    with get_db() as conn:
        return handle_assistant_question(conn, body.question)
