# LLM Dungeon Crawler

A text-based RPG dungeon crawler where the game engine handles the mechanics (stats, items, combat) and an LLM provides atmospheric descriptions and NPC dialogue.

The game uses **Ollama** and the **Gemma 4** model (by default) locally to generate rich, "Dark Fantasy" storytelling as you explore a procedurally generated dungeon. You can also specify other local models using the `--model` flag.

## Requirements

Before you can play, you need the following installed on your host machine:

1. **[uv](https://docs.astral.sh/uv/)** (Python package manager)
2. **[Ollama](https://ollama.com/)** (for running the local LLM)

## Setup & Running the Game

1. **Install and Pull the Model**
   Ensure Ollama is installed, then pull the default Gemma 4 model (or any other compatible model you wish to use):

   ```bash
   ollama pull gemma4:e4b
   ```

2. **Play!**
   Launch the game directly on your host machine. The game will automatically start the Ollama server for you if it isn't already running:

   ```bash
   uv run dungeon-crawler
   ```

   **Using a Custom Model:**
   You can specify a different model using the `--model` flag (ensure you have pulled it via `ollama pull <model_name>` first):

   ```bash
   uv run dungeon-crawler --model llama3
   ```

## Gameplay Controls

Once the game starts, you interact via text commands:

- **Movement:** `go north`, `go south`, `go east`, `go west`
- **Combat:** `attack <enemy_name>`
- **Interaction:** `talk <npc_name>`
- **Items:** `take <item_name>`, `use <item_name>`, `equip <weapon_name>`, `unequip`
- **Information:** `look` (describe room again), `status` or `inventory` (check health/items)
- **Other:** `help`, `quit`
