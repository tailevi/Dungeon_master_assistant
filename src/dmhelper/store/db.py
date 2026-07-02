"""Tiny local SQLite store.

Holds two things:

- `pending_changes` — per-session changeset queued by the orchestrator,
  popped on `/confirm`.
- `kanka_id_map` — `(group_id, local_key)` -> `(entity_type, kanka_id)` so
  search-before-write can short-circuit straight to an UPDATE on a
  previously created entity.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from dmhelper.config import get_settings

_LOCK = threading.Lock()


def _db_path() -> Path:
    settings = get_settings()
    settings.store_db_path.parent.mkdir(parents=True, exist_ok=True)
    return settings.store_db_path


@contextmanager
def _conn(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    target = path or _db_path()
    with _LOCK:
        conn = sqlite3.connect(target)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def init_db(path: Path | None = None) -> None:
    with _conn(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS pending_changes (
                session_id TEXT PRIMARY KEY,
                payload    TEXT NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS kanka_id_map (
                group_id    TEXT NOT NULL,
                local_key   TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                kanka_id    INTEGER NOT NULL,
                PRIMARY KEY (group_id, local_key)
            );

            CREATE TABLE IF NOT EXISTS chats (
                group_id   TEXT NOT NULL,
                chat_id    TEXT NOT NULL,
                title      TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (group_id, chat_id)
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                chat_id  TEXT NOT NULL,
                role     TEXT NOT NULL,
                content  TEXT NOT NULL,
                ts       REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_chat_messages
                ON chat_messages (group_id, chat_id, id);
            """
        )


# -- pending changeset --------------------------------------------------

def save_pending(session_id: str, payload: dict[str, Any]) -> None:
    init_db()
    import time

    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO pending_changes(session_id, payload, created_at) "
            "VALUES (?, ?, ?)",
            (session_id, json.dumps(payload), time.time()),
        )


def load_pending(session_id: str) -> dict[str, Any] | None:
    init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT payload FROM pending_changes WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    if not row:
        return None
    return json.loads(row["payload"])


def clear_pending(session_id: str) -> None:
    init_db()
    with _conn() as conn:
        conn.execute(
            "DELETE FROM pending_changes WHERE session_id = ?", (session_id,)
        )


# -- kanka id map -------------------------------------------------------

def get_kanka_id(group_id: str, local_key: str) -> tuple[str, int] | None:
    init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT entity_type, kanka_id FROM kanka_id_map "
            "WHERE group_id = ? AND local_key = ?",
            (group_id, local_key),
        ).fetchone()
    if not row:
        return None
    return row["entity_type"], int(row["kanka_id"])


def set_kanka_id(
    group_id: str, local_key: str, entity_type: str, kanka_id: int
) -> None:
    init_db()
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO kanka_id_map"
            "(group_id, local_key, entity_type, kanka_id) VALUES (?, ?, ?, ?)",
            (group_id, local_key, entity_type, kanka_id),
        )


# -- chats + display transcript ----------------------------------------
#
# The OpenAI Agents SQLiteSession (data/sessions.db) already persists the
# model context per `group:chat` and auto-resumes it. These tables add the
# UI layer: a list of chats per group and the human-readable transcript so
# the DM can reopen a past chat and see its history.

import time
import uuid


def create_chat(group_id: str, title: str = "New chat") -> str:
    init_db()
    chat_id = uuid.uuid4().hex[:12]
    now = time.time()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO chats(group_id, chat_id, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (group_id, chat_id, title, now, now),
        )
    return chat_id


def list_chats(group_id: str) -> list[dict[str, Any]]:
    """Chats for a group, most-recently-updated first."""
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT chat_id, title, updated_at FROM chats "
            "WHERE group_id = ? ORDER BY updated_at DESC",
            (group_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def rename_chat(group_id: str, chat_id: str, title: str) -> None:
    init_db()
    with _conn() as conn:
        conn.execute(
            "UPDATE chats SET title = ?, updated_at = ? "
            "WHERE group_id = ? AND chat_id = ?",
            (title, time.time(), group_id, chat_id),
        )


def delete_chat(group_id: str, chat_id: str) -> None:
    init_db()
    with _conn() as conn:
        conn.execute(
            "DELETE FROM chat_messages WHERE group_id = ? AND chat_id = ?",
            (group_id, chat_id),
        )
        conn.execute(
            "DELETE FROM chats WHERE group_id = ? AND chat_id = ?",
            (group_id, chat_id),
        )


def add_message(group_id: str, chat_id: str, role: str, content: str) -> None:
    """Append a display message and bump the chat's updated_at (creating the
    chat row if it doesn't exist yet)."""
    init_db()
    now = time.time()
    with _conn() as conn:
        exists = conn.execute(
            "SELECT 1 FROM chats WHERE group_id = ? AND chat_id = ?",
            (group_id, chat_id),
        ).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO chats(group_id, chat_id, title, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (group_id, chat_id, "New chat", now, now),
            )
        conn.execute(
            "INSERT INTO chat_messages(group_id, chat_id, role, content, ts) "
            "VALUES (?, ?, ?, ?, ?)",
            (group_id, chat_id, role, content, now),
        )
        conn.execute(
            "UPDATE chats SET updated_at = ? WHERE group_id = ? AND chat_id = ?",
            (now, group_id, chat_id),
        )


def get_messages(group_id: str, chat_id: str) -> list[dict[str, str]]:
    """Display transcript for a chat as [{role, content}, ...]."""
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages "
            "WHERE group_id = ? AND chat_id = ? ORDER BY id",
            (group_id, chat_id),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def message_count(group_id: str, chat_id: str) -> int:
    init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM chat_messages "
            "WHERE group_id = ? AND chat_id = ?",
            (group_id, chat_id),
        ).fetchone()
    return int(row["n"]) if row else 0
