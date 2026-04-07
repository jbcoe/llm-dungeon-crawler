"""AI-powered narration and response generation."""

import importlib.resources
import logging
import os
import signal
import subprocess
import time
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Generator

import ollama
from ollama import chat, generate, ps

from game.logger import log_event
from game.mechanics import generate_mechanics

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def load_prompt(filename: str) -> str:
    """Load a prompt template from a markdown file in the data directory."""
    filepath = importlib.resources.files("game.data.prompts").joinpath(filename)
    if not filepath.is_file():
        raise FileNotFoundError(f"Missing expected prompt file: {filename}")
    return filepath.read_text(encoding="utf-8")


class AIGenerator:
    """Handles all LLM generation logic using a specific model."""

    def __init__(self, model: str = "gemma4:e4b") -> None:
        """Initialize the AI generator with a specific model."""
        self.model = model

    @staticmethod
    @contextmanager
    def manage_ollama(model: str) -> Generator[None, None, None]:
        """
        Manage the lifecycle of the Ollama model/server.

        Ensures that the LLM (server or model) is stopped on exit if it was
        started by the game.
        """
        server_was_running = True
        try:
            ollama.list()
        except Exception:
            server_was_running = False

        server_process = None
        if not server_was_running:
            try:
                server_process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                # Wait for server to start (20s max, checking every 0.1s)
                for _ in range(200):
                    if server_process.poll() is not None:
                        # Process died early (e.g. port already in use)
                        break
                    try:
                        ollama.list()
                        server_was_running = True
                        break
                    except Exception:
                        time.sleep(0.1)
            except OSError:
                pass

        model_was_loaded = False
        if server_was_running:
            try:
                response = ps()
                models_list = (
                    getattr(response, "models", [])
                    if hasattr(response, "models")
                    else response.get("models", [])
                )
                for m in models_list:
                    name = getattr(m, "model", "") or m.get("model", "")
                    if name == model:
                        model_was_loaded = True
                        break
            except Exception:
                pass

        try:
            yield
        finally:
            if server_process:
                try:
                    if hasattr(os, "killpg"):
                        os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
                    else:
                        server_process.terminate()
                    server_process.wait(timeout=5)
                except Exception:
                    pass
            elif not model_was_loaded:
                try:
                    # Unload the model if it was started by the game
                    generate(model=model, keep_alive=0)
                except Exception:
                    pass

    def _query_model(self, prompt: str, system_message: str | None = None) -> str:
        """Make a call to the AI model without silencing errors."""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        log_event(f"API_CALL: {self.model}", prompt)
        response = chat(
            model=self.model,
            messages=messages,
            options={"temperature": 0.7},
        )
        if not response.message or not response.message.content:
            logger.error("AI returned an empty response.")
            raise ValueError("AI returned an empty response.")

        content = response.message.content.strip()
        log_event(f"API_RESPONSE: {self.model}", content)
        return content

    def generate_room(self, floor: int, previous_context: str = "") -> dict[str, Any]:
        """Generate a room description using AI based on current mechanics."""
        mechanics = generate_mechanics(floor)

        # Format lists for the prompt
        room_type_name = mechanics["room_type"]["name"]
        room_type_desc = mechanics["room_type"]["description"]
        exits_str = ", ".join(mechanics["exits"])
        enemies_str = (
            ", ".join([e["name"] for e in mechanics["enemies"]])
            if mechanics["enemies"]
            else "None"
        )
        npcs_str = (
            ", ".join([n["name"] for n in mechanics["npcs"]])
            if mechanics["npcs"]
            else "None"
        )
        items_str = (
            ", ".join([i["name"] for i in mechanics["items"]])
            if mechanics["items"]
            else "None"
        )

        template = load_prompt("room.md")
        prompt = template.format(
            previous_context=previous_context,
            room_type_name=room_type_name,
            room_type_desc=room_type_desc,
            exits_str=exits_str,
            enemies_str=enemies_str,
            npcs_str=npcs_str,
            items_str=items_str,
        )

        description = self._query_model(prompt)
        mechanics["description"] = description

        return mechanics

    def narrate_item_use(
        self, item_name: str, item_description: str, room_context: str
    ) -> str:
        """Generate narrative text for using an item."""
        template = load_prompt("item_use.md")
        prompt = template.format(
            item_name=item_name,
            item_description=item_description,
            room_context=room_context,
        )
        return self._query_model(prompt)

    def generate_npc_response(
        self, npc_name: str, npc_context: str, player_message: str, history: str = ""
    ) -> str:
        """Generate a dialogue response from an NPC."""
        template = load_prompt("npc.md")
        prompt = template.format(
            npc_name=npc_name,
            npc_context=npc_context,
            history=history,
            player_message=player_message,
        )
        return self._query_model(prompt)

    def narrate_combat(
        self,
        player_action: str,
        player_hp: int,
        enemy_name: str,
        enemy_hp: int,
        damage_dealt: int,
    ) -> str:
        """Generate visceral narration for a combat exchange."""
        template = load_prompt("combat.md")
        prompt = template.format(
            player_action=player_action,
            enemy_name=enemy_name,
            damage_dealt=damage_dealt,
            enemy_hp=enemy_hp,
            player_hp=player_hp,
        )
        return self._query_model(prompt)

    def generate_intro(self) -> str:
        """Generate a haunting introduction for the game session."""
        prompt = load_prompt("intro.md")
        return self._query_model(prompt)
