"""Command line interface and entry point logic."""

import argparse
import json
import os
import sys
from urllib.request import Request

import ollama
from rich.console import Console

from game.ai import AIGenerator, safe_urlopen
from game.engine import GameEngine
from game.utils import get_model_name, models_match

console = Console()


def check_ollama_connection(required_model: str = "gemma4:e4b") -> None:
    """Verify that Ollama is running and the required model is available."""
    try:
        response = ollama.list()
        # Support both older dict responses and newer object responses
        # from the ollama library
        models_list = (
            response.models
            if hasattr(response, "models")
            else response.get("models", [])
        )

        model_names: list[str] = [get_model_name(m) for m in models_list]

        model_found = any(models_match(required_model, name) for name in model_names)

        if not model_found:
            console.print(
                f"[bold red]ERROR: Model '{required_model}' "
                "not found in Ollama.[/bold red]"
            )
            console.print(
                f"Please run [bold]ollama pull {required_model}[/bold] "
                "on your machine and try again."
            )
            sys.exit(1)

    except Exception as e:
        console.print("[bold red]ERROR: Could not connect to Ollama server.[/bold red]")
        console.print(f"Details: {e}")
        console.print("\n[bold]Troubleshooting:[/bold]")
        console.print(
            "1. Ensure Ollama is installed and running on your system "
            "(e.g., run `ollama serve`)."
        )
        console.print(
            "2. If running inside a Docker container, ensure OLLAMA_HOST "
            "is correctly set to point to your host machine."
        )
        sys.exit(1)


def check_openai_connection(
    base_url: str, required_model: str, api_key: str | None
) -> None:
    """Verify an OpenAI-compatible endpoint and required model are available."""
    normalized_url = base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    request = Request(f"{normalized_url}/models", headers=headers)
    try:
        with safe_urlopen(request, timeout=10) as response:
            response_data = json.loads(response.read())
        model_names = [model.get("id", "") for model in response_data.get("data", [])]
        if required_model not in model_names:
            console.print(
                f"[bold red]ERROR: Model '{required_model}' was not advertised by "
                f"{normalized_url}.[/bold red]"
            )
            console.print(f"Available models: {', '.join(model_names) or 'none'}")
            sys.exit(1)
    except Exception as e:
        console.print(
            "[bold red]ERROR: Could not connect to the OpenAI-compatible "
            "server.[/bold red]"
        )
        console.print(f"Details: {e}")
        sys.exit(1)


def check_history_length(value: str) -> int:
    """Validate that the history length is a non-negative integer."""
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError(
            f"{value} is an invalid non-negative integer value"
        )
    return ivalue


def check_map_size(value: str) -> int:
    """Validate that the map size is at least 3."""
    ivalue = int(value)
    if ivalue < 3:
        raise argparse.ArgumentTypeError(f"{value} is an invalid map size (min: 3)")
    return ivalue


def main() -> None:
    """Parse arguments and start the game engine."""
    parser = argparse.ArgumentParser(description="LLM Dungeon Crawler")
    parser.add_argument(
        "--backend",
        choices=("ollama", "openai"),
        default="ollama",
        help="Inference backend to use (default: ollama)",
    )
    parser.add_argument(
        "--base-url",
        help="Base URL for an OpenAI-compatible API, including /v1",
    )
    parser.add_argument(
        "--history-length",
        type=check_history_length,
        default=1000,
        help="Maximum number of commands to keep in history (default: 1000)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemma4:e4b",
        help="The model ID to use for the game (default: gemma4:e4b)",
    )
    parser.add_argument(
        "--size",
        type=check_map_size,
        default=8,
        help="The size of the pre-generated dungeon map (default: 8)",
    )
    parser.add_argument(
        "--experimental-max-loading-time",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help=(
            "Experimental: maximum random loading time in seconds between "
            "room transitions (default: 0, disabled). Gives the game a retro feel."
        ),
    )
    args = parser.parse_args()

    if args.backend == "ollama":
        with AIGenerator.manage_ollama(args.model):
            check_ollama_connection(args.model)
            engine = GameEngine(
                max_history=args.history_length,
                model=args.model,
                map_size=args.size,
                max_loading_time=args.experimental_max_loading_time,
            )
            engine.start()
    else:
        if not args.base_url:
            parser.error("--base-url is required when --backend=openai")
        api_key = os.environ.get("OPENAI_API_KEY")
        check_openai_connection(args.base_url, args.model, api_key)
        ai_generator = AIGenerator(
            model=args.model,
            backend="openai",
            base_url=args.base_url,
            api_key=api_key,
        )
        engine = GameEngine(
            max_history=args.history_length,
            model=args.model,
            ai_generator=ai_generator,
            map_size=args.size,
            max_loading_time=args.experimental_max_loading_time,
        )
        engine.start()


if __name__ == "__main__":
    main()
