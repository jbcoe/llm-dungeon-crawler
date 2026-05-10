"""AI-powered narration and response generation."""

import importlib.resources
import logging
from functools import lru_cache
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from game.logger import log_event
from game.mechanics import generate_mechanics

logger = logging.getLogger(__name__)

DEFAULT_LLAMA_SERVER_URL = "http://localhost:8080"


@lru_cache(maxsize=None)
def load_prompt(filename: str) -> str:
    """Load a prompt template from a markdown file in the data directory."""
    filepath = importlib.resources.files("game.data.prompts").joinpath(filename)
    if not filepath.is_file():
        raise FileNotFoundError(f"Missing expected prompt file: {filename}")
    return filepath.read_text(encoding="utf-8")


class AIGenerator:
    """Handles all LLM generation logic using a specific model."""

    def __init__(
        self,
        model: str = "default",
        server_url: str = DEFAULT_LLAMA_SERVER_URL,
    ) -> None:
        """Initialize the AI generator with a specific model and server URL."""
        self.model = model
        base_url = server_url.rstrip("/") + "/v1"
        self.client = OpenAI(base_url=base_url, api_key="not-needed")

    def _query_model(self, prompt: str, system_message: str | None = None) -> str:
        """Make a call to the AI model without silencing errors."""
        messages: list[ChatCompletionMessageParam] = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        log_event(f"API_CALL: {self.model}", prompt)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
        )
        if not response.choices or not response.choices[0].message.content:
            logger.error("AI returned an empty response.")
            raise ValueError("AI returned an empty response.")

        content = response.choices[0].message.content.strip()
        log_event(f"API_RESPONSE: {self.model}", content)
        return content

    def generate_room(
        self,
        floor: int,
        previous_context: str = "",
        exits: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate a room description using AI based on current mechanics."""
        mechanics = generate_mechanics(floor, exits=exits)

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
        mechanics["name"] = room_type_name

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

    def narrate_rest(self, player_hp: int, player_max_hp: int) -> str:
        """Generate narrative text for the player resting."""
        template = load_prompt("rest.md")
        prompt = template.format(
            player_hp=player_hp,
            player_max_hp=player_max_hp,
        )
        return self._query_model(prompt)
