"""Instructor judge Agent + the explicit writer/judge loop.

The judge returns plain text starting with `APPROVED` or `REJECT`. We parse
that text directly — no structured output type, which keeps it portable
across LitellmModel providers.
"""

from __future__ import annotations

from dataclasses import dataclass

from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel

from dmhelper.config import Settings, get_settings


def _load_instructor_prompt(settings: Settings) -> str:
    judge_path = settings.prompts_dir / "instructor.md"
    rules_path = settings.prompts_dir / "instructions.md"

    rules = (
        rules_path.read_text(encoding="utf-8")
        if rules_path.exists()
        else "(no house rules file found)"
    )
    judge = (
        judge_path.read_text(encoding="utf-8")
        if judge_path.exists()
        else "You are the Instructor. Reply APPROVED or REJECT with numbered critique."
    )
    return judge.replace("<INSTRUCTIONS>", rules)


def build_instructor() -> Agent:
    settings = get_settings()
    return Agent(
        name="Instructor",
        instructions=_load_instructor_prompt(settings),
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


async def judge_draft(user_question: str, draft: str) -> Verdict:
    instructor = build_instructor()
    result = await Runner.run(instructor, _judge_input(user_question, draft))
    return parse_verdict(str(result.final_output))
