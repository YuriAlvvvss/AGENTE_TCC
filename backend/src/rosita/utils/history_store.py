"""Persistência do histórico de conversas em SQLite, indexado por usuário.

Cada usuário (admin/usuario/...) possui sua própria conversa, que sobrevive a
reinicializações do servidor. O acesso é serializado por um lock e usa uma
conexão por operação, evitando problemas de concorrência entre threads
(gunicorn gthread).
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Optional


class HistoryStore:
    """Armazena e recupera mensagens de chat por usuário."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = str(db_path)
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._lock, self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_username ON messages(username, id)"
            )

    def append(self, username: str, role: str, content: str) -> None:
        """Acrescenta uma mensagem ao histórico do usuário."""
        if not username:
            return
        with self._lock, self._connect() as con:
            con.execute(
                "INSERT INTO messages (username, role, content) VALUES (?, ?, ?)",
                (username, role, content),
            )

    def get(self, username: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Retorna as mensagens do usuário em ordem cronológica.

        Se ``limit`` for informado, retorna apenas as ``limit`` mais recentes
        (ainda em ordem cronológica).
        """
        if not username:
            return []
        with self._lock, self._connect() as con:
            if limit and limit > 0:
                rows = con.execute(
                    "SELECT role, content FROM messages WHERE username = ? "
                    "ORDER BY id DESC LIMIT ?",
                    (username, limit),
                ).fetchall()
                rows = list(reversed(rows))
            else:
                rows = con.execute(
                    "SELECT role, content FROM messages WHERE username = ? ORDER BY id ASC",
                    (username,),
                ).fetchall()
        return [{"role": role, "content": content} for role, content in rows]

    def clear(self, username: str) -> None:
        """Remove todo o histórico do usuário."""
        if not username:
            return
        with self._lock, self._connect() as con:
            con.execute("DELETE FROM messages WHERE username = ?", (username,))
