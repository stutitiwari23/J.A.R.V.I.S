import sqlite3
import os
import tempfile
from pathlib import Path

# In serverless environments (e.g. Vercel, AWS Lambda), the local filesystem is read-only
# except for the /tmp directory. Route SQLite to tempdir when running on Vercel.
if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    DB_PATH = Path(tempfile.gettempdir()) / "memory.db"
else:
    DB_PATH = Path("memory.db")

class Memory:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def set(self, key: str, value: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (key.strip().lower(), value.strip())
            )
            conn.commit()

    def get(self, key: str) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM preferences WHERE key = ?", (key.strip().lower(),))
            row = cursor.fetchone()
            return row[0] if row else None

    def list_all(self) -> dict[str, str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM preferences")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def find_relevant(self, text: str) -> list[str]:
        """Find stored preferences matching words in the user query."""
        all_prefs = self.list_all()
        matches = []
        text_lower = text.lower()
        for k, v in all_prefs.items():
            if k in text_lower or any(word in text_lower for word in k.split('_')):
                matches.append(f"{k}: {v}")
        return matches

    def add_history(self, role: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO conversation_history (role, content) VALUES (?, ?)",
                (role, content)
            )
            conn.commit()

    def get_recent_history(self, limit: int = 10) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM conversation_history ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def add_search(self, query: str):
        query = query.strip()
        if not query:
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO search_history (query) VALUES (?)",
                (query,)
            )
            conn.commit()

    def get_search_history(self, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, query, strftime('%Y-%m-%d %H:%M:%S', timestamp) FROM search_history ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [{"id": r[0], "query": r[1], "timestamp": r[2]} for r in rows]

    def delete_search(self, item_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM search_history WHERE id = ?", (int(item_id),))
            conn.commit()

    def clear_search_history(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM search_history")
            conn.commit()

memory = Memory()
