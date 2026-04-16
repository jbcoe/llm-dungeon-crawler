# LLM Dungeon Crawler

A text-based RPG dungeon crawler where the game engine handles the mechanics (stats, items, combat) and an LLM provides atmospheric descriptions and NPC dialogue.

The game uses **llama-server** (from [llama.cpp](https://github.com/ggerganov/llama.cpp)) locally to generate rich, "Dark Fantasy" storytelling as you explore a procedurally generated dungeon. Any model served via llama-server's OpenAI-compatible API works out of the box.

## Requirements

Before you can play, you need the following installed on your host machine:

1. **[uv](https://docs.astral.sh/uv/)** (Python package manager)
2. **[llama-server](https://github.com/ggerganov/llama.cpp)** (for running the local LLM)

## Setup & Running the Game

1. **Download a model and start llama-server**
   Download any GGUF model (e.g. from [Hugging Face](https://huggingface.co/)) and start the server:

   ```bash
   llama-server --model your_model.gguf --port 8080
   ```

   The server exposes an OpenAI-compatible API at `http://localhost:8080` by default.

2. **Play!**
   Launch the game on your host machine:

   ```bash
   uv run dungeon-crawler
   ```

   **Using a different server address:**
   If your llama-server runs on a different host or port, use `--server-url`:

   ```bash
   uv run dungeon-crawler --server-url http://192.168.1.10:8080
   ```

   **Using a specific model alias:**
   If you started llama-server with `--alias mymodel`, pass it via `--model`:

   ```bash
   uv run dungeon-crawler --model mymodel
   ```

## Gameplay Controls

Once the game starts, you interact via text commands:

- **Movement:** `go north`, `go south`, `go east`, `go west`
- **Combat:** `attack <enemy_name>`
- **Interaction:** `talk <npc_name>`
- **Items:** `take <item_name>`, `use <item_name>`, `equip <weapon_name>`, `unequip`
- **Information:** `look` (describe room again), `status` or `inventory` (check health/items)
- **Other:** `help`, `quit`
