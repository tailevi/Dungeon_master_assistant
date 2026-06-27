# DM Helper

Single-user Dungeon Master assistant for Mayan. Orchestrator agent + function tools + Writer + Instructor judge loop + confirmation-gated Kanka writes. Anthropic Claude only (routed through LiteLLM); Kanka REST for canonical campaign data; whole-file lore lookup (no RAG).

## Stack

- Python 3.11+, managed with [uv](https://docs.astral.sh/uv/)
- `openai-agents[litellm]` for the agent framework and `SQLiteSession`
- `anthropic` SDK for the native `web_search` server tool
- `gradio` for the local chat UI
- `httpx` + `tenacity` for the Kanka client (429-aware)
- `pydantic` + `pydantic-settings` for typed config and changeset validation
- `python-frontmatter` for tagging Alexya lore by category

Tracing is disabled at import (`set_tracing_disabled(True)` in `dmhelper/__init__.py`) because there is no OpenAI key in this project.

## Setup

```bash
uv sync --all-extras
cp .env.example .env
# fill in ANTHROPIC_API_KEY, KANKA_API_TOKEN, KANKA_CAMPAIGN_ID
```

Web search requires `web_search` to be enabled for your Anthropic organisation in the Claude Console (Privacy settings).

## Run

```bash
uv run python app.py
```

Gradio launches on `http://127.0.0.1:7860`. Pick a group from the dropdown. **New chat** starts a fresh `SQLiteSession` for that group.

## How a turn flows

1. Orchestrator Agent (Claude Opus) sees the message, loads the rolling memory for the active group, decides which tools to call. Tools: `lore_search`, `web_search`, `kanka_player_search`, `memory_read`, `memory_write`, `propose_changeset`.
2. Orchestrator output is fed to the **Writer Agent** (Claude Opus, no tools), which polishes it for Mayan.
3. If `DMHELPER_JUDGE_ENABLED=true` (default), the **Instructor judge** (Claude Sonnet) reviews the Writer draft against `prompts/instructions.md`. On `REJECT`, the Writer re-runs with the critique. Max 2 judge iterations.
4. If the user message is `/confirm`, the orchestrator is skipped and the queued Kanka changeset is applied.

## Kanka write gate

The orchestrator can call `propose_changeset(group_id, chat_id, items_json)` which queues edits in `data/store.db` (`pending_changes` table) and prints a summary ending with `Reply "/confirm" to save`. **Nothing is written to Kanka** until the user replies `/confirm` in the same chat.

On `/confirm`, the book-keeper:

1. For each item, looks up `(group_id, local_key)` in `kanka_id_map`. If a row exists, it issues `PUT /<entity_type>/<id>` directly (no search).
2. Otherwise searches Kanka by name; if an exact match is found, updates it and caches the id.
3. Otherwise creates a new entity and caches the id.
4. Appends a `## /confirm <timestamp>` block to `data/memory/memory_<group>.md`.

## Tests

```bash
uv run pytest
```

`tests/` covers the Kanka client (search/list/create plus 429 backoff and give-up), the memory tool, the verdict parser, and the write gate (unconfirmed writes are blocked, search-before-write dedupes, cached id short-circuits a second `/confirm`, memory file is appended).

## Layout

```
app.py
src/dmhelper/
    config.py
    orchestrator.py
    agents/{writer.py, instructor.py}
    tools/{lore.py, web.py, kanka_search.py, kanka_write.py, memory.py}
    clients/kanka.py
    store/db.py
data/
    lore/          # Alexya homebrew .md (frontmatter `category`, `world`)
    memory/        # rolling memory_<group>.md
prompts/
    orchestrator.md
    writer.md
    instructor.md
    instructions.md
tests/
```

## Environment

| Variable                       | Default                          | Purpose                                                  |
| ------------------------------ | -------------------------------- | -------------------------------------------------------- |
| `ANTHROPIC_API_KEY`            | —                                | Routed to every Claude call via LiteLLM.                 |
| `KANKA_API_TOKEN`              | —                                | Bearer token for `api.kanka.io`.                         |
| `KANKA_CAMPAIGN_ID`            | —                                | Campaign id scope for all Kanka requests.                |
| `DMHELPER_ORCHESTRATOR_MODEL`  | `anthropic/claude-opus-4-8`      | LiteLLM model string for the Orchestrator.               |
| `DMHELPER_WRITER_MODEL`        | `anthropic/claude-opus-4-8`      | LiteLLM model string for the Writer.                     |
| `DMHELPER_JUDGE_MODEL`         | `anthropic/claude-sonnet-4-6`    | LiteLLM model string for the Instructor judge.           |
| `DMHELPER_WEB_MODEL`           | `claude-sonnet-4-6`              | Native Anthropic model id for `web_search`.              |
| `DMHELPER_JUDGE_ENABLED`       | `true`                           | Set to `false` to skip the judge loop.                   |
| `DMHELPER_DATA_DIR`            | `data`                           | Base dir for lore, memory, SQLite stores.                |
