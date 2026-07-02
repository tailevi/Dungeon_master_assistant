"""Local lore tools.

Everything under `data/lore/` is local homebrew canon:

- `data/lore/alaxya/`        -> the homebrew WORLD of Alaxya (Deities,
                                History, Geography, the Seven Espada, world
                                events such as the planned invasion of
                                Exandria, ...).
- `data/lore/player groups/` -> one markdown file per play group holding
                                that group's backstory / players / info.

`lore_search` searches the WHOLE `data/lore` tree (world lore + every group
file) so world events, locations, creatures, deities, and cross-world plot
threads always surface regardless of which group is active. It returns the
most relevant markdown SECTIONS (split by heading) with file + heading
citations, ranked by keyword overlap and capped in size — this keeps huge
files (e.g. a multi-megabyte Deities.md) usable without dumping them whole.

`group_lore_search` still returns a single group's WHOLE backstory document.

No embeddings, no vector DB — plain keyword ranking over headings/sections.

This module also exposes write-back helpers used by the Kanka `/confirm`
flow so that, once new canon is saved to Kanka, the same content is
persisted back into these folders.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

import frontmatter
from agents import function_tool

from dmhelper.config import get_settings
from dmhelper.maintenance.clean_lore import strip_data_uris


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9]+")
# trailing "players" with any leading spaces/underscores, e.g. "Noir_ Players"
_GROUP_SUFFIX_RE = re.compile(r"[ _]*players\s*$", re.IGNORECASE)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$", re.MULTILINE)

# Output budget so a single search never floods the model context.
_MAX_SECTIONS = 8
_MAX_SECTION_CHARS = 2800
_MAX_TOTAL_CHARS = 16000


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _norm(text: str) -> str:
    return " ".join(_tokens(text))


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "entry"


def _slug_title(path: Path, meta: dict[str, object]) -> str:
    raw = meta.get("title")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return path.stem.replace("-", " ").replace("_", " ").title()


@dataclass(slots=True)
class LoreSection:
    path: Path
    title: str
    category: str | None
    heading: str
    body: str

    def citation(self) -> str:
        loc = f"{self.path.name}"
        if self.heading and self.heading != self.title:
            loc += f" > {self.heading}"
        if self.category:
            loc += f" [{self.category}]"
        return loc

    def to_text(self) -> str:
        body = self.body.strip()
        if len(body) > _MAX_SECTION_CHARS:
            body = body[:_MAX_SECTION_CHARS].rstrip() + " …(truncated)"
        return f"### {self.citation()}\n\n{body}"


def _split_sections(
    path: Path, title: str, category: str | None, text: str
) -> list[LoreSection]:
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [LoreSection(path, title, category, title, text)]

    sections: list[LoreSection] = []
    pre = text[: matches[0].start()].strip()
    if pre:
        sections.append(LoreSection(path, title, category, title, pre))
    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append(
                LoreSection(path, title, category, heading, body)
            )
    return sections


# Parsed-section cache keyed by path -> (mtime, size, sections). Avoids
# re-reading/re-splitting large files on every search within a session.
_SECTION_CACHE: dict[Path, tuple[float, int, list[LoreSection]]] = {}


def _sections_for_file(path: Path) -> list[LoreSection]:
    stat = path.stat()
    cached = _SECTION_CACHE.get(path)
    if cached and cached[0] == stat.st_mtime and cached[1] == stat.st_size:
        return cached[2]

    post = frontmatter.load(path)
    category = post.metadata.get("category")
    # Defensive: strip embedded base64 images so an un-cleaned export never
    # bloats scoring or the returned context.
    content = strip_data_uris(post.content or "")
    sections = _split_sections(
        path,
        _slug_title(path, post.metadata),
        str(category) if category else None,
        content,
    )
    _SECTION_CACHE[path] = (stat.st_mtime, stat.st_size, sections)
    return sections


def _load_sections(lore_dir: Path) -> list[LoreSection]:
    if not lore_dir.exists():
        return []
    out: list[LoreSection] = []
    for path in sorted(lore_dir.rglob("*.md")):
        out.extend(_sections_for_file(path))
    return out


def _score_section(section: LoreSection, query_tokens: list[str]) -> int:
    if not query_tokens:
        return 0
    hay = " ".join(
        [section.title, section.heading, section.category or "", section.body]
    ).lower()
    # weight heading/title hits higher than body mentions
    head = " ".join([section.title, section.heading]).lower()
    score = 0
    for tok in query_tokens:
        score += hay.count(tok)
        score += 3 * head.count(tok)
    return score


# --------------------------------------------------------------------------
# Whole-tree lore search  ->  lore_search
# --------------------------------------------------------------------------


def lore_search_impl(query: str, category: str | None = None) -> str:
    """Plain-function form of lore_search (used by tests + the tool)."""
    settings = get_settings()
    sections = _load_sections(settings.lore_dir)
    if category:
        sections = [
            s
            for s in sections
            if s.category and s.category.lower() == category.lower()
        ]
    if not sections:
        return (
            "No lore files found under data/lore/. Add .md files under "
            "data/lore/alaxya/ or data/lore/player groups/."
        )

    tokens = _tokens(query)
    scored = sorted(
        ((_score_section(s, tokens), s) for s in sections),
        key=lambda pair: pair[0],
        reverse=True,
    )
    top = [s for score, s in scored if score > 0][:_MAX_SECTIONS]
    if not top:
        return (
            f"No lore section matched {query!r}. The lore files exist but "
            "none contained these keywords — try different terms."
        )

    out: list[str] = []
    total = 0
    for section in top:
        block = section.to_text()
        if total + len(block) > _MAX_TOTAL_CHARS and out:
            break
        out.append(block)
        total += len(block)
    return "\n\n---\n\n".join(out)


@function_tool
def lore_search(query: str, category: str | None = None) -> str:
    """Search ALL local homebrew lore under `data/lore/` — the world of
    Alaxya (deities, history, geography, the Seven Espada, world events such
    as the planned invasion of Exandria) AND every play-group file.

    Always use this for questions about world events, locations, creatures,
    deities, factions, and cross-world plot — even for an Exandria-set group,
    because Alaxya canon can reach into Exandria. Returns the most relevant
    markdown sections with `file > heading` citations. If nothing matches,
    it says so explicitly (it does NOT mean the folder is empty).

    Args:
        query: free-text question or keywords.
        category: optional filter against a file's frontmatter `category`
            field (e.g. "Deities", "History", "Seven Espada", "Geography").
    """
    return lore_search_impl(query, category)


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
