import logging
import os
import sqlite3
from typing import Any, Dict, Optional

logger = logging.getLogger("agent.db")

# Place memory.db in the backend folder
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory.db"
)


def init_db():
    logger.info(f"Initializing database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS escalations (
            reference_id TEXT PRIMARY KEY,
            reason TEXT,
            short_summary TEXT,
            checked_info TEXT,
            urgency TEXT,
            language TEXT,
            preferred_followup TEXT,
            status TEXT,
            created_at TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS calls (
            call_id TEXT PRIMARY KEY,
            call_type TEXT,
            status TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT user_id, name, language_preference, facts, last_interaction FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "user_id": row["user_id"],
                "name": row["name"],
                "language_preference": row["language_preference"],
                "facts": row["facts"],
                "last_interaction": row["last_interaction"],
            }
        return None
    finally:
        conn.close()


def save_user_db(
    user_id: str,
    name: str,
    language_preference: str,
    facts: str,
    last_interaction: str,
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (user_id, name, language_preference, facts, last_interaction)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name=excluded.name,
                language_preference=excluded.language_preference,
                facts=excluded.facts,
                last_interaction=excluded.last_interaction
            """,
            (user_id, name, language_preference, facts, last_interaction),
        )
        conn.commit()
    finally:
        conn.close()


def create_escalation(
    reason: str,
    short_summary: str,
    checked_info: str,
    urgency: str,
    language: str,
    preferred_followup: str = "phone",
) -> str:
    from datetime import datetime

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Get date in YYYYMMDD format
        today_str = datetime.now().strftime("%Y%m%d")

        # Get sequential count for today
        like_pattern = f"HA-{today_str}-%"
        cursor.execute(
            "SELECT COUNT(*) FROM escalations WHERE reference_id LIKE ?",
            (like_pattern,),
        )
        count = cursor.fetchone()[0]
        seq = count + 1
        reference_id = f"HA-{today_str}-{seq:03d}"

        created_at = datetime.now().isoformat()
        status = "OPEN"

        cursor.execute(
            """
            INSERT INTO escalations (
                reference_id, reason, short_summary, checked_info,
                urgency, language, preferred_followup, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reference_id,
                reason,
                short_summary,
                checked_info,
                urgency,
                language,
                preferred_followup,
                status,
                created_at,
            ),
        )
        conn.commit()
        logger.info(f"Escalation successfully created: {reference_id}")
        return reference_id
    except Exception as e:
        logger.exception("Failed to insert escalation into DB")
        raise e
    finally:
        conn.close()


def create_call(call_id: str, call_type: str, status: str = "failed") -> None:
    from datetime import datetime
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR IGNORE INTO calls (call_id, call_type, status, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (call_id, call_type, status, datetime.now().isoformat()),
        )
        conn.commit()
        logger.info(f"Call record created: {call_id} ({call_type})")
    except Exception as e:
        logger.exception(f"Failed to create call record for {call_id}")
    finally:
        conn.close()


def update_call_status(call_id: str, status: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE calls SET status = ? WHERE call_id = ?",
            (status, call_id),
        )
        conn.commit()
        logger.info(f"Call record updated: {call_id} -> {status}")
    except Exception as e:
        logger.exception(f"Failed to update call status for {call_id}")
    finally:
        conn.close()


def get_call_analytics() -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Safeguard: check if calls table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calls'")
        if not cursor.fetchone():
            return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}

        cursor.execute("SELECT COUNT(*) FROM calls")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM calls WHERE status = 'success'")
        success = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM calls WHERE status = 'failed'")
        failed = cursor.fetchone()[0]

        return {
            "total_calls": total,
            "successful_calls": success,
            "failed_calls": failed,
        }
    except Exception as e:
        logger.exception("Failed to get call analytics")
        return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
    finally:
        conn.close()


# Automatically initialize the database on module import
init_db()
