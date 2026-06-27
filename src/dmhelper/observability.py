"""Tracing configuration.

The OpenAI Agents SDK can upload execution traces to the OpenAI Traces
dashboard (https://platform.openai.com/traces). Those uploads authenticate
with an OpenAI API key that is SEPARATE from the model calls — every model
call in this project still routes to Claude through LiteLLM. So the traces
land in *your* OpenAI account, not in anyone's Anthropic billing.

`configure_tracing()` is called once at app startup. It is deliberately not
run at package import time, so importing `dmhelper` (e.g. during tests)
never enables trace export.
"""

from __future__ import annotations

from agents import set_tracing_disabled, set_tracing_export_api_key

from dmhelper.config import get_settings


def configure_tracing() -> bool:
    """Enable trace export iff tracing is on AND an OpenAI key is present.

    Returns True if tracing was enabled, else False (and tracing is left
    disabled so nothing is uploaded).
    """
    settings = get_settings()
    if settings.tracing_enabled and settings.openai_api_key is not None:
        set_tracing_export_api_key(settings.openai_api_key.get_secret_value())
        set_tracing_disabled(False)
        return True

    set_tracing_disabled(True)
    return False
