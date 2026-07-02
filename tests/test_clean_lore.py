from __future__ import annotations

from pathlib import Path

import pytest

from dmhelper.config import get_settings
from dmhelper.maintenance import clean_lore


@pytest.fixture(autouse=True)
def _env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("KANKA_API_TOKEN", "x")
    monkeypatch.setenv("KANKA_CAMPAIGN_ID", "1")
    monkeypatch.setenv("DMHELPER_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


_BLOB = "A" * 5000


def test_strip_reference_definition_keeps_label() -> None:
    text = f"# Deities\n\nBahamut.\n\n[image1]: <data:image/png;base64,{_BLOB}>\n"
    out = clean_lore.strip_data_uris(text)
    assert "base64" not in out and "data:image" not in out
    assert "[image1]: (image removed)" in out
    assert "Bahamut." in out


def test_strip_inline_data_uri() -> None:
    text = f"See ![portrait](data:image/jpeg;base64,{_BLOB}) here."
    out = clean_lore.strip_data_uris(text)
    assert "base64" not in out
    assert "(image removed)" in out


def test_clean_file_saves_bytes_and_is_idempotent() -> None:
    s = get_settings()
    s.alexya_lore_dir.mkdir(parents=True, exist_ok=True)
    f = s.alexya_lore_dir / "Deities.md"
    f.write_text(
        f"# Deities\n\nprose\n\n[image1]: <data:image/png;base64,{_BLOB}>\n",
        encoding="utf-8",
    )
    before = f.stat().st_size
    saved = clean_lore.clean_file(f)
    after = f.stat().st_size
    assert saved > 4000
    assert after < before
    # second run: nothing left to strip
    assert clean_lore.clean_file(f) == 0


def test_clean_lore_dir_reports_changed_files() -> None:
    s = get_settings()
    s.alexya_lore_dir.mkdir(parents=True, exist_ok=True)
    (s.alexya_lore_dir / "big.md").write_text(
        f"x [image1]: <data:image/png;base64,{_BLOB}>", encoding="utf-8"
    )
    (s.alexya_lore_dir / "clean.md").write_text("# Fine\n\nno images", encoding="utf-8")

    results = clean_lore.clean_lore_dir(s.lore_dir)
    names = {p.name for p in results}
    assert "big.md" in names
    assert "clean.md" not in names  # unchanged files not reported
