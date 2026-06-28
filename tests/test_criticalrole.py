from __future__ import annotations

import httpx
import pytest
import respx

from dmhelper.clients.criticalrole import (
    CriticalRoleClient,
    CriticalRoleError,
    strip_markup,
)

API = "https://criticalrole.fandom.com/api.php"


@pytest.fixture
async def client():
    c = CriticalRoleClient(max_attempts=3)
    try:
        yield c
    finally:
        await c.aclose()


def test_strip_markup_reduces_wikitext() -> None:
    raw = (
        "== Part I ==\n'''MATT:''' The [[Mighty Nein|party]] enters "
        "{{tooltip|the keep}}.<ref>note</ref>\n[[File:x.png]]"
    )
    out = strip_markup(raw)
    assert "Part I" in out
    assert "MATT:" in out
    assert "party enters" in out
    assert "{{" not in out and "[[" not in out and "<ref" not in out
    assert "File:" not in out


@respx.mock
async def test_list_transcript_titles_filters(client: CriticalRoleClient) -> None:
    respx.get(API).mock(
        return_value=httpx.Response(
            200,
            json={
                "parse": {
                    "links": [
                        {"ns": 0, "*": "Campaign 1 Episode 1 Transcript"},
                        {"ns": 14, "*": "Category:Transcripts"},
                        {"ns": 0, "*": "Vox Machina"},
                        {"ns": 0, "*": "C2E5 Transcript"},
                    ]
                }
            },
        )
    )
    titles = await client.list_transcript_titles(limit=5)
    assert "Campaign 1 Episode 1 Transcript" in titles
    assert "C2E5 Transcript" in titles
    assert "Category:Transcripts" not in titles
    assert "Vox Machina" not in titles


@respx.mock
async def test_get_transcript_text_strips(client: CriticalRoleClient) -> None:
    respx.get(API).mock(
        return_value=httpx.Response(
            200,
            json={"parse": {"wikitext": {"*": "'''MATT:''' Welcome.<ref>x</ref>"}}},
        )
    )
    text = await client.get_transcript_text("C2E5 Transcript")
    assert "MATT: Welcome." in text
    assert "'''" not in text and "<ref" not in text


@respx.mock
async def test_retries_on_5xx_then_succeeds(client: CriticalRoleClient) -> None:
    route = respx.get(API).mock(
        side_effect=[
            httpx.Response(503, text="busy"),
            httpx.Response(200, json={"parse": {"links": []}}),
        ]
    )
    titles = await client.list_transcript_titles(limit=3)
    assert titles == []
    assert route.call_count == 2


@respx.mock
async def test_4xx_raises(client: CriticalRoleClient) -> None:
    respx.get(API).mock(return_value=httpx.Response(404, text="nope"))
    with pytest.raises(CriticalRoleError):
        await client.get_transcript_text("Missing")
