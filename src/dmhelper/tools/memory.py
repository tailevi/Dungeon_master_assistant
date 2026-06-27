"""Per-group rolling memory files.

`data/memory/memory_<group>.md` is a free-form running summary written by
the book-keeper agent (later step). For now we expose read/write tools so
the orchestrator can pull current memory into context and append notes.
"""

from __future__ import annotations

import re
from pathlib import Path

from agents import function_tool

from dmhelper.config import get_settings

_SLUG_RE = re.compile(r"[^a-z0-9_-]+")


def slug(group_id: str) -> str:
    return _SLUG_RE.sub("-", group_id.lower()).strip("-") or "default"


def memory_path(group_id: str) -> Path:
    settings = get_settings()
    settings.memory_dir.mkdir(parents=True, exist_ok=True)
    return settings.memory_dir / f"memory_{slug(group_id)}.md"


def read_memory(group_id: str) -> str:
    path = memory_path(group_id)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_memory(group_id: str, summary: str) -> Path:
    path = memory_path(group_id)
    path.write_text(summary, encoding="utf-8")
    return path


@function_tool
def memory_read(group_id: str) -> str:
    """Read the rolling memory summary for a play group."""
    text = read_memory(group_id)
    return text or f"(no memory yet for group {group_id!r})"


@function_tool
def memory_write(group_id: str, summary: str) -> str:
    """Overwrite the rolling memory summary for a play group.

    Use to update the running notes about NPCs, locations, plot threads.
    The full new summary should be passed; this replaces the file.
    """
    path = write_memory(group_id, summary)
    return f"Wrote {len(summary)} chars to {path}."
