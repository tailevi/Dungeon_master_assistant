"""Web search tool wrapping Anthropic's native server-side web_search.

This tool exists so the orchestrator (running through LiteLLM) can call
web search via a plain function_tool. The actual search runs inside a
Claude API call here using `anthropic`'s SDK; no third-party search
provider is involved.

Tool block version pinned: `web_search_20260318` (latest as of 2026-06).
"""

from __future__ import annotations

from functools import lru_cache

from agents import function_tool
from anthropic import AsyncAnthropic

from dmhelper.config import get_settings


@lru_cache(maxsize=1)
def _client() -> AsyncAnthropic:
    settings = get_settings()
    return AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value())


def _extract_text(message_content: list[object]) -> str:
    parts: list[str] = []
    for block in message_content:
        text = getattr(block, "text", None)
        if isinstance(text, str) and text.strip():
            parts.append(text)
    return "\n\n".join(parts).strip()


@function_tool
async def web_search(query: str) -> str:
    """Search the public web for information about Exandria (Critical Role)
    or any other lore that is NOT in the local Alexya files.

    Returns Claude's grounded summary with citations. Use sparingly; prefer
    `lore_search` for anything about Alexya.
    """
    settings = get_settings()
    response = await _client().messages.create(
        model=settings.web_model,
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a research helper for a D&D Dungeon Master. "
                    "Search the web and summarise findings concisely with "
                    f"inline source URLs.\n\nQuestion: {query}"
                ),
            }
        ],
        tools=[
            {
                "type": "web_search_20260318",
                "name": "web_search",
                "max_uses": 5,
            }
        ],
    )
    text = _extract_text(list(response.content))
    return text or "No results."
