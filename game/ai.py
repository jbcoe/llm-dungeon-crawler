"""AI-powered narration and response generation."""

import importlib.resources
from functools import lru_cache
from typing import Any

from ollama import chat

from game.logger import log_event
from game.mechanics import generate_mechanics


@lru_cache(maxsize=None)
def load_prompt(filename: str) -> str:
    """Load a prompt template from a markdown file in the data directory."""
    filepath = importlib.resources.files("game.data.prompts").joinpath(filename)
    if not filepath.is_file():
        raise FileNotFoundError(f"Missing expected prompt file: {filename}")
    return filepath.read_text(encoding="utf-8")


def generate_room(floor: int, previous_context: str = "") -> dict[str, Any]:
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

    log_event("API_CALL: generate_room_description", prompt)
    response = chat(
        model="gemma4:e4b",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.7},
    )
    description = (
        response.message.content.strip()
        if response.message and response.message.content
        else ""
    )
    log_event("API_RESPONSE: generate_room_description", description)
    mechanics["description"] = description

    return mechanics


def narrate_item_use(item_name: str, item_description: str, room_context: str) -> str:
    """Generate narrative text for using an item."""
    template = load_prompt("item_use.md")
    prompt = template.format(
        item_name=item_name,
        item_description=item_description,
        room_context=room_context,
    )
    log_event("API_CALL: narrate_item_use", prompt)
    response = chat(model="gemma4:e4b", messages=[{"role": "user", "content": prompt}])
    response_text = (
        response.message.content.strip()
        if response.message and response.message.content
        else ""
    )
    log_event("API_RESPONSE: narrate_item_use", response_text)
    return response_text


def generate_npc_response(
    npc_name: str, npc_context: str, player_message: str, history: str = ""
) -> str:
    """Generate a dialogue response from an NPC."""
    template = load_prompt("npc.md")
    prompt = template.format(
        npc_name=npc_name,
        npc_context=npc_context,
        history=history,
        player_message=player_message,
    )
    log_event("API_CALL: generate_npc_response", prompt)
    response = chat(model="gemma4:e4b", messages=[{"role": "user", "content": prompt}])
    response_text = (
        response.message.content.strip()
        if response.message and response.message.content
        else ""
    )
    log_event("API_RESPONSE: generate_npc_response", response_text)
    return response_text


def narrate_combat(
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
    log_event("API_CALL: narrate_combat", prompt)
    response = chat(model="gemma4:e4b", messages=[{"role": "user", "content": prompt}])
    response_text = (
        response.message.content.strip()
        if response.message and response.message.content
        else ""
    )
    log_event("API_RESPONSE: narrate_combat", response_text)
    return response_text


def generate_intro() -> str:
    """Generate a haunting introduction for the game session."""
    prompt = load_prompt("intro.md")
    log_event("API_CALL: generate_intro", prompt)
    response = chat(model="gemma4:e4b", messages=[{"role": "user", "content": prompt}])
    response_text = (
        response.message.content.strip()
        if response.message and response.message.content
        else ""
    )
    log_event("API_RESPONSE: generate_intro", response_text)
    return response_text
