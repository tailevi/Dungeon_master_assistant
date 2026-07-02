from __future__ import annotations

import time
from pathlib import Path

import pytest

from dmhelper.config import get_settings
from dmhelper.store import db as store


@pytest.fixture(autouse=True)
def _env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("KANKA_API_TOKEN", "x")
    monkeypatch.setenv("KANKA_CAMPAIGN_ID", "1")
    monkeypatch.setenv("DMHELPER_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    store.init_db()
    yield
    get_settings.cache_clear()


def test_create_and_list_chats() -> None:
    a = store.create_chat("Noir", "First")
    time.sleep(0.01)
    b = store.create_chat("Noir", "Second")
    chats = store.list_chats("Noir")
    ids = [c["chat_id"] for c in chats]
    # newest first
    assert ids[0] == b and ids[1] == a
    # scoped by group
    assert store.list_chats("The Wolf Pack") == []


def test_messages_round_trip_and_ordering() -> None:
    cid = store.create_chat("Noir")
    store.add_message("Noir", cid, "user", "hello")
    store.add_message("Noir", cid, "assistant", "hi there")
    msgs = store.get_messages("Noir", cid)
    assert msgs == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]
    assert store.message_count("Noir", cid) == 2


def test_add_message_creates_chat_if_missing() -> None:
    store.add_message("Noir", "orphan123", "user", "hey")
    assert any(c["chat_id"] == "orphan123" for c in store.list_chats("Noir"))


def test_add_message_bumps_updated_at_for_ordering() -> None:
    a = store.create_chat("Noir", "A")
    time.sleep(0.01)
    b = store.create_chat("Noir", "B")
    # a is older; sending to it should float it to the top
    time.sleep(0.01)
    store.add_message("Noir", a, "user", "ping")
    assert store.list_chats("Noir")[0]["chat_id"] == a


def test_rename_and_delete() -> None:
    cid = store.create_chat("Noir", "New chat")
    store.rename_chat("Noir", cid, "Session 13 planning")
    assert store.list_chats("Noir")[0]["title"] == "Session 13 planning"

    store.add_message("Noir", cid, "user", "x")
    store.delete_chat("Noir", cid)
    assert store.list_chats("Noir") == []
    assert store.get_messages("Noir", cid) == []
