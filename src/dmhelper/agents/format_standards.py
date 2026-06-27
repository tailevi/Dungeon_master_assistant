"""Loader for global output-format specs under `data/instructions/`.

These are Mayan's locked specs for specific artifacts — e.g. the dark-themed
HTML session-document template (`Session_Tempalte.md`) and the custom-feat
output format. They apply to every group.

All specs are CONDITIONAL: apply them only when producing the relevant
artifact, not to ordinary questions, lore lookups, or conversation. The same
block is given to the Writer (to comply) and the Instructor (to enforce).
New `.md` files dropped into the folder are picked up automatically.

Per-group context is no longer kept here. The Instructor instead reads the
group's rolling memory file (`data/memory/memory_<group>.md`), maintained by
the book keeper, to check drafts against established canon.
"""

from __future__ import annotations

from dmhelper.config import get_settings

_HEADER = """\
## Output-format standards (CONDITIONAL — apply only when relevant)

The standards below define how to format specific artifacts: session
documents and custom feats. Apply a standard ONLY when Mayan is asking for
that artifact (e.g. "create session 5", "write up the session", "make a
feat"). For ordinary questions, lore lookups, planning, and conversation,
IGNORE these standards and respond normally — do not wrap normal answers in
HTML, and do not penalise a normal answer for not following them.

When producing a session document or feat, output a COMPLETE standalone
HTML document beginning with `<!DOCTYPE html>` exactly as the template
specifies; it will be saved to the outputs folder automatically.
"""


def load_format_standards() -> str:
    """Concatenate all format-standard files, or "" if none exist."""
    folder = get_settings().instructions_dir
    if not folder.exists():
        return ""

    blocks: list[str] = []
    for path in sorted(folder.rglob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            blocks.append(f"### From `{path.name}`\n\n{text}")

    if not blocks:
        return ""
    return _HEADER + "\n\n" + "\n\n---\n\n".join(blocks)
