"""Turn raw LLM/provider exceptions into short, actionable messages.

Anthropic/LiteLLM errors arrive as long stack-trace-y strings. `friendly_error`
maps the common failure modes to a one-line message the DM can act on, so the
Gradio chat shows guidance instead of a traceback.
"""

from __future__ import annotations

_BILLING_URL = "https://console.anthropic.com/settings/billing"
_KEYS_URL = "https://console.anthropic.com/settings/keys"


def friendly_error(err: Exception | str) -> str:
    text = str(err)
    low = text.lower()

    if "credit balance is too low" in low or "plans & billing" in low:
        return (
            "⚠️ Anthropic API: your credit balance is too low. Add credits at "
            f"{_BILLING_URL}, then send your message again."
        )
    if (
        "authentication" in low
        or "invalid x-api-key" in low
        or "invalid api key" in low
        or "401" in low
    ):
        return (
            "⚠️ Anthropic rejected the API key. Check ANTHROPIC_API_KEY in "
            f".env (create/rotate one at {_KEYS_URL}) and restart the app."
        )
    if (
        "rate limit" in low
        or "rate_limit" in low
        or "429" in low
        or "overloaded" in low
        or "529" in low
    ):
        return (
            "⚠️ Anthropic API is rate-limited or overloaded right now. Wait a "
            "few seconds and try again."
        )
    if "model" in low and ("not_found" in low or "not found" in low):
        return (
            "⚠️ Model not found. Check the DMHELPER_*_MODEL ids in .env (e.g. "
            "anthropic/claude-opus-4-8) and restart the app."
        )

    snippet = text.strip().replace("\n", " ")
    if len(snippet) > 300:
        snippet = snippet[:300] + " …"
    return f"⚠️ The AI backend returned an error: {snippet}"
