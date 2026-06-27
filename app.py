"""Gradio chat for local DM-assistant testing.

Run:
    uv run python app.py

Launches on http://127.0.0.1:7860. Pick a group from the dropdown to
swap SQLiteSession; "New chat" bumps the chat counter so history starts
fresh for that group.
"""

from __future__ import annotations

import time
from pathlib import Path

import gradio as gr

import dmhelper  # noqa: F401  (imports run set_tracing_disabled)
from dmhelper.orchestrator import run_turn

def _groups_from_disk() -> list[str]:
    """Derive the group list from `data/lore/player groups/` (the source of
    truth), merged with any group that already has a memory file."""
    from dmhelper.config import get_settings
    from dmhelper.tools.lore import list_player_groups

    found: set[str] = set(list_player_groups())

    settings = get_settings()
    if settings.memory_dir.exists():
        for p in settings.memory_dir.glob("memory_*.md"):
            stem = p.stem.removeprefix("memory_")
            found.add(stem.replace("-", " ").title())
    return sorted(found)


def _new_chat_id() -> str:
    return f"chat-{int(time.time())}"


async def respond(
    message: str,
    history: list[dict[str, str]],
    group: str,
    chat_id: str,
) -> str:
    if not message.strip():
        return ""
    if not group:
        return "Pick a group from the dropdown first."
    return await run_turn(group, chat_id, message)


def build_ui() -> gr.Blocks:
    groups = _groups_from_disk()
    with gr.Blocks(title="DM Assistant") as demo:
        gr.Markdown("# DM Assistant\nClaude-powered DM helper for Mayan.")
        with gr.Row():
            group_dd = gr.Dropdown(
                choices=groups,
                value=groups[0] if groups else None,
                label="Play group",
                scale=3,
                allow_custom_value=True,
            )
            chat_state = gr.State(_new_chat_id())
            chat_label = gr.Markdown(value=f"`chat-id`: not set", scale=2)
            new_btn = gr.Button("New chat", scale=1)

        chat = gr.ChatInterface(
            fn=respond,
            type="messages",
            additional_inputs=[group_dd, chat_state],
            title=None,
            description=(
                "Ask about Alexya (homebrew, local lore), Exandria (web), "
                "or your groups' Kanka data. The assistant may propose a "
                'Kanka changeset; reply "/confirm" to save it.'
            ),
        )

        def _start_new_chat() -> tuple[str, str]:
            new_id = _new_chat_id()
            return new_id, f"`chat-id`: `{new_id}`"

        def _init_label(cid: str) -> str:
            return f"`chat-id`: `{cid}`"

        demo.load(_init_label, inputs=chat_state, outputs=chat_label)
        new_btn.click(_start_new_chat, outputs=[chat_state, chat_label])

    return demo


def main() -> None:
    Path("data").mkdir(exist_ok=True)
    from dmhelper.observability import configure_tracing

    if configure_tracing():
        print("Tracing ON -> https://platform.openai.com/traces")
    else:
        print("Tracing OFF (no OPENAI_API_KEY or DMHELPER_TRACING_ENABLED=false)")
    ui = build_ui()
    ui.launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
