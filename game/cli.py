"""Command line interface and entry point logic."""

import argparse
import sys

import ollama
from rich.console import Console

from game.ai import AIGenerator
from game.engine import GameEngine

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

        model_names: list[str] = []
        for m in models_list:
            if hasattr(m, "model"):
                model_names.append(str(m.model))
            elif isinstance(m, dict):
                model_names.append(str(m.get("model") or m.get("name") or ""))

        # Normalize comparison: if a model is 'name:latest', it can be matched by 'name'
        # and vice-versa.
        model_found = required_model in model_names
        if not model_found:
            if ":" not in required_model:
                model_found = f"{required_model}:latest" in model_names
            elif required_model.endswith(":latest"):
                model_found = required_model[: -len(":latest")] in model_names

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
    args = parser.parse_args()

    with AIGenerator.manage_ollama(args.model):
        check_ollama_connection(args.model)
        engine = GameEngine(max_history=args.history_length, model=args.model)
        engine.start()


if __name__ == "__main__":
    main()
