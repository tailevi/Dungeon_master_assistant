"""Writer Agent — turns the orchestrator's draft + context into the final
answer for Mayan. No tools; pure synthesis."""

from __future__ import annotations

from agents import Agent
from agents.extensions.models.litellm_model import LitellmModel

from dmhelper.config import Settings, get_settings


def _load_prompt(settings: Settings) -> str:
    path = settings.prompts_dir / "writer.md"
    if not path.exists():
        return "You are the Writer."
    return path.read_text(encoding="utf-8")


def build_writer() -> Agent:
    settings = get_settings()
    return Agent(
        name="Writer",
        instructions=_load_prompt(settings),
        model=LitellmModel(
            model=settings.writer_model,
            api_key=settings.anthropic_api_key.get_secret_value(),
        ),
        tools=[],
    )
