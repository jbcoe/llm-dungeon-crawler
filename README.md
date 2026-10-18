# LLM Dungeon Crawler

A text-based RPG dungeon crawler where the game engine handles the mechanics (stats, items, combat) and an LLM provides atmospheric descriptions and NPC dialogue.

The game uses **Ollama** locally by default, or any **OpenAI-compatible API** such as vLLM, to generate rich, "Dark Fantasy" storytelling as you explore a procedurally generated dungeon. You can select a model with `--model` and choose the inference protocol with `--backend`.

## Requirements

You need **[uv](https://docs.astral.sh/uv/)** (Python package manager) and one of these inference backends:

1. **[Ollama](https://ollama.com/)** running locally (the default), or
2. An **OpenAI-compatible API** such as vLLM, reachable over HTTP(S).

## Setup & Running the Game

### Ollama (default)

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

### OpenAI-compatible API (vLLM and similar servers)

Point the game at a server that implements the OpenAI `/v1/models` and
`/v1/chat/completions` endpoints:

```bash
uv run dungeon-crawler \
  --backend openai \
  --base-url http://your-model-server:8000/v1 \
  --model your-served-model
```

For an authenticated API, put the key in the standard environment variable. The
command line intentionally does not accept API keys because process arguments and
shell history may be visible to other users:

```bash
export OPENAI_API_KEY='your-key'
uv run dungeon-crawler --backend openai --base-url https://example.com/v1 --model model-id
```

The game checks server connectivity and model availability before starting. Only use
plain HTTP on a trusted private network; use HTTPS when crossing an untrusted network.

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

| Option                                      | Default        | Description                                                                                                               |
| ------------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `--backend <name>`                          | `ollama`       | Inference protocol (`ollama` or `openai`). Use `openai` for vLLM and other OpenAI-compatible servers.                     |
| `--base-url <url>`                          | —              | OpenAI-compatible API root including `/v1`; required for the `openai` backend.                                            |
| `--model <name>`                            | `gemma4:e4b`   | Model ID used for generation. Ollama users must pull it first; remote users must select an ID advertised by `/v1/models`. |
| `--size <n>`                                | `8`            | Width/height of the pre-generated dungeon map (minimum 3).                                                                |
| `--history-length <n>`                      | `1000`         | Maximum commands retained in readline history; `0` disables history.                                                      |
| `--experimental-max-loading-time <seconds>` | `0` (disabled) | **Experimental.** Random delay up to this duration between room transitions.                                              |

Example — launch with a smaller model on a map of 12×12:

```bash
uv run dungeon-crawler --model llama3 --size 12
```
