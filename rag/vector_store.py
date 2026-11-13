"""
FAISS vector store builder, index persistence, and retrieval manager.
"""

import os
from pathlib import Path
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from config.settings import settings
from rag.embeddings import get_embeddings_model
from utils.logger import logger


def should_rebuild_index(index_path: Path, kb_dir: Path) -> bool:
    """Return True if index does not exist or if any KB markdown file is newer than the index."""
    faiss_file = index_path / "index.faiss"
    if not faiss_file.exists():
        return True

    index_mtime = faiss_file.stat().st_mtime
    for kb_file in kb_dir.glob("*.md"):
        if kb_file.stat().st_mtime > index_mtime:
            logger.info(f"Knowledge base file '{kb_file.name}' modified. Rebuilding FAISS index.")
            return True

    return False


def build_vector_store() -> FAISS:
    """Read markdown documents from knowledge base, chunk, embed, and build FAISS index."""
    kb_dir = settings.KNOWLEDGE_BASE_DIR
    index_path = settings.VECTOR_INDEX_PATH

    if not kb_dir.exists():
        kb_dir.mkdir(parents=True, exist_ok=True)

    documents: List[Document] = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )

    for md_file in kb_dir.glob("*.md"):
        try:
            loader = TextLoader(str(md_file), encoding="utf-8")
            loaded_docs = loader.load()
            for doc in loaded_docs:
                doc.metadata["source_file"] = md_file.name
                chunks = text_splitter.split_documents([doc])
                for chunk in chunks:
                    chunk.metadata["source_file"] = md_file.name
                documents.extend(chunks)
        except Exception as e:
            logger.error(f"Error loading document '{md_file.name}': {e}")

    if not documents:
        logger.warning("No markdown documents found in knowledge base directory.")
        # Fallback dummy doc to prevent crash
        documents = [Document(page_content="ParkSense policy rules.", metadata={"source_file": "default.md"})]

    embeddings = get_embeddings_model()
    logger.info(f"Building FAISS vector index from {len(documents)} document chunks...")
    vector_store = FAISS.from_documents(documents, embeddings)

    index_path.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(index_path))
    logger.info(f"FAISS index saved successfully to '{index_path}'.")
    return vector_store


def load_or_build_vector_store() -> FAISS:
    """Load FAISS index from disk or build if missing or outdated."""
    index_path = settings.VECTOR_INDEX_PATH
    kb_dir = settings.KNOWLEDGE_BASE_DIR

    if should_rebuild_index(index_path, kb_dir):
        return build_vector_store()

    try:
        embeddings = get_embeddings_model()
        logger.info(f"Loading FAISS index from disk '{index_path}'...")
        return FAISS.load_local(
            str(index_path),
            embeddings,
            allow_dangerous_deserialization=True
        )
    except Exception as e:
        logger.error(f"Failed to load FAISS index from disk: {e}. Rebuilding index...")
        return build_vector_store()
