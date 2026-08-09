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


# Automatically initialize the database on module import
init_db()
