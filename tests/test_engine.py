"""Tests for the game engine logic."""

from typing import Any
from unittest.mock import patch

from game.engine import GameEngine
from game.models import NPC, Enemy, Item, Room


def test_engine_initialization(fake_ai: Any) -> None:
    """Test that the engine initializes with correct player state."""
    engine = GameEngine(mock_input=["quit"], ai_generator=fake_ai)
    engine.start()

    assert engine.player.hp == 100
    assert engine.floor == 1
    assert engine.current_room is not None
    assert engine.current_room.description
    assert isinstance(engine.current_room.description, str)
    assert len(engine.current_room.exits) > 0


def test_combat(fake_ai: Any) -> None:
    """Test combat mechanics and enemy death."""
    engine = GameEngine(mock_input=["attack slime", "quit"], ai_generator=fake_ai)
    room = Room(
        name="Test Room",
        description="Test",
        exits=["north"],
        enemies=[
            Enemy(
                name="Slime",
                description="test",
                hp=10,
                max_hp=10,
                attack=2,
            )
        ],
    )
    engine.current_room = room
    with patch("game.engine.random.randint", return_value=10):
        engine.game_loop()

    # Slime should have taken 10 damage from player's attack of 10 and died
    assert len(engine.current_room.enemies) == 0
    # Player takes no damage because slime died before it could attack
    assert engine.player.hp == 100


def test_talk(fake_ai: Any) -> None:
    """Test NPC interaction and dialogue."""
    engine = GameEngine(
        mock_input=["talk merchant", "hello", "bye", "quit"], ai_generator=fake_ai
    )
    room = Room(
        name="Test Room",
        description="Test",
        exits=["north"],
        npcs=[
            NPC(
                name="Merchant",
                description="A merchant",
                dialogue_context="Friendly",
            )
        ],
    )
    engine.current_room = room
    engine.game_loop()


def test_autocompletion_options(fake_ai: Any) -> None:
    """Test that autocompletion returns expected command and entity words."""
    engine = GameEngine(mock_input=["quit"], ai_generator=fake_ai)
    room = Room(
        name="Test Room",
        description="Test Room",
        exits=["north", "east"],
        enemies=[
            Enemy(
                name="Dark Elf",
                description="test",
                hp=10,
                max_hp=10,
                attack=2,
            )
        ],
        npcs=[NPC(name="Old Wizard", description="test")],
        items=[Item(name="Health Potion", description="test")],
    )
    engine.current_room = room
    engine.player.inventory = [Item(name="Rusty Sword", description="An old sword")]

    options = engine.get_completion_options()

    # Check base commands
    assert "look" in options
    assert "attack" in options
    assert "quit" in options

    # Check exits
    assert "north" in options
    assert "east" in options

    # Check entities are split and lowercased
    assert "dark" in options
    assert "elf" in options
    assert "old" in options
    assert "wizard" in options
    assert "health" in options
    assert "potion" in options

    # Check inventory
    assert "rusty" in options
    assert "sword" in options


def test_history_tracking(fake_ai: Any) -> None:
    """Test that player commands are correctly tracked in history."""
    engine = GameEngine(
        mock_input=["look", "go north", "inventory", "quit"], ai_generator=fake_ai
    )
    engine.current_room = Room(name="Test Room", description="Test", exits=["north"])
    # Mock enter_new_room so it doesn't try to generate a real room when moving
    engine.enter_new_room = lambda direction="forward": None
    engine.game_loop()

    assert engine.history == ["look", "go north", "inventory", "quit"]


def test_history_truncation(fake_ai: Any) -> None:
    """Test that command history is truncated according to max_history."""
    engine = GameEngine(
        mock_input=["look", "look", "look", "quit"], max_history=2, ai_generator=fake_ai
    )
    engine.current_room = Room(name="Test Room", description="Test", exits=["north"])
    engine.game_loop()

    assert engine.history == ["look", "quit"]
