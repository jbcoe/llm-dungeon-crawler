"""Tests for the improved engineering and robustness of the game."""

from unittest.mock import MagicMock, patch

import pytest

from game.ai import _safe_ai_call
from game.engine import GameEngine, GameUI
from game.mechanics import _get_item_mechanics, load_data


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
    """Test that item mechanics are correctly balanced and typed."""
    healing_item = {"name": "Large Health Potion", "description": "Heals you."}
    weapon_item = {"name": "Iron Sword", "description": "A sharp blade."}
    junk_item = {"name": "Old Boot", "description": "Smelly."}

    h_mech = _get_item_mechanics(healing_item, floor=1)
    assert h_mech["effect_type"] == "healing"
    assert h_mech["stat_effect"] >= 20

    w_mech = _get_item_mechanics(weapon_item, floor=1)
    assert w_mech["effect_type"] == "weapon"
    assert w_mech["stat_effect"] == 7

    j_mech = _get_item_mechanics(junk_item, floor=1)
    assert j_mech["effect_type"] == "none"
    assert j_mech["stat_effect"] == 0


@patch("game.ai.chat")
def test_safe_ai_call_error_handling(mock_chat: MagicMock) -> None:
    """Test that _safe_ai_call does not silently hide errors."""
    mock_chat.side_effect = Exception("AI Service Down")

    with pytest.raises(Exception, match="AI Service Down"):
        _safe_ai_call("model", "prompt")


@patch("game.ai.chat")
def test_safe_ai_call_empty_response(mock_chat: MagicMock) -> None:
    """Test that _safe_ai_call raises an error on empty responses."""
    mock_response = MagicMock()
    mock_response.message.content = ""
    mock_chat.return_value = mock_response

    with pytest.raises(ValueError, match="AI returned an empty response."):
        _safe_ai_call("model", "prompt")


def test_engine_fallback_on_bad_room_generation() -> None:
    """Test that the engine recovers if room generation fails."""
    with patch("game.engine.generate_room", side_effect=Exception("API failure")):
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
