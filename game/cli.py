import sys
import argparse
import ollama
from rich.console import Console
from game.engine import GameEngine

console = Console()


def check_ollama_connection():
    try:
        response = ollama.list()
        # Support both older dict responses and newer object responses from the ollama library
        models_list = (
            response.models
            if hasattr(response, "models")
            else response.get("models", [])
        )

        model_names = []
        for m in models_list:
            if hasattr(m, "model"):
                model_names.append(m.model)
            elif isinstance(m, dict):
                model_names.append(m.get("model") or m.get("name"))

        required_model = "gemma4:e4b"
        if required_model not in model_names:
            console.print(
                f"[bold red]ERROR: Model '{required_model}' not found in Ollama.[/bold red]"
            )
            console.print(
                f"Please run [bold]ollama pull {required_model}[/bold] on your machine and try again."
            )
            sys.exit(1)

    except Exception as e:
        console.print("[bold red]ERROR: Could not connect to Ollama server.[/bold red]")
        console.print(f"Details: {e}")
        console.print("\n[bold]Troubleshooting:[/bold]")
        console.print(
            "1. Ensure Ollama is installed and running on your system (e.g., run `ollama serve`)."
        )
        console.print(
            "2. If running inside a Docker container, ensure OLLAMA_HOST is correctly set to point to your host machine."
        )
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="LLM Dungeon Crawler")
    parser.add_argument(
        "--history-length",
        type=int,
        default=1000,
        help="Maximum number of commands to keep in history (default: 1000)",
    )
    args = parser.parse_args()

    check_ollama_connection()
    engine = GameEngine(max_history=args.history_length)
    engine.start()


if __name__ == "__main__":
    main()
