"""Instructor judge Agent + the explicit writer/judge loop.

The judge returns plain text starting with `APPROVED` or `REJECT`. We parse
that text directly — no structured output type, which keeps it portable
across LitellmModel providers.

The judge is also given the active group's rolling memory file
(`data/memory/memory_<group>.md`, maintained by the book keeper) so it can
check the draft against established canon — same memory the book keeper
writes on `/confirm`.
"""

from __future__ import annotations

from dataclasses import dataclass

from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel

from dmhelper.agents.format_standards import load_format_standards
from dmhelper.config import Settings, get_settings
from dmhelper.tools.memory import read_memory


def _memory_block(group_id: str | None) -> str:
    if not group_id:
        return ""
    memory = read_memory(group_id).strip()
    body = memory if memory else "(no rolling memory yet)"
    return (
        f"## Established canon — rolling memory for group {group_id!r} "
        f"(book-keeper notes)\n\n{body}\n\n"
        "Use this to check the draft does not CONTRADICT established canon "
        "(NPCs, places, plot threads). Do not reject a draft merely for "
        "omitting memory details; reject only on contradiction or an "
        "invented fact that conflicts with the above."
    )


def _load_instructor_prompt(
    settings: Settings, group_id: str | None = None
) -> str:
    judge_path = settings.prompts_dir / "instructor.md"
    rules_path = settings.prompts_dir / "instructions.md"

    rules = (
        rules_path.read_text(encoding="utf-8")
        if rules_path.exists()
        else "(no house rules file found)"
    )
    standards = load_format_standards()
    if standards:
        rules = f"{rules}\n\n{standards}"
    memory_block = _memory_block(group_id)
    if memory_block:
        rules = f"{rules}\n\n{memory_block}"

    judge = (
        judge_path.read_text(encoding="utf-8")
        if judge_path.exists()
        else "You are the Instructor. Reply APPROVED or REJECT with numbered critique."
    )
    return judge.replace("<INSTRUCTIONS>", rules)


def build_instructor(group_id: str | None = None) -> Agent:
    settings = get_settings()
    return Agent(
        name="Instructor",
        instructions=_load_instructor_prompt(settings, group_id),
        model=LitellmModel(
            model=settings.judge_model,
            api_key=settings.anthropic_api_key.get_secret_value(),
        ),
        tools=[],
    )


@dataclass(slots=True)
class Verdict:
    approved: bool
    critique: str


def parse_verdict(text: str) -> Verdict:
    stripped = (text or "").strip()
    head = stripped.splitlines()[0].strip().upper() if stripped else ""
    if head.startswith("APPROVED"):
        return Verdict(approved=True, critique="")
    if head.startswith("REJECT"):
        critique = "\n".join(stripped.splitlines()[1:]).strip()
        return Verdict(approved=False, critique=critique)
    # Unparseable -> treat as rejection so we make one more pass.
    return Verdict(approved=False, critique=stripped)


def _judge_input(user_question: str, draft: str) -> str:
    return (
        f"User question:\n{user_question}\n\n"
        f"Writer draft:\n---\n{draft}\n---\n\n"
        "Apply the house rules and reply APPROVED or REJECT (with numbered "
        "critique). Output nothing else."
    )


async def judge_draft(
    user_question: str, draft: str, group_id: str | None = None
) -> Verdict:
    instructor = build_instructor(group_id)
    result = await Runner.run(instructor, _judge_input(user_question, draft))
    return parse_verdict(str(result.final_output))
