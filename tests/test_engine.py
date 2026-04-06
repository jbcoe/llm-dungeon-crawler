"""Tests for the game engine logic."""

from typing import Any

from game.engine import GameEngine
from game.models import Room


def test_engine_initialization(mock_ai_api: Any) -> None:
    """Test that the engine initializes with correct player state."""
    mock_gen_room, _, _, _, _, _ = mock_ai_api
    engine = GameEngine(mock_input=["quit"])
    engine.start()

    assert engine.player.hp == 100
    assert engine.floor == 1
    assert engine.current_room is not None
    assert engine.current_room.description == "A mocked room."
    assert "north" in engine.current_room.exits
    mock_gen_room.assert_called_once()


def test_combat(mock_ai_api: Any) -> None:
    """Test combat mechanics and enemy death."""
    _, mock_narrate, _, _, _, _ = mock_ai_api
    engine = GameEngine(mock_input=["attack slime", "quit"])
    room = Room(
        description="Test",
        exits=["north"],
        enemies=[
            {
                "name": "Slime",
                "description": "test",
                "hp": 10,
                "max_hp": 10,
                "attack": 2,
            }
        ],
    )
    engine.current_room = room
    engine.game_loop()

    # Slime should have taken 10 damage from player's attack of 10 and died
    assert len(engine.current_room.enemies) == 0
    # Player takes no damage because slime died before it could attack
    assert engine.player.hp == 100
    mock_narrate.assert_called_once()


def test_talk(mock_ai_api: Any) -> None:
    """Test NPC interaction and dialogue."""
    _, _, mock_npc_resp, _, _, _ = mock_ai_api
    engine = GameEngine(mock_input=["talk merchant", "hello", "bye", "quit"])
    room = Room(
        description="Test",
        exits=["north"],
        npcs=[
            {
                "name": "Merchant",
                "description": "A merchant",
                "dialogue_context": "Friendly",
            }
        ],
    )
    engine.current_room = room
    engine.game_loop()

    mock_npc_resp.assert_called_once()


def test_autocompletion_options(mock_ai_api: Any) -> None:
    """Test that autocompletion returns expected command and entity words."""
    _ = mock_ai_api
    engine = GameEngine(mock_input=["quit"])
    room = Room(
        description="Test Room",
        exits=["north", "east"],
        enemies=[
            {
                "name": "Dark Elf",
                "description": "test",
                "hp": 10,
                "max_hp": 10,
                "attack": 2,
            }
        ],
        npcs=[{"name": "Old Wizard", "description": "test"}],
        items=[{"name": "Health Potion", "description": "test"}],
    )
    engine.current_room = room
    engine.player.inventory = [type("MockItem", (), {"name": "Rusty Sword"})()]

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


def test_history_tracking(mock_ai_api: Any) -> None:
    """Test that player commands are correctly tracked in history."""
    _ = mock_ai_api
    engine = GameEngine(mock_input=["look", "go north", "inventory", "quit"])
    engine.current_room = Room(description="Test", exits=["north"])
    # Mock enter_new_room so it doesn't try to generate a real room when moving
    engine.enter_new_room = lambda direction="forward": None
    engine.game_loop()

    assert engine.history == ["look", "go north", "inventory", "quit"]


def test_history_truncation(mock_ai_api: Any) -> None:
    """Test that command history is truncated according to max_history."""
    _ = mock_ai_api
    engine = GameEngine(mock_input=["look", "look", "look", "quit"], max_history=2)
    engine.current_room = Room(description="Test", exits=["north"])
    engine.game_loop()

    assert engine.history == ["look", "quit"]
