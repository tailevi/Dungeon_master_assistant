from __future__ import annotations

from types import SimpleNamespace

import pytest

from dmhelper.config import get_settings


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("KANKA_API_TOKEN", "x")
    monkeypatch.setenv("KANKA_CAMPAIGN_ID", "1")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _fake_anthropic_module(create_side_effect):
    class _Messages:
        def create(self, **kwargs):
            if isinstance(create_side_effect, Exception):
                raise create_side_effect
            return SimpleNamespace(content=[])

    class _Client:
        def __init__(self, **kwargs):
            self.messages = _Messages()

    return SimpleNamespace(Anthropic=_Client)


def test_preflight_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    from dmhelper import preflight

    monkeypatch.setattr(preflight, "anthropic", _fake_anthropic_module(None))
    ok, msg = preflight.check_anthropic()
    assert ok is True
    assert "reachable" in msg.lower()


def test_preflight_reports_credit_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from dmhelper import preflight

    err = RuntimeError("Your credit balance is too low to access the Anthropic API")
    monkeypatch.setattr(preflight, "anthropic", _fake_anthropic_module(err))
    ok, msg = preflight.check_anthropic()
    assert ok is False
    assert "credit balance is too low" in msg
