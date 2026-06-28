"""Async client for Critical Role transcripts on the fandom wiki.

Uses the MediaWiki action API at https://criticalrole.fandom.com/api.php to
list transcript page titles and fetch transcript prose. Mirrors the
`clients/kanka.py` pattern: own `httpx.AsyncClient`, `aclose`, tenacity
retry on transient HTTP, polite User-Agent. No third-party search provider.

Fandom content is CC-BY-SA; we use it only to distil a transformative
narration style guide and keep short attributed excerpts.
"""

from __future__ import annotations

import re

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

_USER_AGENT = (
    "DMHelper/0.1 (single-user D&D assistant; "
    "https://github.com/tailevi/Dungeon_master_assistant)"
)

# Wiki/HTML markup stripping (same idea as tools/kanka_search.py:_strip_html).
_TAG_RE = re.compile(r"<[^>]+>")
_REF_RE = re.compile(r"<ref[^>]*>.*?</ref>", re.IGNORECASE | re.DOTALL)
_TEMPLATE_RE = re.compile(r"\{\{[^{}]*\}\}")
_FILE_LINK_RE = re.compile(r"\[\[(?:File|Image):[^\]]*\]\]", re.IGNORECASE)
_WIKILINK_RE = re.compile(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]")
_BOLD_ITALIC_RE = re.compile(r"'{2,5}")
_HEADING_RE = re.compile(r"^=+\s*(.*?)\s*=+$", re.MULTILINE)


def strip_markup(text: str) -> str:
    """Reduce wikitext/HTML to plain prose."""
    if not text:
        return ""
    text = _REF_RE.sub(" ", text)
    text = _FILE_LINK_RE.sub(" ", text)
    # collapse nested templates a couple passes
    for _ in range(3):
        new = _TEMPLATE_RE.sub(" ", text)
        if new == text:
            break
        text = new
    text = _WIKILINK_RE.sub(r"\1", text)
    text = _TAG_RE.sub(" ", text)
    text = _HEADING_RE.sub(r"\1", text)
    text = _BOLD_ITALIC_RE.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _looks_like_transcript(title: str) -> bool:
    t = title.lower()
    if ":" in title and not t.startswith("transcript"):
        # skip File:, Category:, Template:, Help: etc.
        return False
    return "transcript" in t or bool(re.search(r"\be\d+\b|episode", t))


class CriticalRoleError(RuntimeError):
    """Non-retryable error from the fandom API."""


class CriticalRoleClient:
    def __init__(
        self,
        *,
        base_url: str = "https://criticalrole.fandom.com/api.php",
        client: httpx.AsyncClient | None = None,
        max_attempts: int = 4,
    ) -> None:
        self._base_url = base_url
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
            timeout=httpx.Timeout(30.0),
        )
        self._max_attempts = max_attempts

    async def __aenter__(self) -> "CriticalRoleClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _get(self, params: dict[str, str]) -> dict:
        retryer = AsyncRetrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=20),
            retry=retry_if_exception_type(
                (httpx.TransportError, CriticalRoleError)
            ),
            reraise=True,
        )
        async for attempt in retryer:
            with attempt:
                resp = await self._client.get(self._base_url, params=params)
                if resp.status_code >= 500:
                    raise CriticalRoleError(
                        f"fandom API {resp.status_code}: {resp.text[:200]}"
                    )
                if resp.status_code >= 400:
                    # client errors are not retryable
                    raise CriticalRoleError(
                        f"fandom API {resp.status_code}: {resp.text[:200]}"
                    )
                return resp.json()
        raise CriticalRoleError("unreachable")

    async def list_transcript_titles(
        self, limit: int = 3, index_page: str = "Transcripts"
    ) -> list[str]:
        """Parse the Transcripts index page and return transcript page titles."""
        data = await self._get(
            {
                "action": "parse",
                "page": index_page,
                "prop": "links",
                "format": "json",
            }
        )
        links = (data.get("parse", {}) or {}).get("links", []) or []
        titles: list[str] = []
        for link in links:
            # MediaWiki returns links as {"ns": 0, "exists": "", "*": "Title"}
            title = link.get("*") if isinstance(link, dict) else None
            if not title:
                continue
            if _looks_like_transcript(title):
                titles.append(title)
            if len(titles) >= limit:
                break
        return titles

    async def get_transcript_text(self, title: str) -> str:
        """Fetch a transcript page's wikitext and reduce it to plain prose."""
        data = await self._get(
            {
                "action": "parse",
                "page": title,
                "prop": "wikitext",
                "format": "json",
            }
        )
        wikitext = (
            (data.get("parse", {}) or {}).get("wikitext", {}) or {}
        ).get("*", "")
        return strip_markup(wikitext)
