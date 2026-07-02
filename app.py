"""Gradio chat for the DM assistant — Claude.ai-style multi-chat UI.

Run:
    uv run python app.py

Launches on http://127.0.0.1:7860.

Each play group has its own list of chats. Chats are saved to disk, so you
can close the app and reopen a chat the next day and continue from where you
stopped, seeing the whole past conversation. Two layers persist this:
- the OpenAI Agents `SQLiteSession` (data/sessions.db) holds the MODEL context
  per `group:chat` and auto-resumes it;
- a small chat registry + transcript (data/store.db) drives the chat list and
  renders the visible history.
Open the app in two browser tabs to run two chats at the same time.
"""

from __future__ import annotations

from pathlib import Path

import gradio as gr

import dmhelper  # noqa: F401  (import runs set_tracing_disabled)
from dmhelper.orchestrator import run_turn
from dmhelper.store import db as store

_THINKING = "_…thinking…_"


def _groups_from_disk() -> list[str]:
    """Group list from `data/lore/player groups/`, merged with any group that
    already has a memory file."""
    from dmhelper.config import get_settings
    from dmhelper.tools.lore import list_player_groups

    found: set[str] = set(list_player_groups())
    settings = get_settings()
    if settings.memory_dir.exists():
        for p in settings.memory_dir.glob("memory_*.md"):
            stem = p.stem.removeprefix("memory_")
            found.add(stem.replace("-", " ").title())
    return sorted(found)


def _title_from(message: str) -> str:
    line = message.strip().splitlines()[0] if message.strip() else "New chat"
    return (line[:40] + "…") if len(line) > 40 else line


def _chat_choices(group: str) -> list[tuple[str, str]]:
    """(label, chat_id) pairs for the chat radio, newest first."""
    return [(c["title"], c["chat_id"]) for c in store.list_chats(group)]


def _radio_update(group: str, selected: str | None):
    return gr.update(choices=_chat_choices(group), value=selected)


def _ensure_chat(group: str) -> str:
    """Return the latest chat for the group, creating one if none exist."""
    chats = store.list_chats(group)
    if chats:
        return chats[0]["chat_id"]
    return store.create_chat(group)


# -- event handlers ----------------------------------------------------


def load_group(group: str):
    """On startup / group change: pick the latest chat and show its history."""
    if not group:
        return _radio_update(group, None), None, []
    chat_id = _ensure_chat(group)
    return _radio_update(group, chat_id), chat_id, store.get_messages(group, chat_id)


def select_chat(group: str, chat_id: str):
    """Load a chat's transcript into the chatbot (no radio change → no loop)."""
    if not group or not chat_id:
        return [], chat_id
    return store.get_messages(group, chat_id), chat_id


def new_chat(group: str):
    chat_id = store.create_chat(group, "New chat")
    return _radio_update(group, chat_id), chat_id, []


def delete_current(group: str, chat_id: str):
    if group and chat_id:
        store.delete_chat(group, chat_id)
    new_id = _ensure_chat(group)
    return _radio_update(group, new_id), new_id, store.get_messages(group, new_id)


async def send(message: str, group: str, chat_id: str):
    outputs_msg = ""  # clears the textbox
    if not message.strip():
        yield store.get_messages(group, chat_id) if chat_id else [], message, gr.update(), chat_id
        return
    if not group:
        yield [{"role": "assistant", "content": "Pick a play group first."}], "", gr.update(), chat_id
        return

    if not chat_id:
        chat_id = store.create_chat(group)

    first = store.message_count(group, chat_id) == 0
    store.add_message(group, chat_id, "user", message)
    if first:
        store.rename_chat(group, chat_id, _title_from(message))

    # immediate echo of the user's message + a thinking placeholder
    echo = store.get_messages(group, chat_id) + [
        {"role": "assistant", "content": _THINKING}
    ]
    yield echo, outputs_msg, _radio_update(group, chat_id), chat_id

    answer = await run_turn(group, chat_id, message)
    store.add_message(group, chat_id, "assistant", answer)

    yield (
        store.get_messages(group, chat_id),
        outputs_msg,
        _radio_update(group, chat_id),
        chat_id,
    )


def build_ui() -> gr.Blocks:
    groups = _groups_from_disk()
    with gr.Blocks(title="DM Assistant", fill_height=True) as demo:
        gr.Markdown("# DM Assistant\nClaude-powered DM helper for Mayan.")

        group_state = gr.State(groups[0] if groups else None)
        chat_state = gr.State(None)

        with gr.Row():
            group_dd = gr.Dropdown(
                choices=groups,
                value=groups[0] if groups else None,
                label="Play group",
                scale=3,
                allow_custom_value=True,
            )

        with gr.Row(equal_height=False):
            with gr.Column(scale=1, min_width=220):
                new_btn = gr.Button("➕ New chat", variant="primary")
                chat_radio = gr.Radio(
                    choices=[], label="Chats", value=None, interactive=True
                )
                delete_btn = gr.Button("🗑 Delete chat", size="sm")
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(height=560, label="Conversation")
                msg_box = gr.Textbox(
                    placeholder="Ask about Alaxya lore, a group's Kanka history, "
                    'or develop the story. Reply "/confirm" to save a proposed '
                    "changeset.",
                    show_label=False,
                    submit_btn=True,
                )

        # keep the group_state in sync with the dropdown
        group_dd.change(lambda g: g, inputs=group_dd, outputs=group_state)

        # startup + group change -> load that group's latest chat
        demo.load(
            load_group,
            inputs=group_dd,
            outputs=[chat_radio, chat_state, chatbot],
        )
        group_dd.change(
            load_group,
            inputs=group_dd,
            outputs=[chat_radio, chat_state, chatbot],
        )

        chat_radio.input(
            select_chat,
            inputs=[group_dd, chat_radio],
            outputs=[chatbot, chat_state],
        )
        new_btn.click(
            new_chat,
            inputs=group_dd,
            outputs=[chat_radio, chat_state, chatbot],
        )
        delete_btn.click(
            delete_current,
            inputs=[group_dd, chat_state],
            outputs=[chat_radio, chat_state, chatbot],
        )

        msg_box.submit(
            send,
            inputs=[msg_box, group_dd, chat_state],
            outputs=[chatbot, msg_box, chat_radio, chat_state],
        )

    return demo


def main() -> None:
    Path("data").mkdir(exist_ok=True)

    # Windows consoles default to cp1252; force UTF-8 so status glyphs and
    # any non-ASCII in messages never crash startup prints.
    import sys

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass

    from dmhelper.observability import configure_tracing

    if configure_tracing():
        print("Tracing ON -> https://platform.openai.com/traces")
    else:
        print("Tracing OFF (no OPENAI_API_KEY or DMHELPER_TRACING_ENABLED=false)")

    from dmhelper.preflight import check_anthropic

    ok, message = check_anthropic()
    print(f"{'✅' if ok else '⚠️ '} {message}")
    if not ok:
        print("   The chat will not be able to reply until this is resolved.")

    ui = build_ui()
    ui.launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
