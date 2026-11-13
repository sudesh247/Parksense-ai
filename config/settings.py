"""
Application settings configuration loader using environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file if present
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv(dotenv_path=BASE_DIR / ".env.example")


class Settings:
    """Type-safe application configuration settings."""

    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Database
    DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "database/parksense.db")

    # LLM & RAG
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    VECTOR_INDEX_PATH: Path = BASE_DIR / os.getenv("VECTOR_INDEX_PATH", "rag/index")
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "4"))
    KNOWLEDGE_BASE_DIR: Path = BASE_DIR / "rag" / "knowledge_base"


settings = Settings()
