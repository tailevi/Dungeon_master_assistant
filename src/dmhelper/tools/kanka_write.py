"""Kanka book-keeper.

Two surfaces:

- `propose_changeset` (a `function_tool`): the orchestrator calls this when
  Mayan asks to remember new canon. It validates the payload and queues
  it in the local `pending_changes` table. **It does not call Kanka.** It
  returns instructions telling Mayan to reply `/confirm` to save.

- `apply_pending` (plain async coroutine, *not* a tool): invoked from
  `orchestrator.run_turn` when the user message is `/confirm`. It loads
  the pending changeset, performs **search-before-write** per item to
  avoid duplicates, creates or updates each entity through `KankaClient`,
  records the resulting Kanka id in `kanka_id_map`, clears the pending
  row, and appends a one-line audit entry to `memory_<group>.md`.

Search-before-write order per item:
  1. If `local_key` already has a `kanka_id_map` row -> UPDATE that id.
  2. Else search by exact (case-insensitive) name; if found -> UPDATE.
  3. Else CREATE.
"""

from __future__ import annotations

import datetime as dt
import json
from typing import Literal, Optional

from agents import function_tool
from pydantic import BaseModel, Field, ValidationError

from dmhelper.clients.kanka import ENTITY_TYPES, EntityType, KankaClient
from dmhelper.config import get_settings
from dmhelper.store import db as store
from dmhelper.tools.lore import append_group_entry, write_alexya_entry
from dmhelper.tools.memory import memory_path, read_memory, write_memory


class ChangesetItem(BaseModel):
    entity_type: Literal[
        "characters",
        "locations",
        "organisations",
        "quests",
        "journals",
        "notes",
    ]
    name: str = Field(..., min_length=1, max_length=191)
    body: str = Field(
        default="",
        description="Long-form HTML/markdown body for the entity entry.",
    )
    local_key: str = Field(
        ...,
        min_length=1,
        max_length=191,
        description=(
            "Stable client-side id. Lets us update the same entity on "
            "repeat /confirm calls without duplicating."
        ),
    )
    lore_target: Optional[Literal["alaxya", "group"]] = Field(
        default=None,
        description=(
            "If set, after the Kanka write succeeds the same content is "
            "written back into local lore markdown: 'alaxya' -> a file in "
            "data/lore/alaxya/; 'group' -> appended to this group's file in "
            "data/lore/player groups/. Leave null for chat-only canon."
        ),
    )
    lore_category: Optional[str] = Field(
        default=None,
        description=(
            "Frontmatter category for an 'alaxya' write-back "
            "(e.g. Deities, History, Geography, Seven Espada)."
        ),
    )


class Changeset(BaseModel):
    group_id: str
    items: list[ChangesetItem]


def _session_id(group_id: str, chat_id: str) -> str:
    return f"{group_id}:{chat_id}"


def propose_changeset_impl(
    group_id: str,
    chat_id: str,
    items_json: str,
) -> str:
    """Plain-function form of propose_changeset (used by tests and the tool).

    Validates the JSON-encoded items, persists a `Changeset` row in
    `pending_changes`, and returns a human-readable summary. Does NOT
    touch Kanka.
    """
    try:
        raw = json.loads(items_json)
    except json.JSONDecodeError as e:
        return f"Invalid items_json: {e}. Pass a JSON array of items."
    try:
        changeset = Changeset(
            group_id=group_id, items=[ChangesetItem(**i) for i in raw]
        )
    except ValidationError as e:
        return f"Changeset failed validation:\n{e}"

    store.save_pending(_session_id(group_id, chat_id), changeset.model_dump())
    bullets = "\n".join(
        f"- **{it.entity_type}** `{it.name}` (local_key=`{it.local_key}`)"
        for it in changeset.items
    )
    return (
        f"Queued {len(changeset.items)} change(s) for group {group_id!r}:\n"
        f"{bullets}\n\n"
        'Reply "/confirm" to save these to Kanka. Nothing has been written yet.'
    )


@function_tool
def propose_changeset(
    group_id: str,
    chat_id: str,
    items_json: str,
) -> str:
    """Queue a set of Kanka edits for the current chat. Does NOT push to Kanka.

    Args:
        group_id: the play group the changes belong to.
        chat_id: the current chat id (used to scope the pending queue).
        items_json: JSON-encoded list of changeset items. Each item must
            contain `entity_type`, `name`, optional `body`, and
            `local_key`. Example::

                [
                  {"entity_type": "characters", "name": "Sir Renn",
                   "body": "Knight of the Espada.", "local_key": "renn-1"}
                ]
    """
    return propose_changeset_impl(group_id, chat_id, items_json)


async def _commit_item(
    client: KankaClient, group_id: str, item: ChangesetItem
) -> tuple[str, int, str]:
    """Returns (action, kanka_id, name). action in {'updated','created'}."""
    payload = {"name": item.name, "entry": item.body or ""}
    existing = store.get_kanka_id(group_id, item.local_key)
    if existing and existing[0] == item.entity_type:
        updated = await client.update(item.entity_type, existing[1], payload)
        return "updated", int(updated.get("id", existing[1])), item.name

    needle = item.name.strip().lower()
    hits = await client.search(item.name)
    for hit in hits:
        if (
            hit.get("type") == item.entity_type[:-1]
            and (hit.get("name") or "").strip().lower() == needle
        ):
            child_id = int(hit.get("child_id") or hit.get("id"))
            updated = await client.update(item.entity_type, child_id, payload)
            store.set_kanka_id(
                group_id, item.local_key, item.entity_type, child_id
            )
            return "updated", child_id, item.name

    created = await client.create(item.entity_type, payload)
    new_id = int(created["id"])
    store.set_kanka_id(group_id, item.local_key, item.entity_type, new_id)
    return "created", new_id, item.name


def _write_back_lore(group_id: str, item: ChangesetItem) -> str | None:
    """After a successful Kanka write, persist the item into local lore
    markdown if the changeset asked for it. Returns a human note or None."""
    if item.lore_target == "alaxya":
        path = write_alexya_entry(item.name, item.body, item.lore_category)
        return f"lore file {path}"
    if item.lore_target == "group":
        path = append_group_entry(group_id, item.name, item.body)
        return f"group file {path}"
    return None


def _append_memory(group_id: str, lines: list[str]) -> None:
    existing = read_memory(group_id)
    stamp = dt.datetime.now().isoformat(timespec="seconds")
    block = f"\n\n## /confirm {stamp}\n" + "\n".join(f"- {l}" for l in lines)
    write_memory(group_id, (existing or "").rstrip() + block + "\n")


async def apply_pending(
    group_id: str,
    chat_id: str,
    client: KankaClient | None = None,
) -> str:
    """Apply the queued changeset for this chat. Returns a human summary."""
    session_id = _session_id(group_id, chat_id)
    payload = store.load_pending(session_id)
    if not payload:
        return (
            "No pending changes queued for this chat. Nothing to confirm. "
            "Ask the assistant to propose a changeset first."
        )

    changeset = Changeset(**payload)

    owns_client = client is None
    if owns_client:
        settings = get_settings()
        client = KankaClient(
            token=settings.kanka_api_token.get_secret_value(),
            campaign_id=settings.kanka_campaign_id,
        )

    summaries: list[str] = []
    lore_notes: list[str] = []
    try:
        for item in changeset.items:
            action, kanka_id, name = await _commit_item(
                client, group_id, item
            )
            line = f"{action} {item.entity_type[:-1]} {name!r} (id={kanka_id})"
            note = _write_back_lore(group_id, item)
            if note:
                line += f" -> wrote {note}"
                lore_notes.append(note)
            summaries.append(line)
    finally:
        if owns_client:
            await client.aclose()

    store.clear_pending(session_id)
    _append_memory(group_id, summaries)
    out = "Saved to Kanka:\n" + "\n".join(f"- {s}" for s in summaries)
    out += f"\n\nMemory updated at {memory_path(group_id)}."
    if lore_notes:
        out += f"\nLore markdown updated: {len(lore_notes)} file(s)."
    return out


__all__ = [
    "Changeset",
    "ChangesetItem",
    "ENTITY_TYPES",
    "EntityType",
    "apply_pending",
    "propose_changeset",
    "propose_changeset_impl",
]
