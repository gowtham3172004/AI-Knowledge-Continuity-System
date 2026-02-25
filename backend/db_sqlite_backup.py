"""
Database module - SQLite for user data, documents, and knowledge gaps.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.db")


def get_db_path() -> str:
    return DB_PATH


@contextmanager
def get_db():
    """Get a database connection with auto-commit/rollback."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database tables."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'developer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                knowledge_type TEXT DEFAULT 'explicit',
                chunk_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'processing',
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS knowledge_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                severity TEXT NOT NULL,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved INTEGER DEFAULT 0,
                resolved_by INTEGER,
                resolved_at TIMESTAMP,
                FOREIGN KEY (resolved_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS onboarding_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                status TEXT DEFAULT 'not_started',
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT 'New Conversation',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                response_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);
            CREATE INDEX IF NOT EXISTS idx_gaps_resolved ON knowledge_gaps(resolved);
            CREATE INDEX IF NOT EXISTS idx_onboarding_user ON onboarding_progress(user_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
        """)


# --- User Operations ---

def create_user(email: str, password_hash: str, full_name: str, role: str = "developer") -> int:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (email, password_hash, full_name, role),
        )
        return cursor.lastrowid


def get_user_by_email(email: str) -> Optional[Dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def update_last_login(user_id: int):
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), user_id),
        )


# --- Document Operations ---

def add_document(user_id: int, filename: str, original_name: str,
                 file_type: str, file_size: int, knowledge_type: str = "explicit") -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO documents (user_id, filename, original_name, file_type, file_size, knowledge_type)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, filename, original_name, file_type, file_size, knowledge_type),
        )
        return cursor.lastrowid


def update_document_status(doc_id: int, status: str, chunk_count: int = 0,
                           knowledge_type: str = None):
    with get_db() as conn:
        if knowledge_type:
            conn.execute(
                "UPDATE documents SET status = ?, chunk_count = ?, knowledge_type = ? WHERE id = ?",
                (status, chunk_count, knowledge_type, doc_id),
            )
        else:
            conn.execute(
                "UPDATE documents SET status = ?, chunk_count = ? WHERE id = ?",
                (status, chunk_count, doc_id),
            )


def get_user_documents(user_id: int) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_documents() -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT d.*, u.full_name as uploader_name 
               FROM documents d JOIN users u ON d.user_id = u.id 
               ORDER BY d.uploaded_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]


def delete_document(doc_id: int, user_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM documents WHERE id = ? AND user_id = ?", (doc_id, user_id)
        )
        return cursor.rowcount > 0


def get_document_stats() -> Dict:
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM documents WHERE status = 'indexed'").fetchone()[0]
        by_type = conn.execute(
            "SELECT knowledge_type, COUNT(*) as cnt FROM documents WHERE status = 'indexed' GROUP BY knowledge_type"
        ).fetchall()
        total_chunks = conn.execute(
            "SELECT COALESCE(SUM(chunk_count), 0) FROM documents WHERE status = 'indexed'"
        ).fetchone()[0]
        return {
            "total_documents": total,
            "total_chunks": total_chunks,
            "by_type": {r["knowledge_type"]: r["cnt"] for r in by_type},
        }


# --- Knowledge Gap Operations ---

def log_knowledge_gap(query: str, confidence_score: float, severity: str) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO knowledge_gaps (query, confidence_score, severity) VALUES (?, ?, ?)",
            (query, confidence_score, severity),
        )
        return cursor.lastrowid


def get_knowledge_gaps(resolved: bool = False, limit: int = 50) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM knowledge_gaps WHERE resolved = ? ORDER BY detected_at DESC LIMIT ?",
            (1 if resolved else 0, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def resolve_knowledge_gap(gap_id: int, user_id: int):
    with get_db() as conn:
        conn.execute(
            "UPDATE knowledge_gaps SET resolved = 1, resolved_by = ?, resolved_at = ? WHERE id = ?",
            (user_id, datetime.utcnow().isoformat(), gap_id),
        )


def get_gap_stats() -> Dict:
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM knowledge_gaps").fetchone()[0]
        unresolved = conn.execute("SELECT COUNT(*) FROM knowledge_gaps WHERE resolved = 0").fetchone()[0]
        by_severity = conn.execute(
            "SELECT severity, COUNT(*) as cnt FROM knowledge_gaps WHERE resolved = 0 GROUP BY severity"
        ).fetchall()
        return {
            "total_gaps": total,
            "unresolved": unresolved,
            "resolved": total - unresolved,
            "by_severity": {r["severity"]: r["cnt"] for r in by_severity},
        }


# --- Conversation Operations ---

def create_conversation(conversation_id: str, user_id: int, title: str = "New Conversation") -> str:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
            (conversation_id, user_id, title),
        )
    return conversation_id


def get_user_conversations(user_id: int) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT c.*, 
                      (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as message_count
               FROM conversations c
               WHERE c.user_id = ?
               ORDER BY c.updated_at DESC""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_conversation(conversation_id: str, user_id: int) -> Optional[Dict]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def update_conversation(conversation_id: str, user_id: int, title: Optional[str] = None):
    with get_db() as conn:
        if title:
            conn.execute(
                "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                (title, conversation_id, user_id),
            )
        else:
            conn.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                (conversation_id, user_id),
            )


def delete_conversation(conversation_id: str, user_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user_id),
        )
        return cursor.rowcount > 0


# --- Message Operations ---

def add_message(message_id: str, conversation_id: str, role: str, content: str, response_data: Optional[str] = None):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, response_data) VALUES (?, ?, ?, ?, ?)",
            (message_id, conversation_id, role, content, response_data),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,),
        )


def get_conversation_messages(conversation_id: str) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
        return [dict(r) for r in rows]
