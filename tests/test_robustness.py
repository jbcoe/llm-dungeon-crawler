"""Tests for the improved engineering and robustness of the game."""

from unittest.mock import MagicMock, patch

import pytest

from game.ai import AIGenerator
from game.engine import GameEngine, GameUI
from game.mechanics import generate_mechanics, load_data


def test_robust_markdown_parsing() -> None:
    """Test that the markdown parser handles different formats correctly."""
    mock_content = """
- Item 1 : Desc 1
 * Item 2:Desc 2
-   Item 3  :   Desc 3
Invalid line
- Only Name
"""
    with patch("importlib.resources.files") as mock_files:
        mock_file = MagicMock()
        mock_file.read_text.return_value = mock_content
        mock_file.is_file.return_value = True
        mock_files.return_value.joinpath.return_value = mock_file

        data = load_data("test.md")

        assert len(data) == 3
        assert data[0] == {"name": "Item 1", "description": "Desc 1"}
        assert data[1] == {"name": "Item 2", "description": "Desc 2"}
        assert data[2] == {"name": "Item 3", "description": "Desc 3"}


def test_item_mechanics_balancing() -> None:
    """Test that item mechanics are correctly balanced through generate_mechanics."""
    with (
        patch("game.mechanics.ENEMIES", []),
        patch("game.mechanics.NPCS", []),
        patch("game.mechanics.ROOMS", [{"name": "Cave", "description": "Dark"}]),
    ):
        # Healing item
        healing_item = [{"name": "Health Potion", "description": "Heals you."}]
        with patch("game.mechanics.ITEMS", healing_item):
            with patch("random.random", return_value=0.1):  # force item spawn
                mechanics = generate_mechanics(floor=1)
                assert len(mechanics["items"]) == 1
                assert mechanics["items"][0]["effect_type"] == "healing"
                assert mechanics["items"][0]["stat_effect"] >= 20

        # Weapon item
        weapon_item = [{"name": "Iron Sword", "description": "A sharp blade."}]
        with patch("game.mechanics.ITEMS", weapon_item):
            with patch("random.random", return_value=0.1):
                mechanics = generate_mechanics(floor=1)
                assert len(mechanics["items"]) == 1
                assert mechanics["items"][0]["effect_type"] == "weapon"
                assert mechanics["items"][0]["stat_effect"] == 7

        # Junk item
        junk_item = [{"name": "Old Boot", "description": "Smelly."}]
        with patch("game.mechanics.ITEMS", junk_item):
            with patch("random.random", return_value=0.1):
                mechanics = generate_mechanics(floor=1)
                assert len(mechanics["items"]) == 1
                assert mechanics["items"][0]["effect_type"] == "none"
                assert mechanics["items"][0]["stat_effect"] == 0


def test_query_model_error_handling() -> None:
    """Test that _query_model does not silently hide errors."""
    ai = AIGenerator()
    ai.client = MagicMock()
    ai.client.chat.completions.create.side_effect = Exception("AI Service Down")

    with pytest.raises(Exception, match="AI Service Down"):
        ai._query_model("prompt")


def test_query_model_empty_response() -> None:
    """Test that _query_model raises an error on empty responses."""
    ai = AIGenerator()
    ai.client = MagicMock()
    choice = MagicMock()
    choice.message.content = ""
    ai.client.chat.completions.create.return_value = MagicMock(choices=[choice])

    with pytest.raises(ValueError, match="AI returned an empty response."):
        ai._query_model("prompt")


def test_engine_fallback_on_bad_room_generation() -> None:
    """Test that the engine recovers if room generation fails."""
    with patch(
        "game.ai.AIGenerator.generate_room", side_effect=Exception("API failure")
    ):
        engine = GameEngine(mock_input=["quit"])
        # Call enter_new_room to trigger room generation and the fallback logic
        engine.enter_new_room("start")

        assert engine.current_room is not None
        assert engine.current_room.description == "A non-descript stone chamber."


def test_ui_abstraction() -> None:
    """Test that GameUI correctly abstracts console calls."""
    mock_console = MagicMock()
    ui = GameUI(console=mock_console)

    ui.print("Hello", style="bold")
    mock_console.print.assert_called_with("Hello", style="bold", markup=True)

    ui.print_error("Danger")
    mock_console.print.assert_called_with("Danger", style="red", markup=False)
