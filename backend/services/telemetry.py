import logging
import sqlite3
from datetime import datetime
from uuid import uuid4

from backend.config import data_path
from backend.services.errors import TelemetryError

DB_PATH = data_path("telemetry.db")
logger = logging.getLogger(__name__)


def _get_connection() -> sqlite3.Connection:
    """Get a database connection with WAL mode for better concurrency."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.Error as exc:
        raise TelemetryError(f"Failed to open telemetry database: {str(exc)}") from exc
    return conn


def init_telemetry_db() -> None:
    """Initialize the telemetry database tables."""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_sessions (
                session_id TEXT PRIMARY KEY,
                timestamp DATETIME,
                system_prompt TEXT,
                target_model TEXT,
                format_type TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attack_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp DATETIME,
                target_model TEXT,
                attack_id TEXT,
                is_vulnerable BOOLEAN,
                evaluator_reason TEXT,
                FOREIGN KEY (session_id) REFERENCES test_sessions(session_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS waitlist_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                created_at DATETIME NOT NULL
            )
        """)
        conn.commit()
    except sqlite3.Error as exc:
        raise TelemetryError(f"Failed to initialize telemetry tables: {str(exc)}") from exc
    finally:
        conn.close()


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid4())


def log_test_session(
    session_id: str,
    system_prompt: str,
    target_model: str,
    format_type: str,
    results: list[dict],
) -> None:
    """Log a test session and all attack results to the telemetry database."""
    conn = _get_connection()
    try:
        timestamp = datetime.utcnow().isoformat()
        conn.execute(
            """
            INSERT OR IGNORE INTO test_sessions 
            (session_id, timestamp, system_prompt, target_model, format_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, timestamp, system_prompt, target_model, format_type),
        )
        attack_records = [
            (
                session_id,
                timestamp,
                target_model,
                result.get("attack_id", "unknown"),
                result.get("is_vulnerable", False),
                result.get("reason", ""),
            )
            for result in results
        ]
        conn.executemany(
            """
            INSERT INTO attack_logs 
            (session_id, timestamp, target_model, attack_id, is_vulnerable, evaluator_reason)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            attack_records,
        )
        conn.commit()
    except sqlite3.Error as exc:
        raise TelemetryError(f"Failed to persist telemetry records: {str(exc)}") from exc
    finally:
        conn.close()


def add_waitlist_lead(email: str) -> None:
    """Persist a waitlist lead email in telemetry database."""
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO waitlist_leads (email, created_at)
            VALUES (?, ?)
            """,
            (email, datetime.utcnow().isoformat()),
        )
        conn.commit()
    except sqlite3.Error as exc:
        raise TelemetryError(f"Failed to persist waitlist lead: {str(exc)}") from exc
    finally:
        conn.close()


# Initialize database on module import
try:
    init_telemetry_db()
except TelemetryError as exc:
    logger.warning("Telemetry initialization failed: %s", str(exc))
