#!/usr/bin/env python3
"""Script to run Claude Code in YOLO mode within a Docker sandbox."""

import argparse
import os
import subprocess
import sys


def main() -> None:
    """Provide the main entry point for the Claude sandbox script."""
    parser = argparse.ArgumentParser(
        description="Run Claude Code in YOLO mode within a Docker sandbox."
    )
    parser.add_argument(
        "--update-claude",
        action="store_true",
        help="Update Claude Code inside the container before running.",
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

    project_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()
    image_name = "llm-dungeon-crawler-claude-sandbox"
    dockerfile = "docker/Dockerfile.claude"

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

    log("--- Starting Sandboxed Claude Code Session (YOLO mode) ---")
    log(f"Note: Your current directory {project_root} is mounted to /workspace")

    # YOLO mode: --dangerously-skip-permissions bypasses all permission prompts,
    # which is safe here because we're already inside an isolated Docker container.
    if args.update_claude:
        update_cmd = (
            "export NPM_CONFIG_PREFIX=~/.npm-global && "
            "export PATH=~/.npm-global/bin:$PATH && "
            "npm install -g @anthropic-ai/claude-code@latest && "
        )
    else:
        update_cmd = ""

    claude_cmd = "claude --dangerously-skip-permissions"

    container_cmd = update_cmd + claude_cmd

    # Persist Claude auth state across container runs by mounting the host's
    # ~/.claude directory and ~/.claude.json file. This avoids re-authenticating
    # every session.
    host_claude_dir = os.path.expanduser("~/.claude")
    host_claude_json = os.path.expanduser("~/.claude.json")
    os.makedirs(host_claude_dir, mode=0o700, exist_ok=True)
    # Ensure the file exists on the host so Docker doesn't create it as a directory.
    # Use os.open with restrictive permissions to avoid exposing credentials to
    # other local users on multi-user systems.
    if not os.path.exists(host_claude_json):
        fd = os.open(host_claude_json, os.O_CREAT | os.O_WRONLY, 0o600)
        os.close(fd)

    run_args = [
        "docker",
        "run",
        "-it",
        "--rm",
        "--network",
        "host",
        "-v",
        f"{project_root}:/workspace",
        "-v",
        f"{host_claude_dir}:/home/vscode/.claude",
        "-v",
        f"{host_claude_json}:/home/vscode/.claude.json",
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
