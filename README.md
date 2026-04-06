# LLM Dungeon Crawler

A text-based RPG dungeon crawler where the game engine handles the mechanics (stats, items, combat) and an LLM provides atmospheric descriptions and NPC dialogue.

The game uses **Ollama** and the **Gemma 4** model locally to generate rich, "Dark Fantasy" storytelling as you explore a procedurally generated dungeon.

## Requirements

Before you can play, you need the following installed on your host machine:

1. **Python 3.12+**
2. **uv** (Python package installer and resolver)
3. **Docker** (for running the sandboxed development environment)
4. **Ollama** (for running the local LLM)

## Setup & Running the Game

1. **Start Ollama**
   Ensure Ollama is running on your host machine:
   ```bash
   ollama serve
   ```

2. **Pull the Model**
   Pull the required Gemma 4 model (the game expects `gemma4:e4b`):
   ```bash
   ollama pull gemma4:e4b
   ```

3. **Launch the Game Sandbox**
   To ensure a clean environment, launch the game inside its Docker sandbox:
   ```bash
   ./scripts/gemini-sandbox.sh
   ```
   *Note: This sandbox uses the host network to communicate with your local Ollama instance.*

4. **Play!**
   Once inside the sandbox, start the game engine:
   ```bash
   uv run main.py
   ```

## Gameplay Controls

Once the game starts, you interact via text commands:

- **Movement:** `go north`, `go south`, `go east`, `go west`
- **Combat:** `attack <enemy_name>`
- **Interaction:** `talk <npc_name>`
- **Items:** `take <item_name>`, `use <item_name>`, `equip <weapon_name>`, `unequip`
- **Information:** `look` (describe room again), `status` or `inventory` (check health/items)
- **Other:** `help`, `quit`
