"""kanka_player_search function tool.

Mayan's groups are tracked in Kanka as quests (one quest per group). The
quest's attached `quest_elements` link to characters, locations, and
journal entries owned by that group. This tool:

  1. resolves the group name to a quest,
  2. pulls the quest's journals (session recaps),
  3. searches those journal entries + linked entities for the user query,
  4. returns a compact text summary the orchestrator can read.
"""

from __future__ import annotations

import re

from agents import function_tool

from dmhelper.clients.kanka import KankaClient
from dmhelper.config import get_settings

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(s: str | None) -> str:
    if not s:
        return ""
    return _TAG_RE.sub(" ", s).strip()


def _matches(haystack: str, query: str) -> bool:
    if not query.strip():
        return True
    tokens = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if t]
    if not tokens:
        return True
    hay = haystack.lower()
    return any(tok in hay for tok in tokens)


async def _find_group_quest(
    client: KankaClient, group_name: str
) -> dict | None:
    quests = await client.list("quests")
    needle = group_name.strip().lower()
    for q in quests:
        if q.get("name", "").strip().lower() == needle:
            return q
    for q in quests:
        if needle in q.get("name", "").strip().lower():
            return q
    return None


@function_tool
async def kanka_player_search(group_name: str, query: str) -> str:
    """Search a play group's Kanka data for information matching `query`.

    Walks: quests -> find quest whose name is `group_name` -> pull its
    journals + linked entities -> return entries that match `query`.

    Args:
        group_name: the play group's name (matches a Kanka quest name).
        query: free-text to match against journal/entity names and entries.
    """
    settings = get_settings()
    async with KankaClient(
        token=settings.kanka_api_token.get_secret_value(),
        campaign_id=settings.kanka_campaign_id,
    ) as client:
        quest = await _find_group_quest(client, group_name)
        if not quest:
            return f"No Kanka quest found for group {group_name!r}."

        lines: list[str] = [
            f"# Group: {quest.get('name')} (quest id={quest.get('id')})"
        ]
        summary = _strip_html(quest.get("entry"))
        if summary:
            lines.append(summary[:600])

        journals = await client.list(
            "journals", params={"quest_id": quest.get("id")}
        )
        matched_journals = [
            j
            for j in journals
            if _matches(
                f"{j.get('name', '')} {_strip_html(j.get('entry'))}", query
            )
        ]
        if matched_journals:
            lines.append(f"\n## Matching journals ({len(matched_journals)})")
            for j in matched_journals[:8]:
                body = _strip_html(j.get("entry"))[:400]
                lines.append(
                    f"- **{j.get('name')}** (id={j.get('id')}): {body}"
                )

        try:
            elements = await client.quest_elements(quest["id"])
        except Exception:
            elements = []
        matched_elements = [
            e
            for e in elements
            if _matches(
                f"{e.get('name', '')} {_strip_html(e.get('description'))}",
                query,
            )
        ]
        if matched_elements:
            lines.append(
                f"\n## Linked entities matching query ({len(matched_elements)})"
            )
            for e in matched_elements[:10]:
                lines.append(
                    f"- {e.get('name')} "
                    f"(entity_id={e.get('entity_id')}, role={e.get('role')})"
                )

        if len(lines) == 1:
            return f"No matches for {query!r} in group {quest.get('name')!r}."
        return "\n".join(lines)
