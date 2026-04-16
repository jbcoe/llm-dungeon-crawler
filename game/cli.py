"""Command line interface and entry point logic."""

import argparse
import sys

from openai import OpenAI
from rich.console import Console

from game.ai import DEFAULT_LLAMA_SERVER_URL
from game.engine import GameEngine

console = Console()


def check_llama_server_connection(
    server_url: str = DEFAULT_LLAMA_SERVER_URL,
) -> None:
    """Verify that llama-server is running and accessible."""
    client = OpenAI(base_url=server_url.rstrip("/") + "/v1", api_key="not-needed")
    try:
        client.models.list()
    except Exception as e:
        console.print("[bold red]ERROR: Could not connect to llama-server.[/bold red]")
        console.print(f"Details: {e}")
        console.print("\n[bold]Troubleshooting:[/bold]")
        console.print(
            "1. Ensure llama-server is installed and running "
            "(e.g., run `llama-server --model your_model.gguf`)."
        )
        console.print(
            f"2. If the server is running on a different address, use "
            f"--server-url to specify the URL (current: {server_url})."
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
        default="default",
        help=(
            "The model name to use in llama-server API calls (default: default). "
            "Must match the alias set when starting llama-server."
        ),
    )
    parser.add_argument(
        "--server-url",
        type=str,
        default=DEFAULT_LLAMA_SERVER_URL,
        help=(
            f"URL of the llama-server instance (default: {DEFAULT_LLAMA_SERVER_URL}). "
            "Set this if your server runs on a different host or port."
        ),
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

    check_llama_server_connection(args.server_url)
    engine = GameEngine(
        max_history=args.history_length,
        model=args.model,
        server_url=args.server_url,
        map_size=args.size,
        max_loading_time=args.experimental_max_loading_time,
    )
    engine.start()


if __name__ == "__main__":
    main()
