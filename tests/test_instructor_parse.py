from __future__ import annotations

from dmhelper.agents.instructor import parse_verdict


def test_approved_single_word() -> None:
    v = parse_verdict("APPROVED")
    assert v.approved is True
    assert v.critique == ""


def test_approved_with_trailing_noise() -> None:
    v = parse_verdict("APPROVED  \n")
    assert v.approved is True


def test_reject_collects_critique_body() -> None:
    v = parse_verdict(
        "REJECT\n1. Missing citation for 'the cult'.\n2. Bleed: Exandria deity in Alexya answer."
    )
    assert v.approved is False
    assert "Missing citation" in v.critique
    assert "Bleed" in v.critique


def test_unparseable_text_treated_as_reject() -> None:
    v = parse_verdict("looks fine to me")
    assert v.approved is False
    assert "looks fine" in v.critique


def test_empty_string_is_rejection_with_empty_critique() -> None:
    v = parse_verdict("")
    assert v.approved is False
    assert v.critique == ""
