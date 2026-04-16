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
- **Rest:** `rest` — recover 20% of your max HP (minimum 5 HP). You cannot rest while enemies are present. Repeated resting in the same room increases the chance of an enemy spawning, so use it wisely.
- **Other:** `help`, `quit`

## Command-Line Options

| Option | Default | Description |
|---|---|---|
| `--model <name>` | `gemma4:e4b` | The Ollama model used to generate narrative text. Smaller models load faster and use less memory but may produce lower-quality descriptions. Larger or more capable models give richer storytelling at the cost of slower responses. Make sure you have pulled the model via `ollama pull <name>` before launching. |
| `--size <n>` | `8` | The width/height of the pre-generated dungeon map (minimum 3). Larger maps mean more rooms to explore but take slightly longer to generate at start-up. |
| `--history-length <n>` | `1000` | Maximum number of commands retained in the readline history. Set to `0` to disable history. Reducing this value may help in memory-constrained environments. |
| `--experimental-max-loading-time <seconds>` | `0` (disabled) | **Experimental.** Adds a random delay of up to the given number of seconds between room transitions, simulating the feel of a retro game loading screen. Has no effect on gameplay beyond pacing. |

Example — launch with a smaller model on a map of 12×12:

```bash
uv run dungeon-crawler --model llama3 --size 12
```
