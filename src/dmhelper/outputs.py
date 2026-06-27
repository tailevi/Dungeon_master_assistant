"""Detect and save HTML artifacts (session documents, feats) the Writer
produces, into the outputs folder.

The session-document template tells Claude to emit a complete standalone
HTML file. When the Writer's answer is such a document, we persist it to
`outputs/` and derive the filename from its <title> per the template's
`Session_[NUMBER]_[TITLE].html` convention.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from dmhelper.config import get_settings

_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def looks_like_html_document(text: str) -> bool:
    head = text.lstrip()[:200].lower()
    return head.startswith("<!doctype html") or head.startswith("<html")


def _filename_from_html(text: str) -> str:
    m = _TITLE_RE.search(text)
    title = m.group(1).strip() if m else ""
    # "Session 5: The Mine" -> "Session_5_The_Mine"
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")
    if not slug:
        slug = "Session_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{slug}.html"


def save_html_output(text: str) -> Path:
    """Write an HTML document to the outputs folder; return its path."""
    settings = get_settings()
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    path = settings.outputs_dir / _filename_from_html(text)
    path.write_text(text, encoding="utf-8")
    return path


def maybe_emit_html(text: str) -> tuple[str, Path | None]:
    """If `text` is a full HTML document, save it and return a chat-friendly
    message plus the path. Otherwise return the text unchanged and None."""
    if not looks_like_html_document(text):
        return text, None
    path = save_html_output(text)
    note = (
        f"Saved session document to `{path}`.\n\n"
        f"<details><summary>HTML source</summary>\n\n"
        f"```html\n{text}\n```\n\n</details>"
    )
    return note, path
