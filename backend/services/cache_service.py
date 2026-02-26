import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from typing import Generator

from backend.config import data_path

DB_PATH = data_path("cache.db")

_local = threading.local()


def _init_db(conn: sqlite3.Connection) -> None:
    """Initialize database tables."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    try:
        conn.execute("ALTER TABLE cache ADD COLUMN run_id TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    # Backfill run_id from JSON value for rows cached before this column existed
    conn.execute(
        "UPDATE cache SET run_id = json_extract(value, '$.run_id') WHERE run_id IS NULL"
    )
    conn.commit()


@contextmanager
def _get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Get a thread-local database connection with connection pooling."""
    if not hasattr(_local, "connection") or _local.connection is None:
        _local.connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _init_db(_local.connection)
    yield _local.connection


def make_cache_key(system_prompt: str, target_model: str, temperature: float = 0.7, response_format: str = "text") -> str:
    """Generate a cache key from request parameters."""
    raw = f"{system_prompt}|{target_model}|{temperature}|{response_format}"
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached_result(cache_key: str) -> dict | None:
    """Retrieve a cached result by key."""
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM cache WHERE key = ?", (cache_key,)
        ).fetchone()
        if row:
            return json.loads(row[0])
        return None


def store_result(cache_key: str, result: dict) -> None:
    """Store a result in the cache."""
    run_id = result.get("run_id")
    with _get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cache (key, value, run_id) VALUES (?, ?, ?)",
            (cache_key, json.dumps(result), run_id),
        )
        conn.commit()


def get_result_by_run_id(run_id: str) -> dict | None:
    """Retrieve a cached result by run_id."""
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM cache WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row:
            return json.loads(row[0])
        return None
