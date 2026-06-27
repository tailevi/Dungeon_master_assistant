"""Local lore tools.

Two distinct corpora under `data/lore/`:

- `data/lore/alaxya/`        -> the homebrew WORLD of Alaxya (Deities,
                                History, Geography, the Seven Espada, ...).
                                Searched by `lore_search`.
- `data/lore/player groups/` -> one markdown file per play group holding
                                that group's backstory / players / info.
                                Read by `group_lore_search`, keyed on the
                                group name.

Both folders are globbed recursively, so new `.md` files added later are
picked up automatically — no code change needed.

Whole documents are returned (no embeddings, no chunking, no RAG).

This module also exposes write-back helpers used by the Kanka `/confirm`
flow so that, once new canon is saved to Kanka, the same content is
persisted back into these folders (keeping the markdown the source of
truth that eventually fully populates the Kanka site).
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

import frontmatter
from agents import function_tool

from dmhelper.config import get_settings


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9]+")
# trailing "players" with any leading spaces/underscores, e.g. "Noir_ Players"
_GROUP_SUFFIX_RE = re.compile(r"[ _]*players\s*$", re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _norm(text: str) -> str:
    return " ".join(_tokens(text))


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "entry"


@dataclass(slots=True)
class LoreDoc:
    path: Path
    title: str
    category: str | None
    body: str

    def to_text(self) -> str:
        header = f"# {self.title}"
        if self.category:
            header += f"  _(category: {self.category})_"
        return f"{header}\n\n{self.body.strip()}\n"


def _slug_title(path: Path, meta: dict[str, object]) -> str:
    raw = meta.get("title")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return path.stem.replace("-", " ").replace("_", " ").title()


def _load_dir(lore_dir: Path) -> list[LoreDoc]:
    if not lore_dir.exists():
        return []
    docs: list[LoreDoc] = []
    for path in sorted(lore_dir.rglob("*.md")):
        post = frontmatter.load(path)
        category = post.metadata.get("category")
        docs.append(
            LoreDoc(
                path=path,
                title=_slug_title(path, post.metadata),
                category=str(category) if category else None,
                body=post.content or "",
            )
        )
    return docs


def _score(doc: LoreDoc, query_tokens: list[str]) -> int:
    if not query_tokens:
        return 0
    hay = " ".join([doc.title, doc.category or "", doc.body]).lower()
    return sum(hay.count(tok) for tok in query_tokens)


# --------------------------------------------------------------------------
# Alaxya world lore  ->  lore_search
# --------------------------------------------------------------------------


@function_tool
def lore_search(query: str, category: str | None = None) -> str:
    """Search the homebrew WORLD-OF-ALAXYA lore (markdown files under
    `data/lore/alaxya/`).

    Returns the full text of the top-matching documents. Use this for any
    question about Alaxya itself — deities, history, the Seven Espada,
    geography, factions. Do NOT use this for play-group backstories (use
    `group_lore_search`) or for Exandria / Critical Role (use `web_search`).

    Args:
        query: free-text question or keywords.
        category: optional filter against a file's frontmatter `category`
            field (e.g. "Deities", "History", "Seven Espada", "Geography").
    """
    settings = get_settings()
    docs = _load_dir(settings.alexya_lore_dir)
    if category:
        docs = [
            d
            for d in docs
            if d.category and d.category.lower() == category.lower()
        ]
    if not docs:
        return (
            "No Alaxya lore files found under data/lore/alaxya/. "
            "Add .md files there."
        )

    tokens = _tokens(query)
    scored = sorted(
        ((_score(d, tokens), d) for d in docs),
        key=lambda pair: pair[0],
        reverse=True,
    )
    top = [d for score, d in scored if score > 0][:3]
    if not top:
        return f"No Alaxya lore matched: {query!r}."

    return "\n\n---\n\n".join(d.to_text() for d in top)


# --------------------------------------------------------------------------
# Player-group lore  ->  group_lore_search
# --------------------------------------------------------------------------


def group_display_name(path: Path) -> str:
    """`Noir_ Players.md` -> `Noir`; `The Wolf Pack_ Players.md` -> `The Wolf Pack`."""
    name = _GROUP_SUFFIX_RE.sub("", path.stem).replace("_", " ").strip()
    return name or path.stem


def list_group_files() -> list[Path]:
    settings = get_settings()
    if not settings.group_lore_dir.exists():
        return []
    return sorted(settings.group_lore_dir.rglob("*.md"))


def list_player_groups() -> list[str]:
    """Distinct group display names derived from the player-groups folder."""
    seen: dict[str, str] = {}
    for p in list_group_files():
        name = group_display_name(p)
        seen.setdefault(_norm(name), name)
    return sorted(seen.values())


def find_group_file(group_name: str) -> Path | None:
    """Resolve a group name to its backstory file. Tolerant of casing,
    underscores, and the `_ Players` suffix."""
    target = _norm(group_name)
    if not target:
        return None
    files = list_group_files()

    # 1. exact normalised display-name match
    for p in files:
        if _norm(group_display_name(p)) == target:
            return p
    # 2. substring either direction
    for p in files:
        dn = _norm(group_display_name(p))
        if dn and (target in dn or dn in target):
            return p
    # 3. token overlap, best wins
    target_tokens = set(target.split())
    best: tuple[int, Path] | None = None
    for p in files:
        overlap = len(target_tokens & set(_norm(group_display_name(p)).split()))
        if overlap and (best is None or overlap > best[0]):
            best = (overlap, p)
    return best[1] if best else None


@function_tool
def group_lore_search(group_name: str, query: str | None = None) -> str:
    """Read a PLAY GROUP's backstory / players / info from
    `data/lore/player groups/`.

    Each group has its own markdown file (e.g. `Noir_ Players.md`). This
    returns that group's whole document so you have full background when
    answering questions about the group, its characters, or its arc.

    Args:
        group_name: the play group's name (e.g. "Noir", "The Wolf Pack").
        query: optional — currently informational only; the whole group
            document is returned regardless so nothing is missed.
    """
    path = find_group_file(group_name)
    if path is None:
        available = list_player_groups()
        hint = (
            f" Available groups: {', '.join(available)}."
            if available
            else " No player-group files found yet."
        )
        return f"No player-group file matched {group_name!r}.{hint}"

    post = frontmatter.load(path)
    body = (post.content or "").strip()
    return (
        f"# {group_display_name(path)} — group file `{path.name}`\n\n"
        f"{body}\n"
    )


# --------------------------------------------------------------------------
# Write-back helpers (used by the Kanka /confirm flow)
# --------------------------------------------------------------------------


def write_alexya_entry(
    name: str, body: str, category: str | None = None
) -> Path:
    """Create/overwrite a single Alaxya world-lore file for `name`.

    One file per entity keeps the corpus easy to push to Kanka later and
    lets new files accrue over time.
    """
    settings = get_settings()
    settings.alexya_lore_dir.mkdir(parents=True, exist_ok=True)
    path = settings.alexya_lore_dir / f"{_slugify(name)}.md"

    metadata: dict[str, object] = {"title": name, "world": "Alaxya"}
    if category:
        metadata["category"] = category
    post = frontmatter.Post(body or "", **metadata)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return path


def append_group_entry(group_name: str, name: str, body: str) -> Path:
    """Append a named canon section to a group's backstory file, creating
    the file if the group has none yet."""
    settings = get_settings()
    path = find_group_file(group_name)
    if path is None:
        settings.group_lore_dir.mkdir(parents=True, exist_ok=True)
        path = settings.group_lore_dir / f"{group_name}_ Players.md"
        path.write_text(f"# {group_name} — Players\n", encoding="utf-8")

    stamp = dt.datetime.now().isoformat(timespec="seconds")
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    block = f"\n\n## {name}\n_(added via assistant {stamp})_\n\n{body.strip()}\n"
    path.write_text(existing.rstrip() + block, encoding="utf-8")
    return path
