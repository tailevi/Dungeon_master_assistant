from __future__ import annotations

from pathlib import Path

import pytest

from dmhelper.config import get_settings
from dmhelper.tools import memory as memory_mod


@pytest.fixture(autouse=True)
def _reset_settings_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("KANKA_API_TOKEN", "x")
    monkeypatch.setenv("KANKA_CAMPAIGN_ID", "1")
    monkeypatch.setenv("DMHELPER_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_read_returns_empty_when_missing() -> None:
    assert memory_mod.read_memory("rolling-thunder") == ""


def test_write_then_read_round_trips() -> None:
    memory_mod.write_memory("rolling thunder", "session 12 recap")
    assert memory_mod.read_memory("rolling thunder") == "session 12 recap"


def test_slug_normalises_group_id() -> None:
    assert memory_mod.slug("Rolling Thunder!") == "rolling-thunder"
