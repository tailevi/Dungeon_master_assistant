"""Build a Matt Mercer narration / storytelling / dialogue guide.

`build_narration_guide` fetches a few episode transcripts from the Critical
Role fandom wiki and asks Claude to distil a reusable "narrate by example"
guide centred on **Matt Mercer's** narration cadence, storytelling drive, and
dialogue delivery. It writes the guide to `data/instructions/narration_style.md`.
From there the existing `format_standards.load_format_standards()` feeds it to
BOTH the Writer (to comply) and the Instructor (to enforce) whenever Mayan
writes or finalizes a story.

On-demand: run it once to set up the storytelling voice, refresh occasionally.
The transcripts (Exandria / Critical Role) are used as a STYLE exemplar only —
the guide must never become a source of Alaxya canon.
"""

from __future__ import annotations

from functools import lru_cache

from agents import function_tool
from anthropic import AsyncAnthropic

from dmhelper.clients.criticalrole import CriticalRoleClient
from dmhelper.config import get_settings

GUIDE_FILENAME = "narration_style.md"

_DISTILL_PROMPT = """\
You are a writing coach for a Dungeon Master. Below are excerpts from Critical \
Role session transcripts, narrated by Matt Mercer. Produce a reusable guide \
titled around MATT MERCER'S NARRATION, STORYTELLING & DIALOGUE that teaches how \
to narrate and run a D&D story in his style, BY EXAMPLE.

Organise the guide around these three core pillars first, each with short \
illustrative quotes drawn from the excerpts (attribute them as \
"Critical Role / Matt Mercer"):

1. NARRATION — Matt Mercer's cadence and rhythm: measured pacing, deliberate \
   pauses, immersive second person ("You see...", "You feel..."), slow builds \
   that crescendo, and vivid, specific sensory imagery.
2. STORYTELLING DRIVE — the momentum that pushes every scene forward: rising \
   stakes and tension, clean dramatic beats, evocative scene transitions, \
   cliffhangers, and the signature handoff of agency back to the players \
   ("What do you do?").
3. DIALOGUE — distinct NPC voices: differentiated accents, registers, verbal \
   tics and speech rhythms, fully in-character delivery, and clear framing of \
   read-aloud / in-character speech versus out-of-character table talk.

After the three pillars, add a short "Putting it together" section with a brief \
worked example showing the cadence, drive, and dialogue in one passage.

Output GitHub-flavored markdown. Begin with an H1 title that names Matt Mercer. \
Keep quotes short (a sentence or two each) and clearly attributed.

CRITICAL CONSTRAINT: this guide teaches STYLE ONLY — cadence, drive, and \
dialogue craft. State explicitly near the top that it must NOT be used as a \
source of canon for the homebrew world Alaxya, and that Exandria / Critical \
Role facts, names, and places must never be imported into Alaxya.

Transcript excerpts:
{excerpts}
"""


@lru_cache(maxsize=1)
def _anthropic() -> AsyncAnthropic:
    settings = get_settings()
    return AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value())


def _extract_text(blocks: list[object]) -> str:
    parts: list[str] = []
    for block in blocks:
        text = getattr(block, "text", None)
        if isinstance(text, str) and text.strip():
            parts.append(text)
    return "\n\n".join(parts).strip()


async def build_narration_guide_impl(
    episodes: int = 0, titles: str | None = None
) -> str:
    """Plain-coroutine form of build_narration_guide (used by tests + tool).

    Distils Matt Mercer's narration cadence, storytelling drive, and dialogue
    from sampled Critical Role transcripts into the narration style guide.
    """
    settings = get_settings()
    sample = episodes if episodes and episodes > 0 else settings.narration_sample

    async with CriticalRoleClient() as client:
        if titles:
            chosen = [t.strip() for t in titles.split(",") if t.strip()]
        else:
            chosen = await client.list_transcript_titles(limit=sample)
        if not chosen:
            return (
                "Could not find any Critical Role transcript pages to sample. "
                "Try passing explicit `titles`."
            )

        excerpt_blocks: list[str] = []
        used: list[str] = []
        for title in chosen[:sample]:
            try:
                text = await client.get_transcript_text(title)
            except Exception as e:  # noqa: BLE001 - skip a bad page, keep going
                excerpt_blocks.append(f"### {title}\n(could not fetch: {e})")
                continue
            if not text:
                continue
            used.append(title)
            excerpt_blocks.append(
                f"### {title}\n{text[: settings.narration_excerpt_chars]}"
            )

    if not used:
        return "Fetched transcript pages were empty; nothing to distil."

    prompt = _DISTILL_PROMPT.format(excerpts="\n\n".join(excerpt_blocks))
    response = await _anthropic().messages.create(
        model=settings.narration_model,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    guide = _extract_text(list(response.content))
    if not guide:
        return "The model returned no guide text; nothing was written."

    settings.instructions_dir.mkdir(parents=True, exist_ok=True)
    path = settings.instructions_dir / GUIDE_FILENAME
    path.write_text(guide, encoding="utf-8")

    return (
        f"Wrote Matt Mercer narration / storytelling / dialogue guide to {path} "
        f"(distilled from {len(used)} transcript(s): {', '.join(used)}). "
        "It will now guide the Writer and be enforced by the Instructor when "
        "you write or finalize a story."
    )


@function_tool
async def build_narration_guide(
    episodes: int = 0, titles: str | None = None
) -> str:
    """Build/refresh a Matt Mercer storytelling guide from Critical Role
    transcripts and save it to data/instructions/narration_style.md.

    Learns Matt Mercer's narration cadence, storytelling drive, and NPC
    dialogue delivery. Run this once to set up the story-narration voice (or to
    refresh it). The saved guide is automatically applied by the Writer and
    enforced by the Instructor when you write or finalize a story. The
    transcripts are used as a STYLE example only - never as Alaxya canon.

    Args:
        episodes: how many transcripts to sample (default: configured value).
        titles: optional comma-separated transcript page titles to use instead
            of auto-picking from the Transcripts index.
    """
    return await build_narration_guide_impl(episodes=episodes, titles=titles)
