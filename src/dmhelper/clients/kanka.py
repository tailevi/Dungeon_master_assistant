"""Async httpx client for the Kanka REST API.

Docs: https://docs.kanka.io/en/latest/advanced/api.html

The free tier limits to 30 requests/minute per client, subscribers to 90.
We retry on HTTP 429 with tenacity's exponential backoff, honouring the
`Retry-After` header when present.
"""

from __future__ import annotations

from typing import Any, Iterable, Literal

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

EntityType = Literal[
    "characters",
    "locations",
    "organisations",
    "quests",
    "journals",
    "notes",
]

ENTITY_TYPES: tuple[EntityType, ...] = (
    "characters",
    "locations",
    "organisations",
    "quests",
    "journals",
    "notes",
)


class KankaError(RuntimeError):
    """Non-retryable API error."""


class KankaRateLimitError(RuntimeError):
    """Retryable rate-limit error (HTTP 429)."""

    def __init__(self, retry_after: float | None = None) -> None:
        super().__init__("Kanka rate limit hit (HTTP 429)")
        self.retry_after = retry_after


def _is_rate_limit(exc: BaseException) -> bool:
    return isinstance(exc, KankaRateLimitError)


class KankaClient:
    """Minimal async Kanka client scoped to a single campaign."""

    def __init__(
        self,
        token: str,
        campaign_id: int,
        *,
        base_url: str = "https://api.kanka.io/1.0",
        client: httpx.AsyncClient | None = None,
        max_attempts: int = 5,
    ) -> None:
        if not token:
            raise ValueError("Kanka token is required")
        if not campaign_id:
            raise ValueError("Kanka campaign_id is required")

        self.campaign_id = campaign_id
        self._campaign_base = f"{base_url.rstrip('/')}/campaigns/{campaign_id}"
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(30.0),
        )
        self._max_attempts = max_attempts

    # -- lifecycle ---------------------------------------------------------

    async def __aenter__(self) -> "KankaClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    # -- core request loop with 429 retry ---------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._campaign_base}{path}"

        retryer = AsyncRetrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=30),
            retry=retry_if_exception(_is_rate_limit),
            reraise=True,
        )
        async for attempt in retryer:
            with attempt:
                resp = await self._client.request(
                    method, url, params=params, json=json
                )
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    raise KankaRateLimitError(
                        float(retry_after) if retry_after else None
                    )
                if resp.status_code >= 400:
                    raise KankaError(
                        f"Kanka {method} {path} -> {resp.status_code}: {resp.text}"
                    )
                if resp.status_code == 204 or not resp.content:
                    return None
                return resp.json()

    # -- search ------------------------------------------------------------

    async def search(self, query: str) -> list[dict[str, Any]]:
        """Search entities by name across the campaign."""
        data = await self._request("GET", f"/search/{query}")
        return list((data or {}).get("data", []))

    # -- generic CRUD ------------------------------------------------------

    async def list(
        self,
        entity: EntityType,
        *,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        data = await self._request("GET", f"/{entity}", params=params)
        return list((data or {}).get("data", []))

    async def get(self, entity: EntityType, entity_id: int) -> dict[str, Any]:
        data = await self._request("GET", f"/{entity}/{entity_id}")
        return dict((data or {}).get("data", {}))

    async def create(
        self, entity: EntityType, payload: dict[str, Any]
    ) -> dict[str, Any]:
        data = await self._request("POST", f"/{entity}", json=payload)
        return dict((data or {}).get("data", {}))

    async def update(
        self, entity: EntityType, entity_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        data = await self._request(
            "PUT", f"/{entity}/{entity_id}", json=payload
        )
        return dict((data or {}).get("data", {}))

    # -- quest helpers used by kanka_player_search -------------------------

    async def quest_elements(self, quest_id: int) -> list[dict[str, Any]]:
        """Children attached to a quest (locations, characters, journals)."""
        data = await self._request("GET", f"/quests/{quest_id}/quest_elements")
        return list((data or {}).get("data", []))

    async def iter_entities(
        self, entities: Iterable[EntityType]
    ) -> dict[EntityType, list[dict[str, Any]]]:
        """List several entity collections sequentially.

        Sequential, not parallel, to stay friendly with the 30/min rate limit.
        """
        out: dict[EntityType, list[dict[str, Any]]] = {}
        for ent in entities:
            out[ent] = await self.list(ent)
        return out
