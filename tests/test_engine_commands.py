"""Unit tests for engine commands."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from game.engine import GameEngine
from game.models import NPC, Enemy, Item, Player, Room


@pytest.fixture
def engine() -> GameEngine:
    """Fixture that initializes a GameEngine with a mocked Room and Player state."""
    engine = GameEngine(mock_input=["quit"])
    engine.player = Player()
    engine.current_room = Room(
        description="A test room",
        exits=["north", "south"],
        items=[Item(name="Key", description="A rusty key")],
        enemies=[Enemy(name="Goblin", description="Ugly", hp=10, max_hp=10, attack=5)],
        npcs=[NPC(name="Merchant", description="Sells things")],
    )
    return engine


def assert_printed(mock_print: MagicMock, expected_text: str) -> None:
    """Verify that a specific substring was printed to the console."""
    found = any(
        expected_text in str(call_args) for call_args in mock_print.call_args_list
    )
    assert found, f"Expected '{expected_text}' to be printed, but it wasn't."


def test_display_room(engine: GameEngine) -> None:
    """Test that the display_room helper renders the room output correctly."""
    with patch("game.engine.GameUI.print") as mock_print:
        engine.display_room()
        assert_printed(mock_print, "A test room")
        assert_printed(mock_print, "north, south")
        assert_printed(mock_print, "Key - A rusty key")
        assert_printed(mock_print, "Goblin")
        assert_printed(mock_print, "Merchant")


def test_display_status(engine: GameEngine) -> None:
    """Test that the display_status helper formats player HP, attack, and inventory."""
    with patch("game.engine.GameUI.print") as mock_print:
        engine.display_status()
        assert_printed(mock_print, "HP:")
        assert_printed(mock_print, "100/100")
        assert_printed(mock_print, "Attack:")
        assert_printed(mock_print, "10")
        assert_printed(mock_print, "Inventory:")
        assert_printed(mock_print, "Empty")


def test_handle_go(engine: GameEngine) -> None:
    """Ensure the 'go' command validates exits and handles enemy blockage correctly."""
    with (
        patch("game.engine.generate_room") as mock_gen_room,
        patch("game.engine.GameUI.print") as mock_print,
    ):
        mock_gen_room.return_value = {
            "description": "New room",
            "room_type": {"name": "Cave"},
            "exits": ["south"],
            "items": list[dict[str, Any]](),
            "enemies": list[dict[str, Any]](),
            "npcs": list[dict[str, Any]](),
        }

        # Cannot move if enemies present
        engine.handle_go(["go", "north"])
        assert engine.floor == 1
        assert_printed(mock_print, "You can't leave while there are enemies here!")

        # Clear enemies to move
        assert engine.current_room is not None
        engine.current_room.enemies = list[Enemy]()

        # Test moving valid direction
        engine.handle_go(["go", "north"])
        assert engine.floor == 2
        mock_gen_room.assert_called_once()

        # Test invalid direction
        engine.handle_go(["go", "east"])
        assert_printed(mock_print, "You cannot go 'east'.")

        # Test no direction
        engine.handle_go(["go"])
        assert_printed(mock_print, "Go where?")


def test_handle_attack(engine: GameEngine) -> None:
    """Validate combat loops, entity targeting, and damage application."""
    with (
        patch("game.engine.narrate_combat", return_value="Slash!"),
        patch("game.engine.GameUI.print") as mock_print,
    ):
        # Test valid attack
        engine.handle_attack(["attack", "goblin"])
        # Enemy should take damage or die depending on player damage.
        # Base attack is 10, enemy HP is 10. So it should die.
        assert engine.current_room is not None
        assert len(engine.current_room.enemies) == 0
        assert_printed(mock_print, "Slash!")
        assert_printed(mock_print, "You defeated Goblin!")

        # Test attack nothing
        engine.handle_attack(["attack"])
        assert_printed(mock_print, "There is nothing to attack here.")

        # Test attack nonexistent
        engine.current_room.enemies.append(Enemy(name="Orc", description="Big"))
        engine.handle_attack(["attack", "dragon"])
        assert_printed(mock_print, "No enemy named 'dragon' here.")


def test_handle_talk(engine: GameEngine) -> None:
    """Test NPC conversational loops and gracefully handling missing targets."""
    with (
        patch("game.engine.generate_npc_response", side_effect=["Hello", "Bye"]),
        patch("game.engine.GameUI.print") as mock_print,
        patch.object(engine, "get_input", side_effect=["hi", "leave"]),
    ):
        # Talk to merchant
        engine.handle_talk(["talk", "merchant"])
        assert_printed(mock_print, "You approach Merchant.")
        assert_printed(mock_print, "Hello")
        assert_printed(mock_print, "Merchant nods as you walk away.")

    with patch("game.engine.GameUI.print") as mock_print:
        # Talk to no one
        engine.handle_talk(["talk"])
        assert_printed(mock_print, "Talk to whom?")

        # Talk to nonexistent
        engine.handle_talk(["talk", "dragon"])
        assert_printed(mock_print, "No one named 'dragon' here.")


def test_handle_take(engine: GameEngine) -> None:
    """Ensure items are removed from the room and placed into player inventory."""
    with patch("game.engine.GameUI.print") as mock_print:
        # Take valid item
        engine.handle_take(["take", "key"])
        assert len(engine.player.inventory) == 1
        assert engine.player.inventory[0].name == "Key"
        assert engine.current_room is not None
        assert len(engine.current_room.items) == 0
        assert_printed(mock_print, "You took the Key.")

        # Take nothing
        engine.handle_take(["take"])
        assert_printed(mock_print, "Take what?")

        # Take nonexistent
        engine.handle_take(["take", "sword"])
        assert_printed(mock_print, "No item named 'sword' here.")


def test_handle_equip(engine: GameEngine) -> None:
    """Test weapon equipping mechanics and validating 'weapon' effect_type."""
    weapon = Item(
        name="Sword", description="Sharp", effect_type="weapon", stat_effect=5
    )
    engine.player.inventory.append(weapon)

    with patch("game.engine.GameUI.print") as mock_print:
        engine.handle_equip(["equip", "sword"])
        assert engine.player.equipped_weapon == weapon
        assert weapon not in engine.player.inventory
        assert_printed(mock_print, "You equipped")
        assert_printed(mock_print, "Sword")

        engine.handle_equip(["equip"])
        assert_printed(mock_print, "Equip what?")

        engine.handle_equip(["equip", "dragon"])
        assert_printed(mock_print, "You don't have an item named 'dragon'.")

        # Try equip non-weapon
        engine.player.inventory.append(Item(name="Key2", description="A rusty key"))
        engine.handle_equip(["equip", "key2"])
        assert engine.player.equipped_weapon == weapon
        assert_printed(mock_print, "You can't equip Key2. It's not a weapon.")


def test_handle_unequip(engine: GameEngine) -> None:
    """Verify that weapons are correctly unequipped back into player inventory."""
    weapon = Item(
        name="Sword", description="Sharp", effect_type="weapon", stat_effect=5
    )
    engine.player.equipped_weapon = weapon

    with patch("game.engine.GameUI.print") as mock_print:
        engine.handle_unequip()
        assert engine.player.equipped_weapon is None
        assert weapon in engine.player.inventory
        assert_printed(mock_print, "You unequipped")
        assert_printed(mock_print, "Sword")

        # Unequip when nothing is equipped
        engine.handle_unequip()
        assert_printed(mock_print, "You don't have a weapon equipped.")


def test_handle_use(engine: GameEngine) -> None:
    """Ensure consumables trigger correct logic (like healing) and get removed."""
    potion = Item(
        name="Potion", description="Heals", effect_type="healing", stat_effect=10
    )
    engine.player.inventory.append(potion)
    engine.player.hp = 10

    with (
        patch("game.engine.narrate_item_use", return_value="Used!"),
        patch("game.engine.GameUI.print") as mock_print,
    ):
        engine.handle_use(["use", "potion"])
        assert engine.player.hp == 20
        assert potion not in engine.player.inventory
        assert_printed(mock_print, "You used Potion and healed 10 HP.")

        engine.handle_use(["use"])
        assert_printed(mock_print, "Use what?")

        engine.handle_use(["use", "dragon"])
        assert_printed(mock_print, "You don't have an item named 'dragon'.")

        # Use weapon (should print error)
        weapon = Item(
            name="Sword", description="Sharp", effect_type="weapon", stat_effect=5
        )
        engine.player.inventory.append(weapon)
        engine.handle_use(["use", "sword"])
        assert_printed(mock_print, "you must 'equip' it.")

        # Use junk
        junk = Item(name="Junk", description="Trash", effect_type="none", stat_effect=0)
        engine.player.inventory.append(junk)
        engine.handle_use(["use", "junk"])
        assert_printed(mock_print, "Used!")
