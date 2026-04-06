#!/usr/bin/env python3
"""Script to run Gemini CLI in a Docker sandbox."""

import argparse
import os
import subprocess
import sys


def main() -> None:
    """Provide the main entry point for the Gemini sandbox script."""
    parser = argparse.ArgumentParser(description="Run Gemini CLI in a Docker sandbox.")
    parser.add_argument(
        "--update-gemini",
        action="store_true",
        help="Update Gemini CLI inside the container before running.",
    )
    parser.add_argument(
        "--rebuild-docker", action="store_true", help="Rebuild the Docker image."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging."
    )

    args = parser.parse_args()

    def log(msg: str) -> None:
        """Log a message if verbose mode is enabled."""
        if args.verbose:
            print(msg)

    if "GEMINI_API_KEY" not in os.environ:
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Please set it before running this script:", file=sys.stderr)
        print("  export GEMINI_API_KEY='your_api_key_here'", file=sys.stderr)
        sys.exit(1)

    project_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()
    image_name = "llm-dungeon-crawler-gemini-sandbox"
    dockerfile = "docker/Dockerfile"

    if args.rebuild_docker:
        log(f"--- Building Docker Sandbox: {image_name} ---")
        subprocess.check_call(
            [
                "docker",
                "build",
                "-t",
                image_name,
                "-f",
                os.path.join(project_root, dockerfile),
                project_root,
            ]
        )

    log("--- Starting Sandboxed Gemini Session ---")
    log(f"Note: Your current directory {project_root} is mounted to /workspace")

    if args.update_gemini:
        container_cmd = (
            "export NPM_CONFIG_PREFIX=~/.npm-global && "
            "export PATH=~/.npm-global/bin:$PATH && "
            "npm install -g @google/gemini-cli@latest && gemini"
        )
    else:
        container_cmd = "gemini"

    run_args = [
        "docker",
        "run",
        "-it",
        "--rm",
        "--network",
        "host",
        "-v",
        f"{project_root}:/workspace",
        "-e",
        f"GEMINI_API_KEY={os.environ.get('GEMINI_API_KEY', '')}",
        "-e",
        f"OLLAMA_HOST={os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434')}",
    ]

    if "TERM" in os.environ:
        run_args.extend(["-e", f"TERM={os.environ['TERM']}"])
    if "COLORTERM" in os.environ:
        run_args.extend(["-e", f"COLORTERM={os.environ['COLORTERM']}"])

    run_args.extend([image_name, "bash", "-c", container_cmd])

    try:
        subprocess.run(run_args, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
