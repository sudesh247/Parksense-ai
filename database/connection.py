"""
SQLite database connection helper and context manager.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator
from config.settings import settings
from utils.logger import logger


def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    """Convert SQLite row tuples to dictionaries."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_db_connection() -> sqlite3.Connection:
    """Create and return a configured SQLite connection."""
    settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(settings.DATABASE_PATH), timeout=10.0)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite database transactions."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction error: {e}")
        raise
    finally:
        conn.close()
