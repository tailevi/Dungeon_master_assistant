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
