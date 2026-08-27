"""
Database module for AI Game Coach.
Provides persistent SQLite storage for users and chat history.
Zero-dependency setup using Python's built-in sqlite3.
"""

import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager

# ─────────────────────────────────────────────
#  Database Configuration & Connection
# ─────────────────────────────────────────────
def get_db_path() -> str:
    """Resolve the SQLite database path from environment or default instance dir."""
    db_path = os.getenv("DATABASE_PATH")
    if db_path:
        # Ensure parent directory exists if specified
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        return db_path

    # Default to instance/ai_game_coach.db relative to this file
    base_dir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(base_dir, "instance")
    os.makedirs(instance_dir, exist_ok=True)
    return os.path.join(instance_dir, "ai_game_coach.db")


@contextmanager
def get_db_connection():
    """Context manager for SQLite database connection with row factory."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  Schema Initialization
# ─────────────────────────────────────────────
def init_db():
    """Initialize database tables if they do not already exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sessions INTEGER DEFAULT 0,
                messages_sent INTEGER DEFAULT 0,
                favorite_game TEXT DEFAULT 'general',
                rank_points INTEGER DEFAULT 0
            )
        """)

        # Chat logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                game TEXT NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Indexes for fast querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_username ON chat_logs(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_game ON chat_logs(game)")


# ─────────────────────────────────────────────
#  User Management Queries
# ─────────────────────────────────────────────
def get_user(username: str) -> dict | None:
    """Retrieve user dictionary by username."""
    if not username:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username.lower().strip(),))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "created_at": row["created_at"],
            "stats": {
                "sessions": row["sessions"],
                "messages_sent": row["messages_sent"],
                "favorite_game": row["favorite_game"],
                "rank_points": row["rank_points"]
            }
        }


def get_user_by_email(email: str) -> dict | None:
    """Retrieve user dictionary by email."""
    if not email:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "created_at": row["created_at"],
            "stats": {
                "sessions": row["sessions"],
                "messages_sent": row["messages_sent"],
                "favorite_game": row["favorite_game"],
                "rank_points": row["rank_points"]
            }
        }


def create_user(username: str, email: str, password_hash: str) -> dict:
    """Insert a new user and return user record."""
    username = username.lower().strip()
    email = email.lower().strip()
    created_at = datetime.now().isoformat()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, created_at, sessions, messages_sent, favorite_game, rank_points)
            VALUES (?, ?, ?, ?, 0, 0, 'general', 0)
            """,
            (username, email, password_hash, created_at)
        )
        user_id = cursor.lastrowid

    return {
        "id": user_id,
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "created_at": created_at,
        "stats": {
            "sessions": 0,
            "messages_sent": 0,
            "favorite_game": "general",
            "rank_points": 0
        }
    }


def increment_user_session(username: str):
    """Increment user login session count."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET sessions = sessions + 1 WHERE username = ?",
            (username.lower().strip(),)
        )


def update_user_stats(username: str, game_type: str):
    """Increment messages_sent count, update favorite_game and rank_points."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET messages_sent = messages_sent + 1,
                favorite_game = ?,
                rank_points = rank_points + 10
            WHERE username = ?
            """,
            (game_type, username.lower().strip())
        )


# ─────────────────────────────────────────────
#  Chat Logs Management Queries
# ─────────────────────────────────────────────
def save_chat_log(username: str, game: str, message: str, response: str):
    """Save a chat message and AI response to the database."""
    username = username.lower().strip()
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_logs (username, game, message, response, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, game, message, response, now)
        )


def get_user_history(username: str, game_filter: str = None) -> list:
    """Get chat history list for user, optionally filtered by game."""
    username = username.lower().strip()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if game_filter:
            cursor.execute(
                """
                SELECT game, message, response, timestamp
                FROM chat_logs
                WHERE username = ? AND game = ?
                ORDER BY id ASC
                """,
                (username, game_filter)
            )
        else:
            cursor.execute(
                """
                SELECT game, message, response, timestamp
                FROM chat_logs
                WHERE username = ?
                ORDER BY id ASC
                """,
                (username,)
            )
        rows = cursor.fetchall()
        return [
            {
                "game": r["game"],
                "message": r["message"],
                "response": r["response"],
                "timestamp": r["timestamp"]
            }
            for r in rows
        ]


def get_recent_sessions(username: str, limit: int = 5) -> list:
    """Get the most recent chat log entries for a user profile."""
    username = username.lower().strip()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT game, message, response, timestamp
            FROM chat_logs
            WHERE username = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (username, limit)
        )
        rows = cursor.fetchall()
        # Return in chronological order
        return [
            {
                "game": r["game"],
                "message": r["message"],
                "response": r["response"],
                "timestamp": r["timestamp"]
            }
            for r in reversed(rows)
        ]


def get_leaderboard(limit: int = 10) -> list:
    """Get top users ranked by messages sent."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT username, messages_sent, sessions, favorite_game, rank_points
            FROM users
            ORDER BY messages_sent DESC, rank_points DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        return [
            {
                "username": r["username"],
                "messages_sent": r["messages_sent"],
                "sessions": r["sessions"],
                "favorite_game": r["favorite_game"],
                "rank_points": r["rank_points"]
            }
            for r in rows
        ]


def check_db_health() -> bool:
    """Verify database connection and query readiness."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return cursor.fetchone() is not None
    except Exception:
        return False
