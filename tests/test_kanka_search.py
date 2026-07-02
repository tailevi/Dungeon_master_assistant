from __future__ import annotations

import httpx
import pytest
import respx

from dmhelper.config import get_settings
from dmhelper.tools import kanka_search

CAMPAIGN_ID = 267518
BASE = f"https://api.kanka.io/1.0/campaigns/{CAMPAIGN_ID}"


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("KANKA_API_TOKEN", "tok")
    monkeypatch.setenv("KANKA_CAMPAIGN_ID", str(CAMPAIGN_ID))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_keywords_drops_stopwords_and_short() -> None:
    kws = kanka_search._keywords(
        "session 13 combat faceless Inya twin elf Yondu Christopher Strovnik"
    )
    lowered = [k.lower() for k in kws]
    assert "inya" in lowered and "yondu" in lowered and "strovnik" in lowered
    assert "session" not in lowered and "combat" not in lowered
    assert "elf" not in lowered  # short / stopword


async def _run(group: str, query: str) -> str:
    return await kanka_search.kanka_player_search_impl(group, query)


@respx.mock
async def test_campaign_wide_search_runs_and_covers_other_groups() -> None:
    # quests: the active group + another group's quest
    respx.get(f"{BASE}/quests").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"id": 144477, "name": "The Wolf Pack", "entry": "<p>arc</p>"},
                    {"id": 112912, "name": "The Unseen Assembly"},
                ]
            },
        )
    )
    respx.get(f"{BASE}/journals").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    respx.get(f"{BASE}/quests/144477/quest_elements").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    # campaign-wide search: Yondu exists (owned conceptually by another group)
    respx.get(f"{BASE}/search/Yondu").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"id": 5, "entity_id": 500, "name": "Yondu", "type": "character"}
                ]
            },
        )
    )
    # any other search term -> empty
    respx.get(url__regex=rf"{BASE}/search/.+").mock(
        return_value=httpx.Response(200, json={"data": []})
    )

    out = await _run("The Wolf Pack", "Where is Yondu headed?")
    assert "The Wolf Pack" in out
    assert "Campaign-wide matches" in out
    assert "Yondu" in out


@respx.mock
async def test_search_runs_even_when_group_quest_missing() -> None:
    respx.get(f"{BASE}/quests").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    respx.get(f"{BASE}/search/Strovnik").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"id": 9, "entity_id": 900, "name": "Strovnik", "type": "character"}
                ]
            },
        )
    )
    respx.get(url__regex=rf"{BASE}/search/.+").mock(
        return_value=httpx.Response(200, json={"data": []})
    )

    out = await _run("Unknown Group", "What about Strovnik?")
    assert "No Kanka quest matched" in out
    assert "Strovnik" in out  # campaign search still ran
