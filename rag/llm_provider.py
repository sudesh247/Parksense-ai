"""
LLM Provider abstraction supporting Ollama with graceful fallback handling.
"""

import httpx
from typing import Any, Optional
from langchain_community.llms import Ollama
from config.settings import settings
from utils.logger import logger


def is_ollama_available() -> bool:
    """Check if the local Ollama server is running and reachable."""
    try:
        response = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def get_llm() -> Optional[Any]:
    """
    Instantiate and return the configured LLM wrapper.
    Supports Ollama provider out of the box with offline detection.
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "ollama":
        if not is_ollama_available():
            logger.warning(f"Ollama server not reachable at {settings.OLLAMA_BASE_URL}")
            return None

        return Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.2,
        )

    elif provider == "openai":
        raise NotImplementedError(
            "OpenAI provider is disabled per project specification (Zero Paid API Keys). "
            "Set LLM_PROVIDER=ollama in your .env file."
        )

    else:
        raise ValueError(f"Unsupported LLM provider: '{provider}'")
