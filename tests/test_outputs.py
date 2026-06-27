from __future__ import annotations

from pathlib import Path

import pytest

from dmhelper.config import get_settings


@pytest.fixture(autouse=True)
def _env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("KANKA_API_TOKEN", "x")
    monkeypatch.setenv("KANKA_CAMPAIGN_ID", "1")
    monkeypatch.setenv("DMHELPER_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("DMHELPER_OUTPUTS_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_plain_text_is_not_saved() -> None:
    from dmhelper.outputs import maybe_emit_html

    text = "Here is a normal answer about Bahamut."
    out, path = maybe_emit_html(text)
    assert path is None
    assert out == text


def test_html_document_saved_with_title_filename() -> None:
    from dmhelper.outputs import maybe_emit_html

    html = (
        "<!DOCTYPE html>\n<html><head>"
        "<title>Session 5: The Mine</title></head>"
        "<body>hi</body></html>"
    )
    out, path = maybe_emit_html(html)
    assert path is not None
    assert path.name == "Session_5_The_Mine.html"
    assert path.read_text(encoding="utf-8") == html
    assert "Saved session document" in out
    assert "<details>" in out


def test_html_without_title_falls_back_to_timestamp() -> None:
    from dmhelper.outputs import maybe_emit_html

    html = "<html><body>no title here</body></html>"
    _out, path = maybe_emit_html(html)
    assert path is not None
    assert path.suffix == ".html"
    assert path.name.startswith("Session_")
