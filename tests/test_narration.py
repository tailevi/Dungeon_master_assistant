from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from dmhelper.config import get_settings


@pytest.fixture(autouse=True)
def _env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("KANKA_API_TOKEN", "x")
    monkeypatch.setenv("KANKA_CAMPAIGN_ID", "1")
    monkeypatch.setenv("DMHELPER_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DMHELPER_NARRATION_SAMPLE", "2")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class _FakeCRClient:
    """Stand-in for CriticalRoleClient as an async context manager."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return None

    async def list_transcript_titles(self, limit: int = 3):
        return ["C1E1 Transcript", "C1E2 Transcript", "C1E3 Transcript"][:limit]

    async def get_transcript_text(self, title: str):
        return f"MATT: Narration for {title}. The party steps forward."


def _fake_anthropic(captured: dict):
    class _Messages:
        async def create(self, **kwargs):
            captured.update(kwargs)
            block = SimpleNamespace(text="# Narration Style Guide\nStyle only.")
            return SimpleNamespace(content=[block])

    return SimpleNamespace(messages=_Messages())


async def test_build_guide_writes_file(monkeypatch: pytest.MonkeyPatch) -> None:
    from dmhelper.tools import narration

    captured: dict = {}
    monkeypatch.setattr(narration, "CriticalRoleClient", _FakeCRClient)
    monkeypatch.setattr(narration, "_anthropic", lambda: _fake_anthropic(captured))

    msg = await narration.build_narration_guide_impl()

    settings = get_settings()
    guide = settings.instructions_dir / narration.GUIDE_FILENAME
    assert guide.exists()
    assert "Narration Style Guide" in guide.read_text(encoding="utf-8")
    assert "Wrote Matt Mercer narration" in msg
    # configured sample = 2 -> two transcripts cited
    assert "C1E1 Transcript" in msg and "C1E2 Transcript" in msg
    assert "C1E3 Transcript" not in msg
    # excerpts were passed to the model
    prompt_text = captured["messages"][0]["content"]
    assert "Narration for C1E1" in prompt_text
    # distillation prompt emphasizes Matt Mercer's cadence, drive, dialogue
    assert "Matt Mercer" in prompt_text
    assert "cadence" in prompt_text.lower()
    assert "dialogue" in prompt_text.lower()
    assert "drive" in prompt_text.lower()


async def test_guide_is_loaded_by_format_standards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dmhelper.agents.format_standards import load_format_standards
    from dmhelper.tools import narration

    monkeypatch.setattr(narration, "CriticalRoleClient", _FakeCRClient)
    monkeypatch.setattr(narration, "_anthropic", lambda: _fake_anthropic({}))

    await narration.build_narration_guide_impl(episodes=1)
    standards = load_format_standards()
    assert "Narration Style Guide" in standards


async def test_explicit_titles_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from dmhelper.tools import narration

    captured: dict = {}
    monkeypatch.setattr(narration, "CriticalRoleClient", _FakeCRClient)
    monkeypatch.setattr(narration, "_anthropic", lambda: _fake_anthropic(captured))

    msg = await narration.build_narration_guide_impl(titles="C2E5 Transcript")
    assert "C2E5 Transcript" in msg
