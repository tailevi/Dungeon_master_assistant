"""Strip embedded base64 images out of lore markdown.

Rich-text / Google-Docs exports embed images inline as base64 data URIs,
which can balloon a ~40 KB lore file to multiple megabytes (e.g. a single
image is 1.2 MB of base64 text). Those blobs are useless to the text-only
assistant and would flood the model context, so we replace each with a
`(image removed)` placeholder.

Run once, or after each export:

    uv run python -m dmhelper.maintenance.clean_lore

Idempotent — re-running does nothing once the blobs are gone.
"""

from __future__ import annotations

import re
from pathlib import Path

from dmhelper.config import get_settings

_PLACEHOLDER = "(image removed)"

# A base64 image data URI. Blobs here are single-line, so no newlines inside.
_DATA_URI_RE = re.compile(r"data:image/[\w.+-]+;base64,[A-Za-z0-9+/=]+")
# The whole reference-definition line: `[label]: <data:image/...;base64,...>`
_REF_DEF_RE = re.compile(
    r"^(\[[^\]]+\]:\s*)<?\s*data:image/[\w.+-]+;base64,[A-Za-z0-9+/=]+\s*>?\s*$",
    re.MULTILINE,
)


def strip_data_uris(text: str) -> str:
    """Replace every embedded base64 image with a placeholder."""
    if "base64," not in text:
        return text
    # Collapse reference-definition lines first so the label survives.
    text = _REF_DEF_RE.sub(rf"\1{_PLACEHOLDER}", text)
    # Then any remaining inline data URIs (markdown/html img src).
    text = _DATA_URI_RE.sub(_PLACEHOLDER, text)
    return text


def clean_file(path: Path) -> int:
    """Strip a single file in place. Returns bytes saved (0 if unchanged)."""
    original = path.read_text(encoding="utf-8")
    cleaned = strip_data_uris(original)
    if cleaned == original:
        return 0
    saved = len(original.encode("utf-8")) - len(cleaned.encode("utf-8"))
    path.write_text(cleaned, encoding="utf-8")
    return saved


def clean_lore_dir(lore_dir: Path) -> dict[Path, int]:
    """Strip every .md under `lore_dir`. Returns {path: bytes_saved} for changed files."""
    results: dict[Path, int] = {}
    if not lore_dir.exists():
        return results
    for path in sorted(lore_dir.rglob("*.md")):
        saved = clean_file(path)
        if saved:
            results[path] = saved
    return results


def main() -> None:
    settings = get_settings()
    results = clean_lore_dir(settings.lore_dir)
    if not results:
        print(f"No embedded images found under {settings.lore_dir}. Nothing to do.")
        return
    total = 0
    for path, saved in results.items():
        total += saved
        print(f"  {path}: -{saved:,} bytes")
    print(f"Cleaned {len(results)} file(s), saved {total:,} bytes total.")


if __name__ == "__main__":
    main()
