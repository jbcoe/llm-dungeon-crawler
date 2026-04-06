# Development Guide

This document outlines how to develop and contribute to `llm-dungeon-crawler`.

## Architecture: The Dual-LLM Setup

This project uses two different AI systems for distinct purposes:
1. **Ollama (Local)**: Powers the game's actual runtime (NPC dialogue, room descriptions).
2. **Gemini (Cloud)**: Powers the **Agentic Development Workflow** via the Gemini CLI to help write code, fix bugs, and refactor.

## Agentic Development Workflow

To work on this codebase using AI assistance, you should use the provided Docker sandbox. This keeps your host machine clean while giving the Gemini CLI full access to the project.

1. **Set your API Key** on your host machine:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```
2. **Launch the Sandbox**:
   ```bash
   ./scripts/gemini-sandbox.sh
   ```
   *This script mounts your local workspace, passes your Gemini API key, and sets up host networking so the game can still reach your local Ollama instance.*

3. **Start the Agent**:
   Once inside the container, simply run:
   ```bash
   gemini
   ```
   You can now ask the agent to implement features, run tests, or debug code.

## Working with the Code

The codebase is structured to separate deterministic mechanics from LLM flavor:
- `game/mechanics.py`: Handles all stats, logic, and procedural generation based on tables.
- `data/*.md`: Markdown lists containing definitions for enemies, items, NPCs, and rooms. Add new content here!
- `game/ai.py`: Connects to Ollama to generate atmospheric text based on the mechanics output.
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
