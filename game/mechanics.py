"""Game mechanics and data loading."""

import importlib.resources
import json
import logging
import random
import re
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_ENEMY_HP = 10
DEFAULT_ENEMY_ATTACK = 5
DEFAULT_ENEMY_LEVEL = 1
_ENEMY_STAT_JITTER = 2


def load_data(filename: str) -> list[dict[str, str]]:
    """Load game data from a markdown file with robust parsing."""
    items: list[dict[str, str]] = []
    try:
        filepath = importlib.resources.files("game.data").joinpath(filename)
        if not filepath.is_file():
            logger.error(f"Missing expected data file: {filename}")
            return []

        content = filepath.read_text(encoding="utf-8")
        # Match lines starting with optional space, then - or *, then name : description
        pattern = re.compile(r"^\s*[-*]\s*([^:]+):\s*(.*)$", re.MULTILINE)
        matches = pattern.findall(content)
        for name, desc in matches:
            items.append({"name": name.strip(), "description": desc.strip()})
    except Exception:
        logger.exception(f"Error loading data from {filename}")

    return items


def load_enemy_data(filename: str) -> list[dict[str, Any]]:
    """Load enemy definitions, including base hp/attack, from a JSON file."""
    enemies: list[dict[str, Any]] = []
    try:
        filepath = importlib.resources.files("game.data").joinpath(filename)
        if not filepath.is_file():
            logger.error(f"Missing expected data file: {filename}")
            return []

        enemies = json.loads(filepath.read_text(encoding="utf-8"))
    except Exception:
        logger.exception(f"Error loading data from {filename}")

    return enemies


def roll_enemy_stats(enemy_data: dict[str, Any]) -> tuple[int, int, int]:
    """
    Roll an enemy's hp/attack from its base stats, with a small fixed jitter.

    The jitter does not depend on dungeon floor, so enemies of a given type
    stay roughly the same strength no matter how deep the player has gone.
    Level is read directly from the enemy's data and is not jittered.
    """
    base_hp = enemy_data.get("hp", DEFAULT_ENEMY_HP)
    base_attack = enemy_data.get("attack", DEFAULT_ENEMY_ATTACK)
    jitter = _ENEMY_STAT_JITTER
    hp = max(1, base_hp + random.randint(-jitter, jitter))
    attack = max(1, base_attack + random.randint(-jitter, jitter))
    level = enemy_data.get("level", DEFAULT_ENEMY_LEVEL)
    return hp, attack, level


ENEMIES = load_enemy_data("enemies.json")
ITEMS = load_data("items.md")
NPCS = load_data("npcs.md")
ROOMS = load_data("rooms.md")


def _get_item_mechanics(item_data: dict[str, str], floor: int) -> dict[str, Any]:
    """Determine item mechanics based on its name and floor."""
    name_lower = item_data["name"].lower()

    # Define keywords for different item types
    healing_keywords = ["potion", "salve", "elixir", "herb", "tonic"]
    weapon_keywords = [
        "sword",
        "blade",
        "axe",
        "hammer",
        "dagger",
        "spear",
        "mace",
        "staff",
    ]

    effect_type = "none"
    stat_effect = 0

    if any(k in name_lower for k in healing_keywords):
        effect_type = "healing"
        stat_effect = 20 + (floor * 2)
    elif any(k in name_lower for k in weapon_keywords):
        effect_type = "weapon"
        stat_effect = 5 + (floor * 2)

    return {
        "name": item_data["name"],
        "description": item_data["description"],
        "effect_type": effect_type,
        "stat_effect": stat_effect,
    }


def generate_mechanics(
    floor: int,
    exits: list[str] | None = None,
) -> dict[str, Any]:
    """Generate the mechanical components of a room based on the current floor."""
    if not exits:
        exits_pool = ["north", "south", "east", "west"]
        num_exits = random.randint(1, 4)
        exits = random.sample(exits_pool, num_exits)

    room_type = (
        random.choice(ROOMS)
        if ROOMS
        else {"name": "Generic Room", "description": "A cold stone room."}
    )

    room_items: list[dict[str, Any]] = []
    room_enemies: list[dict[str, Any]] = []
    room_npcs: list[dict[str, Any]] = []

    # Probability logic
    enemy_chance = 0.3 + (floor * 0.05)  # Difficulty increases with floors
    enemy_chance = min(enemy_chance, 0.7)

    if ENEMIES and random.random() < enemy_chance:
        enemy_data = random.choice(ENEMIES)
        hp, attack, level = roll_enemy_stats(enemy_data)
        room_enemies.append(
            {
                "name": enemy_data["name"],
                "description": enemy_data["description"],
                "hp": hp,
                "max_hp": hp,
                "attack": attack,
                "level": level,
            }
        )

    # NPCs appear if there are no enemies (usually)
    if NPCS and not room_enemies and random.random() < 0.2:
        npc_data = random.choice(NPCS)
        room_npcs.append(
            {
                "name": npc_data["name"],
                "description": npc_data["description"],
                "dialogue_context": npc_data["description"],
            }
        )

    # Items can appear anywhere
    item_chance = 0.4
    if ITEMS and random.random() < item_chance:
        item_data = random.choice(ITEMS)
        room_items.append(_get_item_mechanics(item_data, floor))

    return {
        "room_type": room_type,
        "exits": exits,
        "items": room_items,
        "enemies": room_enemies,
        "npcs": room_npcs,
    }
