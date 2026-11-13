"""
RAG Engine orchestrating FAISS document retrieval and prompt execution.
"""

import re
from typing import Dict, Any, List
from config.settings import settings
from rag.vector_store import load_or_build_vector_store
from rag.llm_provider import get_llm, is_ollama_available
from rag.prompts import POLICY_RAG_PROMPT
from utils.logger import logger

_vector_store = None


def get_active_vector_store():
    """Singleton accessor for the loaded FAISS vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = load_or_build_vector_store()
    return _vector_store


def answer_policy_question(question: str) -> Dict[str, Any]:
    """
    Execute RAG pipeline for policy questions:
    FAISS Retrieval -> Context formatting -> LLM Generation.
    Falls back gracefully if Ollama is not running.
    """
    vector_store = get_active_vector_store()
    top_k = settings.RETRIEVAL_TOP_K

    # Perform similarity search
    results_with_scores = vector_store.similarity_search_with_score(question, k=top_k)

    context_passages = []
    source_docs = set()

    for doc, _score in results_with_scores:
        src = doc.metadata.get("source_file", "policy_doc.md")
        source_docs.add(src)
        context_passages.append(f"--- Document: {src} ---\n{doc.page_content}")

    context_str = "\n\n".join(context_passages)
    sources_list = sorted(list(source_docs))

    # Check Ollama availability
    if not is_ollama_available():
        logger.info("Ollama unavailable for RAG. Returning structured context fallback.")
        raw_text = context_passages[0] if context_passages else 'No document excerpts found.'
        clean_text = re.sub(r"^--- Document: .*? ---\n", "", raw_text).strip()
        fallback_answer = (
            "📋 **Verified Policy Information:**\n\n"
            f"{clean_text}\n\n"
            "💡 *(Note: Local Ollama LLM is offline. Serving direct verified policy facts.)*"
        )
        return {
            "answer": fallback_answer,
            "retrieved_docs": sources_list,
            "llm_used": False,
        }

    try:
        llm = get_llm()
        if llm is None:
            raise RuntimeError("LLM instance creation returned None.")

        prompt = POLICY_RAG_PROMPT.format(question=question, context=context_str)
        raw_response = llm.invoke(prompt)

        return {
            "answer": str(raw_response).strip(),
            "retrieved_docs": sources_list,
            "llm_used": True,
        }
    except Exception as e:
        logger.error(f"Error during RAG generation: {e}")
        return {
            "answer": (
                "An error occurred while generating the policy answer. "
                f"Retrieved relevant documents: {', '.join(sources_list)}. "
                "Please ensure Ollama model 'llama3.2:3b' is pulled and operational."
            ),
            "retrieved_docs": sources_list,
            "llm_used": False,
        }
