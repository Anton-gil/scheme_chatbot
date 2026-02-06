import sqlite3
from datetime import datetime
from pathlib import Path
import uuid

DB_PATH = Path(__file__).parent / "chat_history.db"


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT DEFAULT 'New Chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()


def create_session(title: str = "New Chat") -> str:
    """Create a new chat session."""
    conn = get_connection()
    session_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO sessions (id, title) VALUES (?, ?)",
        (session_id, title)
    )
    conn.commit()
    conn.close()
    return session_id


def get_all_sessions():
    """Get all chat sessions."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, title, created_at FROM sessions ORDER BY created_at DESC"
    )
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sessions


def get_session_messages(session_id: str):
    """Get all messages for a session."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,)
    )
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages


def add_message(session_id: str, role: str, content: str):
    """Add a message to a session."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()


def update_session_title(session_id: str, title: str):
    """Update session title."""
    conn = get_connection()
    conn.execute(
        "UPDATE sessions SET title = ? WHERE id = ?",
        (title, session_id)
    )
    conn.commit()
    conn.close()


def delete_session(session_id: str):
    """Delete a session and its messages."""
    conn = get_connection()
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


# Initialize database on import
init_db()
