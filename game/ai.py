"""AI-powered narration and response generation."""

from typing import Any

from ollama import chat

from game.logger import log_event
from game.mechanics import generate_mechanics


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

    prompt = f"""
    Act as a master of Dark Fantasy storytelling.
    You are describing a single room in a dungeon.

    The player has just entered this room. The journey so far: {previous_context}

    Room Elements (DO NOT invent extra enemies, items, or NPCs not listed here):
    - Room Type: {room_type_name} ({room_type_desc})
    - Exits: {exits_str}
    - Enemies present: {enemies_str}
    - NPCs present: {npcs_str}
    - Items found here: {items_str}

    Write a rich, 3-4 sentence atmospheric description of the room itself.
    Focus on lighting, sound, smell, and the mood, reflecting the Room Type description.
    Incorporate the presence of any enemies, NPCs, or items seamlessly into the
    environment description.
    Return ONLY the descriptive text. Do not use JSON or code blocks.
    """

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
    prompt = f"""
    Act as a poetic Dungeon Master.
    A player interacts with an object in their environment.
    Item: {item_name}
    Description: {item_description}
    Current Room: {room_context}

    Narrate the interaction with evocative, "Show, Don't Tell" prose.
    Focus on the physical sensation or the sudden shift in the room's energy.
    Keep it to 1-2 powerful sentences.
    Return ONLY the narrative text. Do not provide options, choices, or commentary.
    """
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
    prompt = f"""
    Act as {npc_name}, a resident of this dark dungeon.
    Your identity: {npc_context}
    The conversation so far: {history}

    The traveler says: "{player_message}"

    Respond in your unique voice. Avoid being overly helpful
    unless it fits your character.
    Keep it brief (1-3 sentences), but let your personality
    bleed through the words.
    Return ONLY the dialogue and actions. Do not provide options,
    choices, or commentary.
    """
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
    prompt = f"""
    Act as a gritty combat narrator.
    The player {player_action} against the {enemy_name}.
    Impact: {damage_dealt} damage dealt.
    Enemy Status: {enemy_hp} HP remaining.
    Player Status: {player_hp} HP remaining.

    Describe the violence of the exchange in 1-2 visceral sentences.
    Incorporate sensory details like the sound of weapons, the spray
    of blood, or the heavy breathing of the combatants.
    Return ONLY the narrative text. Do not provide options,
    choices, or commentary.
    """
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
    prompt = """
    Act as a Dungeon Master.
    Write a haunting introduction for a new journey.

    1. Describe the player character's striking physical feature or
    equipment that hints at their class.
    2. Describe the oppressive entrance to the dungeon.
    3. Provide one cryptic reason for their arrival (an old map,
    a family curse, a whispered rumor).

    Use 3-4 sentences of high-quality dark fantasy prose.
    Return ONLY the narrative text. Do not provide options,
    choices, or commentary.
    """
    log_event("API_CALL: generate_intro", prompt)
    response = chat(model="gemma4:e4b", messages=[{"role": "user", "content": prompt}])
    response_text = (
        response.message.content.strip()
        if response.message and response.message.content
        else ""
    )
    log_event("API_RESPONSE: generate_intro", response_text)
    return response_text
