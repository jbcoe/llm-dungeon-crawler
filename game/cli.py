"""Command line interface and entry point logic."""

import argparse
import sys

import ollama
from rich.console import Console

from game.ai import AIGenerator
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
        "--history-length",
        type=check_history_length,
        default=1000,
        help="Maximum number of commands to keep in history (default: 1000)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemma4:e4b",
        help="The Ollama model to use for the game (default: gemma4:e4b)",
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

    with AIGenerator.manage_ollama(args.model):
        check_ollama_connection(args.model)
        engine = GameEngine(
            max_history=args.history_length,
            model=args.model,
            map_size=args.size,
            max_loading_time=args.experimental_max_loading_time,
        )
        engine.start()


if __name__ == "__main__":
    main()
