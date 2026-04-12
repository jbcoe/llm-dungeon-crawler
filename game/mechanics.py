"""Game mechanics and data loading."""

import importlib.resources
import logging
import random
import re
from typing import Any

logger = logging.getLogger(__name__)


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


ENEMIES = load_data("enemies.md")
ITEMS = load_data("items.md")
NPCS = load_data("npcs.md")
ROOMS = load_data("rooms.md")
BOSSES = load_data("bosses.md")


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
        hp = 10 + floor * 5
        attack = 3 + floor * 2
        room_enemies.append(
            {
                "name": enemy_data["name"],
                "description": enemy_data["description"],
                "hp": hp,
                "max_hp": hp,
                "attack": attack,
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


# Room types reserved for the final boss encounter.
_FINAL_ROOM_TYPES: list[dict[str, str]] = [
    {
        "name": "Throne of Bones",
        "description": (
            "A cavernous hall where a throne of bleached skulls towers over a "
            "sea of shattered weapons and rusted armour."
        ),
    },
    {
        "name": "Sanctum of the Abyss",
        "description": (
            "A vast circular chamber ringed by floating obsidian pillars, where "
            "a portal to the void pulses with malevolent energy."
        ),
    },
    {
        "name": "Heart of Darkness",
        "description": (
            "The dungeon's innermost sanctum, where the walls bleed shadow and "
            "the air hums with ancient, terrible power."
        ),
    },
    {
        "name": "The Black Altar",
        "description": (
            "A temple of dark stone dominated by an enormous altar stained with "
            "centuries of sacrificial offerings to a nameless god."
        ),
    },
    {
        "name": "Wyrm's Lair",
        "description": (
            "An immense cavern littered with the treasure and bones of countless "
            "adventurers who came before, and failed."
        ),
    },
]


def generate_final_room_mechanics(
    floor: int,
    exits: list[str] | None = None,
) -> dict[str, Any]:
    """Generate the mechanical components of the final boss room."""
    if exits is None:
        exits = []

    room_type = random.choice(_FINAL_ROOM_TYPES)

    boss_data = (
        random.choice(BOSSES)
        if BOSSES
        else {
            "name": "The Dark Lord",
            "description": "An ancient evil of immeasurable power.",
        }
    )

    # Boss stats scale steeply with floor depth
    hp = 80 + floor * 20
    attack = 15 + floor * 5

    boss: dict[str, Any] = {
        "name": boss_data["name"],
        "description": boss_data["description"],
        "hp": hp,
        "max_hp": hp,
        "attack": attack,
        "is_boss": True,
    }

    # Guarantee at least one item as a reward for reaching the final room
    room_items: list[dict[str, Any]] = []
    if ITEMS:
        item_data = random.choice(ITEMS)
        room_items.append(_get_item_mechanics(item_data, floor))

    return {
        "room_type": room_type,
        "exits": exits,
        "items": room_items,
        "enemies": [boss],
        "npcs": [],
        "is_final_room": True,
    }
