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
- **Rest:** `rest` — recover 20% of your max HP (minimum 5 HP). You cannot rest while enemies are present. Repeated resting in the same room increases the chance of an enemy spawning, so use it wisely.
- **Other:** `help`, `quit`

## Command-Line Options

| Option                                      | Default        | Description                                                                                                                                                                                                                                                                                                         |
| ------------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--model <name>`                            | `gemma4:e4b`   | The Ollama model used to generate narrative text. Smaller models load faster and use less memory but may produce lower-quality descriptions. Larger or more capable models give richer storytelling at the cost of slower responses. Make sure you have pulled the model via `ollama pull <name>` before launching. |
| `--size <n>`                                | `8`            | The width/height of the pre-generated dungeon map (minimum 3). Larger maps mean more rooms to explore but take slightly longer to generate at start-up.                                                                                                                                                             |
| `--history-length <n>`                      | `1000`         | Maximum number of commands retained in the readline history. Set to `0` to disable history. Reducing this value may help in memory-constrained environments.                                                                                                                                                        |
| `--experimental-max-loading-time <seconds>` | `0` (disabled) | **Experimental.** Adds a random delay of up to the given number of seconds between room transitions, simulating the feel of a retro game loading screen. Has no effect on gameplay beyond pacing.                                                                                                                   |

Example — launch with a smaller model on a map of 12×12:

```bash
uv run dungeon-crawler --model llama3 --size 12
```
