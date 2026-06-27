from __future__ import annotations

from pathlib import Path

import pytest

from dmhelper.config import get_settings


@pytest.fixture(autouse=True)
def _env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("KANKA_API_TOKEN", "x")
    monkeypatch.setenv("KANKA_CAMPAIGN_ID", "1")
    monkeypatch.setenv("DMHELPER_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_empty_when_no_instructions_dir() -> None:
    from dmhelper.agents.format_standards import load_format_standards

    assert load_format_standards() == ""


def test_loads_and_wraps_instruction_files() -> None:
    from dmhelper.agents.format_standards import load_format_standards

    s = get_settings()
    s.instructions_dir.mkdir(parents=True, exist_ok=True)
    (s.instructions_dir / "Session_Tempalte.md").write_text(
        "# SESSION TEMPLATE\nUse dark HTML.", encoding="utf-8"
    )

    out = load_format_standards()
    assert "CONDITIONAL" in out
    assert "Session_Tempalte.md" in out
    assert "Use dark HTML." in out


def test_writer_prompt_includes_standards() -> None:
    from dmhelper.agents.writer import _load_prompt

    s = get_settings()
    s.instructions_dir.mkdir(parents=True, exist_ok=True)
    (s.instructions_dir / "feats.md").write_text(
        "Custom feat format here.", encoding="utf-8"
    )
    prompt = _load_prompt(s)
    assert "Custom feat format here." in prompt
    assert "CONDITIONAL" in prompt


def test_instructor_prompt_includes_standards() -> None:
    from dmhelper.agents.instructor import _load_instructor_prompt

    s = get_settings()
    s.instructions_dir.mkdir(parents=True, exist_ok=True)
    (s.instructions_dir / "feats.md").write_text(
        "Custom feat format here.", encoding="utf-8"
    )
    prompt = _load_instructor_prompt(s)
    assert "Custom feat format here." in prompt


def test_instructor_prompt_includes_group_memory() -> None:
    from dmhelper.agents.instructor import _load_instructor_prompt
    from dmhelper.tools.memory import write_memory

    s = get_settings()
    write_memory("Noir", "Captain Vale rules the docks.")
    prompt = _load_instructor_prompt(s, "Noir")
    assert "Captain Vale rules the docks." in prompt
    assert "Established canon" in prompt


def test_instructor_prompt_handles_missing_group_memory() -> None:
    from dmhelper.agents.instructor import _load_instructor_prompt

    s = get_settings()
    prompt = _load_instructor_prompt(s, "Noir")
    assert "no rolling memory yet" in prompt
