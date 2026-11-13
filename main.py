"""
Main FastAPI application entry point for ParkSense AI.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from config.settings import settings
from database.seed import seed_database_if_empty
from rag.vector_store import load_or_build_vector_store
from api.routes_slots import router as slots_router
from api.routes_bookings import router as bookings_router
from api.routes_analytics import router as analytics_router
from api.routes_chat import router as chat_router
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for database initialization, seeding, and FAISS index setup."""
    logger.info("Initializing ParkSense AI service...")

    # 1. Database seed check
    try:
        seed_database_if_empty()
    except Exception as e:
        logger.error(f"Error seeding database: {e}")

    # 2. Vector Store initialize
    try:
        load_or_build_vector_store()
    except Exception as e:
        logger.error(f"Error initializing vector store: {e}")

    logger.info("ParkSense AI startup completed successfully.")
    yield
    logger.info("Shutting down ParkSense AI service.")


app = FastAPI(
    title="ParkSense AI — Smart Parking Analytics Platform",
    description="AI-powered multi-floor parking management, analytics, and hybrid RAG assistant.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register API Routers
app.include_router(slots_router)
app.include_router(bookings_router)
app.include_router(analytics_router)
app.include_router(chat_router)

# Mount static files directory
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    """Serve single-page static HTML interface."""
    index_file = static_dir / "index.html"
    return FileResponse(str(index_file))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=settings.DEBUG)
