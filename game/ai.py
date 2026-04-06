import json
import random
from ollama import chat
from .logger import log_event
from .models import Room


def _get_random_suggestions(filename: str, count: int = 3) -> str:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip().startswith("- ")]
        if not lines:
            return "None"
        samples = random.sample(lines, min(count, len(lines)))
        return "\n    ".join(samples)
    except Exception:
        return "None"


def generate_room(floor: int, previous_context: str = "") -> dict:
    room_ideas = _get_random_suggestions("data/rooms.md", 3)
    enemy_ideas = _get_random_suggestions("data/enemies.md", 3)
    npc_ideas = _get_random_suggestions("data/npcs.md", 3)
    item_ideas = _get_random_suggestions("data/items.md", 3)

    prompt = f"""
    Act as a Dungeon Master. Generate a new room for floor {floor}.
    Previous context: {previous_context}

    Design this room inspired by canonical fantasy literature and films.
    CRITICAL: Create variety! Not every room should have a fight. Many rooms should be empty but highly atmospheric. Include intricate puzzles, environmental storytelling, or mysterious NPCs (who might offer riddles, lore, or trades). When enemies do appear, mix them up (e.g., mythical beasts, ancient undead, cunning cultists, magical constructs) rather than just generic monsters.

    Here are some inspirations you can use or adapt (you don't have to use them all, or exactly as written):
    Room Concepts:
    {room_ideas}

    Enemies:
    {enemy_ideas}

    NPCs:
    {npc_ideas}

    Items:
    {item_ideas}

    Return ONLY a valid JSON object with:
    - description (string): Atmospheric description of the room, puzzles, or environmental challenges.
    - exits (list of strings): Available directions (e.g. north, south, east, west).
    - items (list of objects): Zero or more items with 'name', 'description', 'stat_effect' (int), and 'effect_type' ('healing', 'damage', 'weapon', or 'none'). Many items should just be 'none' for puzzles or lore. 'weapon' items increase player attack power by their 'stat_effect'.
    - enemies (list of objects): Zero or more enemies with 'name', 'description', 'hp' (int), 'max_hp' (int), 'attack' (int). Often leave this empty to build tension!
    - npcs (list of objects): Zero or more friendly/neutral NPCs with 'name', 'description', and 'dialogue_context' (string, brief instructions on how they speak and what they know, e.g., "A sphinx who speaks in riddles").
    """
    log_event("API_CALL: generate_room", prompt)
    try:
        response = chat(
            model="gemma-4:e4b",
            messages=[{"role": "user", "content": prompt}],
            format=Room.model_json_schema(),
            options={"temperature": 0},
        )
        response_text = response.message.content or "{}"
        log_event("API_RESPONSE: generate_room", response_text)
        return json.loads(response_text)
    except Exception as e:
        log_event("API_ERROR: generate_room", str(e))
        return _fallback_room()


def narrate_item_use(item_name: str, item_description: str, room_context: str) -> str:
    prompt = f"""
    Act as a Dungeon Master. The player tries to use an item in their current location.
    Item: {item_name}
    Description: {item_description}
    Current Room Context: {room_context}

    Narrate what happens when they use, inspect, or interact with it. Keep it to 1-2 evocative sentences. It might reveal lore, have a mysterious but harmless effect, or simply do nothing right now.
    """
    log_event("API_CALL: narrate_item_use", prompt)
    try:
        response = chat(
            model="gemma-4:e4b", messages=[{"role": "user", "content": prompt}]
        )
        response_text = (
            response.message.content.strip()
            if response.message.content
            else f"You examine the {item_name}. It seems to do nothing."
        )
        log_event("API_RESPONSE: narrate_item_use", response_text)
        return response_text
    except Exception as e:
        log_event("API_ERROR: narrate_item_use", str(e))
        return f"You examine the {item_name}. It seems to do nothing."


def generate_npc_response(
    npc_name: str, npc_context: str, player_message: str, history: str = ""
) -> str:
    prompt = f"""
    Act as an NPC named {npc_name} in a dungeon crawler.
    Context/Personality: {npc_context}
    Recent conversation history: {history}
    The player says: "{player_message}"
    Respond in character. Keep it brief, 1-3 sentences.
    """
    log_event("API_CALL: generate_npc_response", prompt)
    try:
        response = chat(
            model="gemma-4:e4b", messages=[{"role": "user", "content": prompt}]
        )
        response_text = (
            response.message.content.strip() if response.message.content else "..."
        )
        log_event("API_RESPONSE: generate_npc_response", response_text)
        return response_text
    except Exception as e:
        log_event("API_ERROR: generate_npc_response", str(e))
        return "The NPC just stares at you blankly."


def narrate_combat(
    player_action: str,
    player_hp: int,
    enemy_name: str,
    enemy_hp: int,
    damage_dealt: int,
) -> str:
    prompt = f"""
    Act as a Dungeon Master narrating a single turn of combat.
    The player chose to: {player_action}.
    The enemy is {enemy_name}.
    Damage dealt: {damage_dealt}.
    Current Player HP: {player_hp}. Current Enemy HP: {enemy_hp}.
    Provide a brief, exciting 1-2 sentence description of what just happened.
    """
    log_event("API_CALL: narrate_combat", prompt)
    try:
        response = chat(
            model="gemma-4:e4b", messages=[{"role": "user", "content": prompt}]
        )
        response_text = (
            response.message.content.strip()
            if response.message.content
            else f"You {player_action} the {enemy_name} for {damage_dealt} damage."
        )
        log_event("API_RESPONSE: narrate_combat", response_text)
        return response_text
    except Exception as e:
        log_event("API_ERROR: narrate_combat", str(e))
        return f"You {player_action} the {enemy_name} for {damage_dealt} damage."


def generate_intro() -> str:
    prompt = """
    Act as a Dungeon Master. Generate an atmospheric introduction (3-4 sentences) setting the scene for a new adventurer entering an endless, procedurally generated dungeon inspired by classic fantasy.
    Crucially, explicitly describe the player character's appearance, class, or demeanor to give them a distinct identity, and give them a vague but compelling reason to be there (e.g., seeking a lost arcane artifact, fulfilling a grim oath, or hunting a rumor of endless wealth).
    """
    log_event("API_CALL: generate_intro", prompt)
    try:
        response = chat(
            model="gemma-4:e4b", messages=[{"role": "user", "content": prompt}]
        )
        response_text = (
            response.message.content.strip()
            if response.message.content
            else "You stand before the entrance of a dark, forgotten dungeon. What secrets lie within?"
        )
        log_event("API_RESPONSE: generate_intro", response_text)
        return response_text
    except Exception as e:
        log_event("API_ERROR: generate_intro", str(e))
        return "You stand before the entrance of a dark, forgotten dungeon. What secrets lie within?"


def _fallback_room() -> dict:
    return {
        "description": "A dark, generic room. You sense an error in the matrix.",
        "exits": ["north", "south"],
        "items": [],
        "enemies": [
            {
                "name": "Glitch Slime",
                "description": "A trembling blob of bad code.",
                "hp": 10,
                "max_hp": 10,
                "attack": 2,
            }
        ],
        "npcs": [],
    }
