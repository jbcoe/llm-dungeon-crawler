# Development Guide

This document outlines how to develop and contribute to `llm-dungeon-crawler`.

## Architecture: The Dual-LLM Setup

This project uses two different AI systems for distinct purposes:

1. **Ollama (Local)**: Powers the game's actual runtime (NPC dialogue, room descriptions).
2. **Gemini or Claude (Cloud)**: Powers the **Agentic Development Workflow** via the Gemini CLI or Claude Code to help write code, fix bugs, and refactor.

## Agentic Development Workflow

To work on this codebase using AI assistance, you should use the provided Docker sandbox. This keeps your host machine clean while giving the agent CLI full access to the project. Both **Gemini CLI** and **Claude Code** are supported.

### Gemini

```bash
./scripts/agentic-sandbox.sh gemini
```

*Gemini CLI starts automatically inside the container.*

### Claude

```bash
./scripts/agentic-sandbox.sh claude
```

*Claude Code starts automatically in YOLO mode (`--dangerously-skip-permissions`), which is safe inside the isolated container.*

### Options

Both agents accept the following flags:

| Flag               | Description                                                |
| ------------------ | ---------------------------------------------------------- |
| `--rebuild-docker` | Rebuild the Docker image before launching.                 |
| `--update`         | Update the agent CLI to the latest version before running. |
| `-v` / `--verbose` | Enable verbose logging.                                    |

## Non-Coding Development (Content Creation)

The game is designed to be easily expanded by non-programmers. All flavor text, entities, environments, and core AI prompts are data-driven and can be updated without touching any Python code.

All content is stored in the `themes/` directory. Each theme is a self-contained folder (e.g., `themes/dark-fantasy/`) containing:

1. **Entities and Environments:**
   Lists of available enemies, items, NPCs, and rooms are defined in markdown files: `enemies.md`, `items.md`, `npcs.md`, and `rooms.md`. To add new content, add a new line following the established `- Name: Description` format.

2. **AI Prompts:**
   All instructions sent to the Ollama LLM are stored as prompt templates in the `prompts/` subdirectory (e.g., `prompts/room.md`, `prompts/combat.md`). These files control the tone, style, and rules the AI follows.

   - The engine uses variables wrapped in curly braces (e.g., `{enemy_name}`). When modifying the prompt text, ensure these variables are kept intact.
   - **Important:** If you need to use literal curly braces in your prompt, you must escape them by doubling them up like `{{` and `}}`.

To create a new theme, copy an existing one (like `themes/dark-fantasy`) to a new folder in `themes/` and modify the files. You can then play it using:

```bash
uv run dungeon-crawler --theme my-new-theme
```

## Working with the Code

The codebase is structured to separate deterministic mechanics from LLM flavor:

- `game/mechanics.py`: Handles all stats, logic, and procedural generation based on thematic data.
- `themes/`: Root directory for all game settings. Add new themes here!
- `game/theme.py`: Defines the `Theme` data model and strict validation logic.
- `game/ai.py`: Connects to Ollama to generate atmospheric text based on theme prompts.
- `game/engine.py`: The core game loop, state management, and command parser.

## Running Tests

The project uses `pytest`. AI API calls are mocked globally in `tests/conftest.py` so tests are fast, deterministic, and don't require an active Ollama server.

To run the test suite:

```bash
uv run pytest
```

To run tests with verbose output:

```bash
uv run pytest -v
```

## Linting and Formatting

The project uses `ruff` for fast linting and formatting, alongside `pre-commit` hooks.

**Run the Linter:**

```bash
uv run ruff check .
```

**Run the Formatter:**

```bash
uv run ruff format .
```

*(Optional)* **Set up Pre-commit Hooks** so linting runs automatically before you commit:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```
