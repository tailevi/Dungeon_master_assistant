"""Orchestrator Agent + per-turn pipeline.

Pipeline per user turn:

1. If the user message is `/confirm`, apply the queued Kanka changeset and
   return the audit summary. Do not invoke the orchestrator.
2. Otherwise run the Orchestrator Agent (with SQLiteSession for history).
   It calls retrieval tools and produces a draft answer with citations.
3. Pass that draft to the Writer Agent (no session) to polish.
4. If `judge_enabled`, send the Writer output to the Instructor judge.
   On `REJECT`, re-run the Writer with the critique appended. Max 2
   judge iterations total.
"""

from __future__ import annotations

from agents import Agent, Runner, SQLiteSession, trace
from agents.extensions.models.litellm_model import LitellmModel

from dmhelper.agents.instructor import judge_draft
from dmhelper.agents.writer import build_writer
from dmhelper.config import Settings, get_settings
from dmhelper.tools.kanka_search import kanka_player_search
from dmhelper.tools.kanka_write import apply_pending, propose_changeset
from dmhelper.tools.lore import (
    find_group_file,
    group_lore_search,
    list_player_groups,
    lore_search,
)
from dmhelper.outputs import maybe_emit_html
from dmhelper.tools.memory import memory_read, memory_write, read_memory
from dmhelper.tools.web import web_search

CONFIRM_TOKEN = "/confirm"


def _load_prompt(settings: Settings) -> str:
    path = settings.prompts_dir / "orchestrator.md"
    if not path.exists():
        return "You are the DM Assistant."
    return path.read_text(encoding="utf-8")


def _instructions_for(group_id: str, chat_id: str) -> str:
    settings = get_settings()
    base = _load_prompt(settings)
    memory = read_memory(group_id).strip() or "(no rolling memory yet)"

    known_groups = list_player_groups()
    groups_line = ", ".join(known_groups) if known_groups else "(none on disk)"
    has_file = find_group_file(group_id) is not None
    group_note = (
        f"A backstory file exists for this group — call "
        f"group_lore_search({group_id!r}) before answering group-specific "
        f"questions."
        if has_file
        else (
            f"No backstory file found for {group_id!r} yet; group_lore_search "
            f"will tell you which group files exist."
        )
    )

    return (
        f"{base}\n\n"
        f"## Active session\n"
        f"group_id = {group_id!r}\n"
        f"chat_id  = {chat_id!r}\n"
        f"known play groups on disk: {groups_line}\n"
        f"{group_note}\n\n"
        f"## Rolling memory for this group\n"
        f"{memory}\n"
    )


def _make_orchestrator_model() -> LitellmModel:
    settings = get_settings()
    return LitellmModel(
        model=settings.orchestrator_model,
        api_key=settings.anthropic_api_key.get_secret_value(),
    )


def build_orchestrator(group_id: str, chat_id: str) -> Agent:
    return Agent(
        name="DM Assistant",
        instructions=_instructions_for(group_id, chat_id),
        model=_make_orchestrator_model(),
        tools=[
            lore_search,
            group_lore_search,
            web_search,
            kanka_player_search,
            memory_read,
            memory_write,
            propose_changeset,
        ],
    )


def make_session(group_id: str, chat_id: str) -> SQLiteSession:
    settings = get_settings()
    settings.sessions_db_path.parent.mkdir(parents=True, exist_ok=True)
    return SQLiteSession(
        session_id=f"{group_id}:{chat_id}",
        db_path=str(settings.sessions_db_path),
    )


def _writer_input(user_message: str, draft: str, critique: str = "") -> str:
    parts = [
        f"User question:\n{user_message}",
        f"Orchestrator draft and gathered context:\n---\n{draft}\n---",
    ]
    if critique:
        parts.append(
            "Instructor critique on the previous Writer draft:\n"
            f"---\n{critique}\n---\n"
            "Address every numbered point."
        )
    return "\n\n".join(parts)


async def _write_with_judge(
    user_message: str, draft: str, group_id: str | None = None
) -> str:
    settings = get_settings()
    writer = build_writer()

    writer_result = await Runner.run(
        writer, _writer_input(user_message, draft)
    )
    answer = str(writer_result.final_output)

    if not settings.judge_enabled:
        return answer

    max_iterations = 2
    for _ in range(max_iterations):
        verdict = await judge_draft(user_message, answer, group_id)
        if verdict.approved:
            return answer
        writer_result = await Runner.run(
            writer, _writer_input(user_message, draft, verdict.critique)
        )
        answer = str(writer_result.final_output)
    return answer


async def run_turn(group_id: str, chat_id: str, user_message: str) -> str:
    if user_message.strip().lower() == CONFIRM_TOKEN:
        return await apply_pending(group_id, chat_id)

    # One trace per turn, grouped by group:chat so the OpenAI Traces
    # dashboard threads the orchestrator -> writer -> judge spans together.
    # No-op when tracing is disabled.
    with trace("DM turn", group_id=f"{group_id}:{chat_id}"):
        agent = build_orchestrator(group_id, chat_id)
        session = make_session(group_id, chat_id)
        orch_result = await Runner.run(agent, user_message, session=session)
        draft = str(orch_result.final_output)

        answer = await _write_with_judge(user_message, draft, group_id)

    # If the Writer produced a full HTML session document / feat, persist it
    # to the outputs folder and return a chat-friendly note + collapsible source.
    answer, _saved = maybe_emit_html(answer)
    return answer
