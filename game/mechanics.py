"""Game mechanics and data loading."""

import random
from typing import Any

from game.theme import Theme


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
    theme: Theme,
    exits: list[str] | None = None,
) -> dict[str, Any]:
    """Generate the mechanical components of a room from the theme."""
    if not exits:
        exits_pool = ["north", "south", "east", "west"]
        num_exits = random.randint(1, 4)
        exits = random.sample(exits_pool, num_exits)

    enemies = theme.enemies
    items = theme.items
    npcs = theme.npcs
    rooms = theme.rooms

    room_type = (
        random.choice(rooms)
        if rooms
        else {"name": "Generic Room", "description": "A cold stone room."}
    )

    room_items: list[dict[str, Any]] = []
    room_enemies: list[dict[str, Any]] = []
    room_npcs: list[dict[str, Any]] = []

    # Probability logic
    enemy_chance = 0.3 + (floor * 0.05)  # Difficulty increases with floors
    enemy_chance = min(enemy_chance, 0.7)

    if enemies and random.random() < enemy_chance:
        enemy_data = random.choice(enemies)
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
    if npcs and not room_enemies and random.random() < 0.2:
        npc_data = random.choice(npcs)
        room_npcs.append(
            {
                "name": npc_data["name"],
                "description": npc_data["description"],
                "dialogue_context": npc_data["description"],
            }
        )

    # Items can appear anywhere
    item_chance = 0.4
    if items and random.random() < item_chance:
        item_data = random.choice(items)
        room_items.append(_get_item_mechanics(item_data, floor))

    return {
        "room_type": room_type,
        "exits": exits,
        "items": room_items,
        "enemies": room_enemies,
        "npcs": room_npcs,
    }
