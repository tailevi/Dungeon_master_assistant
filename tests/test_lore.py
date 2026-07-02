from __future__ import annotations

from pathlib import Path

import frontmatter
import pytest

from dmhelper.config import get_settings
from dmhelper.tools import lore


@pytest.fixture(autouse=True)
def _env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("KANKA_API_TOKEN", "x")
    monkeypatch.setenv("KANKA_CAMPAIGN_ID", "1")
    monkeypatch.setenv("DMHELPER_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    s = get_settings()
    s.alexya_lore_dir.mkdir(parents=True, exist_ok=True)
    s.group_lore_dir.mkdir(parents=True, exist_ok=True)
    yield
    get_settings.cache_clear()


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_group_display_name_strips_players_suffix(tmp_path: Path) -> None:
    assert lore.group_display_name(Path("Noir_ Players.md")) == "Noir"
    assert (
        lore.group_display_name(Path("The Wolf Pack_ Players.md"))
        == "The Wolf Pack"
    )


def test_find_group_file_tolerant_match() -> None:
    s = get_settings()
    _write(s.group_lore_dir / "The Wolf Pack_ Players.md", "# pack")
    _write(s.group_lore_dir / "Noir_ Players.md", "# noir")

    assert lore.find_group_file("the wolf pack").name == "The Wolf Pack_ Players.md"
    assert lore.find_group_file("Noir").name == "Noir_ Players.md"
    assert lore.find_group_file("Nonexistent") is None


def test_list_player_groups() -> None:
    s = get_settings()
    _write(s.group_lore_dir / "Noir_ Players.md", "x")
    _write(s.group_lore_dir / "The Wolf Pack_ Players.md", "x")
    assert lore.list_player_groups() == ["Noir", "The Wolf Pack"]


def test_write_alexya_entry_creates_frontmatter_file() -> None:
    path = lore.write_alexya_entry(
        "Bahamut", "The platinum dragon.", category="Deities"
    )
    assert path.exists()
    post = frontmatter.load(path)
    assert post.metadata["title"] == "Bahamut"
    assert post.metadata["category"] == "Deities"
    assert "platinum dragon" in post.content


def test_append_group_entry_appends_section() -> None:
    s = get_settings()
    gpath = s.group_lore_dir / "Noir_ Players.md"
    _write(gpath, "# Noir — Players\n\nBackstory.")
    out = lore.append_group_entry("Noir", "Captain Vale", "A new NPC.")
    text = out.read_text(encoding="utf-8")
    assert "Backstory." in text
    assert "## Captain Vale" in text
    assert "A new NPC." in text


def test_append_group_entry_creates_file_when_missing() -> None:
    out = lore.append_group_entry("Brand New Group", "Thing", "body")
    assert out.exists()
    assert out.name == "Brand New Group_ Players.md"


def test_lore_search_finds_cross_world_section() -> None:
    s = get_settings()
    _write(
        s.alexya_lore_dir / "HISTORY OF ALAXYA.md",
        "# History\n\n## The Rift\nRoutine backstory.\n\n"
        "## Planned Invasion\nAlaxya prepares an invasion of Exandria "
        "through the rift.\n",
    )
    # a group file also under data/lore -> must be searchable too
    _write(
        s.group_lore_dir / "The Wolf Pack_ Players.md",
        "# Wolf Pack\n\n## Echo\nCursed by the hag.\n",
    )

    out = lore.lore_search_impl("invasion of Exandria")
    assert "Planned Invasion" in out
    assert "invasion of Exandria" in out
    # citation points at the file + heading
    assert "HISTORY OF ALAXYA.md" in out


def test_lore_search_returns_sections_not_whole_huge_file() -> None:
    s = get_settings()
    big = "# Deities\n\n" + "".join(
        f"## Deity {i}\n" + ("filler word " * 200) + "\n\n" for i in range(200)
    )
    # inject one relevant section
    big += "## Bwonsamdi\nGod of death, deal-maker, loa.\n"
    _write(s.alexya_lore_dir / "Deities.md", big)

    out = lore.lore_search_impl("Bwonsamdi deal-maker")
    assert "Bwonsamdi" in out
    # section-scoped: far smaller than the whole multi-section file
    assert len(out) < len(big)


def test_lore_search_reports_no_match_not_empty() -> None:
    s = get_settings()
    _write(s.alexya_lore_dir / "Deities.md", "# Deities\n\nBahamut.\n")
    out = lore.lore_search_impl("zzzznonexistentkeyword")
    assert "No lore section matched" in out
    assert "empty" not in out.lower()


def test_lore_search_ignores_embedded_base64() -> None:
    s = get_settings()
    blob = "Q" * 6000
    _write(
        s.alexya_lore_dir / "Deities.md",
        f"# Deities\n\n## Bahamut\nThe platinum dragon.\n\n"
        f"[image1]: <data:image/png;base64,{blob}>\n",
    )
    out = lore.lore_search_impl("Bahamut platinum dragon")
    assert "platinum dragon" in out
    # the base64 blob must never leak into the returned context
    assert "base64" not in out and blob not in out
