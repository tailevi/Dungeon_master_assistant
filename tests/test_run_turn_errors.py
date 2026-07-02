from __future__ import annotations

import pytest

from dmhelper.config import get_settings


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("KANKA_API_TOKEN", "x")
    monkeypatch.setenv("KANKA_CAMPAIGN_ID", "1")
    monkeypatch.setenv("DMHELPER_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_run_turn_returns_friendly_message_on_model_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dmhelper import orchestrator

    async def _boom(*args, **kwargs):
        raise RuntimeError(
            'AnthropicError: {"error":{"message":"Your credit balance is too '
            'low to access the Anthropic API."}}'
        )

    # make building the agent cheap and force the model call to fail
    monkeypatch.setattr(orchestrator, "build_orchestrator", lambda g, c: object())
    monkeypatch.setattr(orchestrator.Runner, "run", _boom)

    out = await orchestrator.run_turn("Noir", "chat-1", "hello there")
    assert "credit balance is too low" in out
    assert "billing" in out.lower()
    # no exception escaped
    assert out.startswith("⚠️")
