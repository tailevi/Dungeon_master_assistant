from __future__ import annotations

from dmhelper.errors import friendly_error


def test_credit_balance_maps_to_billing() -> None:
    msg = friendly_error(
        'AnthropicException - {"error":{"message":"Your credit balance is '
        'too low to access the Anthropic API."}}'
    )
    assert "credit balance is too low" in msg
    assert "billing" in msg.lower()


def test_auth_error_maps_to_key_guidance() -> None:
    msg = friendly_error("anthropic authentication_error: invalid x-api-key")
    assert "ANTHROPIC_API_KEY" in msg


def test_rate_limit_maps() -> None:
    msg = friendly_error("Error code: 429 - rate_limit_error overloaded")
    assert "rate-limited" in msg.lower() or "overloaded" in msg.lower()


def test_model_not_found_maps() -> None:
    msg = friendly_error('not_found_error: model "claude-bogus" not found')
    assert "DMHELPER_" in msg


def test_fallback_truncates() -> None:
    msg = friendly_error("boom " * 200)
    assert msg.startswith("⚠️ The AI backend returned an error:")
    assert len(msg) < 360
