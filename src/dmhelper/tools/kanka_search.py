"""kanka_player_search function tool.

Mayan's groups are tracked in Kanka as quests (one quest per group). This
tool searches Kanka broadly, not just one quest:

  1. resolve the group name to a quest and pull its journals + linked
     `quest_elements` (the group's own play history),
  2. run a CAMPAIGN-WIDE entity search for each meaningful keyword in the
     query (characters, NPCs, locations, organisations, notes, journals).
     Kanka's search endpoint is campaign-scoped, so this automatically
     covers entities that belong to the OTHER play groups too — matching the
     rule "if it isn't in this group, look across the whole campaign".

Returns a combined text summary. It only reports "nothing found" after BOTH
the group walk and the campaign-wide search come back empty.
"""

from __future__ import annotations

import re

from agents import function_tool

from dmhelper.clients.kanka import KankaClient
from dmhelper.config import get_settings

_TAG_RE = re.compile(r"<[^>]+>")

# generic words we never want to fire a Kanka name-search on
_STOPWORDS = {
    "session", "sessions", "combat", "the", "and", "for", "with", "they",
    "them", "their", "this", "that", "from", "into", "about", "some",
    "will", "have", "had", "was", "were", "are", "our", "out", "who",
    "what", "when", "where", "which", "long", "rest", "player", "players",
    "group", "party", "twin", "elf", "info", "information", "everything",
    "post", "pre", "npc", "npcs", "page", "pages", "thing", "things",
}


def _strip_html(s: str | None) -> str:
    if not s:
        return ""
    return _TAG_RE.sub(" ", s).strip()


def _query_tokens(query: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", query.lower()) if t]


def _matches(haystack: str, tokens: list[str]) -> bool:
    if not tokens:
        return True
    hay = haystack.lower()
    return any(tok in hay for tok in tokens)


def _keywords(query: str, limit: int = 8) -> list[str]:
    """Extract meaningful name-like keywords to search Kanka for.

    Keeps original casing, drops stopwords and short tokens, dedupes.
    """
    out: list[str] = []
    seen: set[str] = set()
    for raw in re.findall(r"[A-Za-z][A-Za-z0-9'\-]+", query):
        low = raw.lower()
        if len(low) < 4 or low in _STOPWORDS or low in seen:
            continue
        seen.add(low)
        out.append(raw)
        if len(out) >= limit:
            break
    return out


async def _find_group_quest(client: KankaClient, group_name: str) -> dict | None:
    quests = await client.list("quests")
    needle = group_name.strip().lower()
    for q in quests:
        if q.get("name", "").strip().lower() == needle:
            return q
    for q in quests:
        if needle and needle in q.get("name", "").strip().lower():
            return q
    return None


async def _group_section(
    client: KankaClient, group_name: str, tokens: list[str]
) -> list[str]:
    quest = await _find_group_quest(client, group_name)
    if not quest:
        return [
            f"_No Kanka quest matched group {group_name!r} "
            f"(searched campaign-wide instead)._"
        ]

    lines = [f"# Group quest: {quest.get('name')} (id={quest.get('id')})"]
    summary = _strip_html(quest.get("entry"))
    if summary:
        lines.append(summary[:600])

    journals = await client.list(
        "journals", params={"quest_id": quest.get("id")}
    )
    matched = [
        j
        for j in journals
        if _matches(f"{j.get('name', '')} {_strip_html(j.get('entry'))}", tokens)
    ] or journals  # if no keyword hit, still show the group's journals
    if matched:
        lines.append(f"\n## Group journals ({len(matched)})")
        for j in matched[:8]:
            body = _strip_html(j.get("entry"))[:400]
            lines.append(f"- **{j.get('name')}** (id={j.get('id')}): {body}")

    try:
        elements = await client.quest_elements(quest["id"])
    except Exception:
        elements = []
    el_matched = [
        e
        for e in elements
        if _matches(
            f"{e.get('name', '')} {_strip_html(e.get('description'))}", tokens
        )
    ]
    if el_matched:
        lines.append(f"\n## Linked entities ({len(el_matched)})")
        for e in el_matched[:10]:
            lines.append(
                f"- {e.get('name')} "
                f"(entity_id={e.get('entity_id')}, role={e.get('role')})"
            )
    return lines


async def _campaign_search(
    client: KankaClient, keywords: list[str]
) -> list[str]:
    seen: set[tuple[str, object]] = set()
    hits: list[str] = []
    for kw in keywords:
        try:
            results = await client.search(kw)
        except Exception:
            continue
        for r in results:
            key = (str(r.get("type")), r.get("id"))
            if key in seen:
                continue
            seen.add(key)
            name = r.get("name")
            etype = r.get("type")
            eid = r.get("entity_id") or r.get("id")
            hits.append(f"- **{name}** ({etype}, entity_id={eid}) — via {kw!r}")
    if not hits:
        return []
    return [f"# Campaign-wide matches ({len(hits)})", *hits]


async def kanka_player_search_impl(group_name: str, query: str) -> str:
    """Plain-coroutine form of kanka_player_search (used by tests + tool)."""
    settings = get_settings()
    tokens = _query_tokens(query)
    keywords = _keywords(query)

    async with KankaClient(
        token=settings.kanka_api_token.get_secret_value(),
        campaign_id=settings.kanka_campaign_id,
    ) as client:
        group_lines = await _group_section(client, group_name, tokens)
        search_lines = await _campaign_search(client, keywords)

    blocks = ["\n".join(group_lines)]
    if search_lines:
        blocks.append("\n".join(search_lines))
    else:
        blocks.append(
            "# Campaign-wide matches\n"
            f"_No Kanka entity matched keywords {keywords!r} across the "
            "whole campaign._"
        )
    return "\n\n".join(blocks)


@function_tool
async def kanka_player_search(group_name: str, query: str) -> str:
    """Search Kanka for information relevant to a play group and query.

    Does BOTH:
      1. walks the group's quest (journals + linked entities), and
      2. runs a campaign-wide search for each name/keyword in `query`,
         which also covers entities owned by the other play groups.

    Use this for any question about play history, NPCs, locations, or events
    that might be recorded in Kanka. Only trust a "nothing found" result
    after this has run.

    Args:
        group_name: the play group's name (matches a Kanka quest name).
        query: free text; names/keywords are extracted for the campaign search.
    """
    return await kanka_player_search_impl(group_name, query)
