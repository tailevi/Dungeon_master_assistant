from __future__ import annotations

import httpx
import pytest
import respx

from dmhelper.clients.kanka import KankaClient, KankaError


CAMPAIGN_BASE = "https://api.kanka.io/1.0/campaigns/42"


@pytest.fixture
async def client():
    c = KankaClient(token="tok", campaign_id=42, max_attempts=3)
    try:
        yield c
    finally:
        await c.aclose()


@respx.mock
async def test_list_characters_returns_data(client: KankaClient) -> None:
    respx.get(f"{CAMPAIGN_BASE}/characters").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": 1, "name": "Vex"}]}
        )
    )
    chars = await client.list("characters")
    assert chars == [{"id": 1, "name": "Vex"}]


@respx.mock
async def test_search_passes_query(client: KankaClient) -> None:
    route = respx.get(f"{CAMPAIGN_BASE}/search/Vex").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": 1, "name": "Vex"}]}
        )
    )
    hits = await client.search("Vex")
    assert hits and hits[0]["id"] == 1
    assert route.called


@respx.mock
async def test_retries_on_429_then_succeeds(client: KankaClient) -> None:
    route = respx.get(f"{CAMPAIGN_BASE}/quests").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"data": [{"id": 7, "name": "Q"}]}),
        ]
    )
    quests = await client.list("quests")
    assert route.call_count == 2
    assert quests == [{"id": 7, "name": "Q"}]


@respx.mock
async def test_gives_up_after_max_attempts(client: KankaClient) -> None:
    respx.get(f"{CAMPAIGN_BASE}/notes").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "0"})
    )
    from dmhelper.clients.kanka import KankaRateLimitError

    with pytest.raises(KankaRateLimitError):
        await client.list("notes")


@respx.mock
async def test_4xx_other_than_429_raises(client: KankaClient) -> None:
    respx.get(f"{CAMPAIGN_BASE}/journals/99").mock(
        return_value=httpx.Response(404, text="not found")
    )
    with pytest.raises(KankaError):
        await client.get("journals", 99)


@respx.mock
async def test_create_posts_payload(client: KankaClient) -> None:
    route = respx.post(f"{CAMPAIGN_BASE}/characters").mock(
        return_value=httpx.Response(
            201, json={"data": {"id": 11, "name": "New"}}
        )
    )
    created = await client.create("characters", {"name": "New"})
    assert created["id"] == 11
    import json as _json

    assert _json.loads(route.calls.last.request.read()) == {"name": "New"}
