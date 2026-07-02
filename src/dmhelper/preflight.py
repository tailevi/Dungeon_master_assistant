"""Startup preflight: is the Anthropic API reachable with the current key?

A tiny 1-token call at launch so the DM is warned in the terminal if the key
is invalid or out of credit BEFORE typing into the chat. Non-fatal — the UI
still starts either way.
"""

from __future__ import annotations

import anthropic

from dmhelper.config import get_settings
from dmhelper.errors import friendly_error


def check_anthropic() -> tuple[bool, str]:
    """Ping Anthropic with a minimal request. Returns (ok, message)."""
    settings = get_settings()
    try:
        client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key.get_secret_value()
        )
        client.messages.create(
            model=settings.web_model,  # cheap native id (e.g. sonnet)
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True, "Anthropic API reachable."
    except Exception as e:  # noqa: BLE001 - report, never crash startup
        return False, friendly_error(e)
