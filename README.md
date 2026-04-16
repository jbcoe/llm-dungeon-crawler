# LLM Dungeon Crawler

A text-based RPG dungeon crawler where the game engine handles the mechanics (stats, items, combat) and an LLM provides atmospheric descriptions and NPC dialogue.

The game uses **Ollama** and the **Gemma 4** model (by default) to generate rich, "Dark Fantasy" storytelling as you explore a procedurally generated dungeon. You can run the model locally on your machine, or connect to a [hosted Ollama instance](CLOUD_SETUP.md) on Google Cloud.

## Requirements

Before you can play, you need the following installed on your host machine:

1. **[uv](https://docs.astral.sh/uv/)** (Python package manager)
2. **[Ollama](https://ollama.com/)** (for running the LLM — local play only)

## Setup & Running the Game

### Option A — Local play (no internet required after setup)

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

### Option B — Cloud play (connects to a hosted Ollama server)

If you (or a friend) have set up an Ollama server on Google Cloud, you can connect without installing Ollama locally at all:

```bash
uv run dungeon-crawler --ollama-url http://<SERVER_IP>:11434
```

You can also combine this with a custom model:

```bash
uv run dungeon-crawler --ollama-url http://<SERVER_IP>:11434 --model llama3
```

Alternatively, set the `OLLAMA_HOST` environment variable instead of using `--ollama-url`:

```bash
export OLLAMA_HOST=http://<SERVER_IP>:11434
uv run dungeon-crawler
```

See [CLOUD_SETUP.md](CLOUD_SETUP.md) for step-by-step instructions on setting up a Gemma 4 server on Google Cloud Compute Engine, including cost estimates and security guidance.

## Gameplay Controls

Once the game starts, you interact via text commands:

- **Movement:** `go north`, `go south`, `go east`, `go west`
- **Combat:** `attack <enemy_name>`
- **Interaction:** `talk <npc_name>`
- **Items:** `take <item_name>`, `use <item_name>`, `equip <weapon_name>`, `unequip`
- **Information:** `look` (describe room again), `status` or `inventory` (check health/items)
- **Other:** `help`, `quit`
