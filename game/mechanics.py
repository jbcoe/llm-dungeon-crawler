import random
import importlib.resources


def load_data(filename):
    items = []
    filepath = importlib.resources.files("game.data").joinpath(filename)
    if not filepath.exists():
        raise FileNotFoundError(f"Missing expected data file: {filename}")
    with filepath.open("r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("- "):
                parts = line[2:].strip().split(":", 1)
                if len(parts) == 2:
                    items.append(
                        {"name": parts[0].strip(), "description": parts[1].strip()}
                    )
    return items


ENEMIES = load_data("enemies.md")
ITEMS = load_data("items.md")
NPCS = load_data("npcs.md")
ROOMS = load_data("rooms.md")


def generate_mechanics(floor: int) -> dict:
    exits_pool = ["north", "south", "east", "west"]
    exits = random.sample(exits_pool, random.randint(1, 4))

    room_type = (
        random.choice(ROOMS)
        if ROOMS
        else {"name": "Generic Room", "description": "A stone room."}
    )

    room_items = []
    room_enemies = []
    room_npcs = []

    # 30% chance for an enemy
    if ENEMIES and random.random() < 0.3:
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

    # 20% chance for NPC, typically not in same room as enemy
    if NPCS and random.random() < 0.2 and not room_enemies:
        npc_data = random.choice(NPCS)
        room_npcs.append(
            {
                "name": npc_data["name"],
                "description": npc_data["description"],
                "dialogue_context": npc_data["description"],
            }
        )

    # 40% chance for an Item
    if ITEMS and random.random() < 0.4:
        item_data = random.choice(ITEMS)
        effect_type = "none"
        stat_effect = 0
        name_lower = item_data["name"].lower()
        if "potion" in name_lower or "salve" in name_lower:
            effect_type = "healing"
            stat_effect = 20
        elif (
            "sword" in name_lower
            or "blade" in name_lower
            or "axe" in name_lower
            or "hammer" in name_lower
            or "dagger" in name_lower
        ):
            effect_type = "weapon"
            stat_effect = 5 + floor * 2

        room_items.append(
            {
                "name": item_data["name"],
                "description": item_data["description"],
                "effect_type": effect_type,
                "stat_effect": stat_effect,
            }
        )

    return {
        "room_type": room_type,
        "exits": exits,
        "items": room_items,
        "enemies": room_enemies,
        "npcs": room_npcs,
    }
