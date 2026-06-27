from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from dmhelper.clients.kanka import KankaClient
from dmhelper.config import get_settings
from dmhelper.store import db as store
from dmhelper.tools import kanka_write
from dmhelper.tools.kanka_write import Changeset, ChangesetItem, apply_pending


CAMPAIGN_ID = 42
CAMPAIGN_BASE = f"https://api.kanka.io/1.0/campaigns/{CAMPAIGN_ID}"


@pytest.fixture(autouse=True)
def _isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("KANKA_API_TOKEN", "x")
    monkeypatch.setenv("KANKA_CAMPAIGN_ID", str(CAMPAIGN_ID))
    monkeypatch.setenv("DMHELPER_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    store.init_db()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def client():
    c = KankaClient(token="tok", campaign_id=CAMPAIGN_ID, max_attempts=3)
    try:
        yield c
    finally:
        await c.aclose()


def _queue_one_item() -> Changeset:
    cs = Changeset(
        group_id="rolling-thunder",
        items=[
            ChangesetItem(
                entity_type="characters",
                name="Sir Renn",
                body="Knight of the Espada.",
                local_key="sir-renn",
            )
        ],
    )
    store.save_pending(
        kanka_write._session_id("rolling-thunder", "chat-1"),
        cs.model_dump(),
    )
    return cs


async def test_confirm_writes_back_to_alaxya_lore(
    client: KankaClient,
) -> None:
    cs = Changeset(
        group_id="noir",
        items=[
            ChangesetItem(
                entity_type="characters",
                name="Bahamut",
                body="The platinum dragon.",
                local_key="bahamut",
                lore_target="alaxya",
                lore_category="Deities",
            )
        ],
    )
    store.save_pending(kanka_write._session_id("noir", "chat-1"), cs.model_dump())

    with respx.mock(assert_all_called=False) as router:
        router.get(f"{CAMPAIGN_BASE}/search/Bahamut").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        router.post(f"{CAMPAIGN_BASE}/characters").mock(
            return_value=httpx.Response(
                201, json={"data": {"id": 900, "name": "Bahamut"}}
            )
        )
        msg = await apply_pending("noir", "chat-1", client=client)

    settings = get_settings()
    written = settings.alexya_lore_dir / "bahamut.md"
    assert written.exists()
    assert "platinum dragon" in written.read_text(encoding="utf-8")
    assert "wrote lore file" in msg


async def test_confirm_writes_back_to_group_file(
    client: KankaClient,
) -> None:
    settings = get_settings()
    settings.group_lore_dir.mkdir(parents=True, exist_ok=True)
    gfile = settings.group_lore_dir / "Noir_ Players.md"
    gfile.write_text("# Noir — Players\n\nOrigin.", encoding="utf-8")

    cs = Changeset(
        group_id="Noir",
        items=[
            ChangesetItem(
                entity_type="characters",
                name="Captain Vale",
                body="A rival captain.",
                local_key="vale",
                lore_target="group",
            )
        ],
    )
    store.save_pending(kanka_write._session_id("Noir", "chat-1"), cs.model_dump())

    with respx.mock(assert_all_called=False) as router:
        router.get(f"{CAMPAIGN_BASE}/search/Captain Vale").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        router.post(f"{CAMPAIGN_BASE}/characters").mock(
            return_value=httpx.Response(
                201, json={"data": {"id": 901, "name": "Captain Vale"}}
            )
        )
        await apply_pending("Noir", "chat-1", client=client)

    text = gfile.read_text(encoding="utf-8")
    assert "Origin." in text
    assert "## Captain Vale" in text
    assert "rival captain" in text


async def test_apply_pending_without_queue_does_not_write(
    client: KankaClient,
) -> None:
    with respx.mock(assert_all_called=False) as router:
        post = router.post(f"{CAMPAIGN_BASE}/characters").mock(
            return_value=httpx.Response(201, json={"data": {"id": 1}})
        )
        msg = await apply_pending(
            "rolling-thunder", "no-queue-chat", client=client
        )
    assert "No pending changes" in msg
    assert post.call_count == 0


async def test_confirm_creates_when_no_existing(
    client: KankaClient,
) -> None:
    _queue_one_item()
    with respx.mock(assert_all_called=False) as router:
        router.get(f"{CAMPAIGN_BASE}/search/Sir Renn").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        post = router.post(f"{CAMPAIGN_BASE}/characters").mock(
            return_value=httpx.Response(
                201, json={"data": {"id": 501, "name": "Sir Renn"}}
            )
        )

        msg = await apply_pending(
            "rolling-thunder", "chat-1", client=client
        )

    assert post.call_count == 1
    assert "created character 'Sir Renn'" in msg
    assert store.get_kanka_id("rolling-thunder", "sir-renn") == (
        "characters",
        501,
    )
    # pending cleared on success
    assert store.load_pending(
        kanka_write._session_id("rolling-thunder", "chat-1")
    ) is None


async def test_search_before_write_updates_existing_match(
    client: KankaClient,
) -> None:
    _queue_one_item()
    with respx.mock(assert_all_called=False) as router:
        router.get(f"{CAMPAIGN_BASE}/search/Sir Renn").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": 9000,
                            "child_id": 777,
                            "name": "Sir Renn",
                            "type": "character",
                        }
                    ]
                },
            )
        )
        post = router.post(f"{CAMPAIGN_BASE}/characters").mock(
            return_value=httpx.Response(500, text="should not be called")
        )
        put = router.put(f"{CAMPAIGN_BASE}/characters/777").mock(
            return_value=httpx.Response(
                200, json={"data": {"id": 777, "name": "Sir Renn"}}
            )
        )

        msg = await apply_pending(
            "rolling-thunder", "chat-1", client=client
        )

    assert post.call_count == 0
    assert put.call_count == 1
    assert "updated character 'Sir Renn'" in msg
    assert store.get_kanka_id("rolling-thunder", "sir-renn") == (
        "characters",
        777,
    )


async def test_repeat_confirm_uses_cached_kanka_id(
    client: KankaClient,
) -> None:
    store.set_kanka_id("rolling-thunder", "sir-renn", "characters", 777)
    _queue_one_item()
    with respx.mock(assert_all_called=False) as router:
        search = router.get(f"{CAMPAIGN_BASE}/search/Sir Renn").mock(
            return_value=httpx.Response(500, text="should not search")
        )
        put = router.put(f"{CAMPAIGN_BASE}/characters/777").mock(
            return_value=httpx.Response(
                200, json={"data": {"id": 777, "name": "Sir Renn"}}
            )
        )

        msg = await apply_pending(
            "rolling-thunder", "chat-1", client=client
        )

    assert search.call_count == 0
    assert put.call_count == 1
    assert "updated character 'Sir Renn'" in msg


async def test_apply_pending_appends_to_memory(client: KankaClient) -> None:
    _queue_one_item()
    with respx.mock(assert_all_called=False) as router:
        router.get(f"{CAMPAIGN_BASE}/search/Sir Renn").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        router.post(f"{CAMPAIGN_BASE}/characters").mock(
            return_value=httpx.Response(
                201, json={"data": {"id": 501, "name": "Sir Renn"}}
            )
        )
        await apply_pending("rolling-thunder", "chat-1", client=client)

    settings = get_settings()
    mem = (settings.memory_dir / "memory_rolling-thunder.md").read_text(
        encoding="utf-8"
    )
    assert "/confirm" in mem
    assert "Sir Renn" in mem
    assert "id=501" in mem


def test_propose_changeset_blocks_writes_until_confirm() -> None:
    """propose_changeset must queue and never call Kanka. We assert no HTTP
    is made and the row lands in pending_changes."""
    payload = json.dumps(
        [
            {
                "entity_type": "notes",
                "name": "Plot thread A",
                "body": "the cult is real",
                "local_key": "plot-a",
            }
        ]
    )
    with respx.mock(assert_all_called=False) as router:
        # Catch-all: any HTTP call during propose must fail the test.
        router.route(host="api.kanka.io").mock(
            return_value=httpx.Response(500, text="propose must not call HTTP")
        )
        msg = kanka_write.propose_changeset_impl(
            group_id="g1", chat_id="c1", items_json=payload
        )
        # Nothing should have been called
        assert all(call.response is None for call in router.calls) or len(
            router.calls
        ) == 0

    assert "Reply" in msg and "/confirm" in msg
    pending = store.load_pending(kanka_write._session_id("g1", "c1"))
    assert pending is not None
    assert pending["items"][0]["name"] == "Plot thread A"
