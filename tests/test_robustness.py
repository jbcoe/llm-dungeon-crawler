"""Tests for the improved engineering and robustness of the game."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from game.ai import AIGenerator
from game.engine import GameEngine, GameUI
from game.mechanics import generate_mechanics
from game.theme import Theme


@pytest.fixture
def theme(tmp_path: Path) -> Theme:
    """Fixture to create a minimal valid theme for testing."""
    theme_path = tmp_path / "test-theme"
    theme_path.mkdir()

    for f in ["enemies.md", "items.md", "npcs.md", "rooms.md"]:
        (theme_path / f).write_text("- Name: Desc\n")

    prompts_dir = theme_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "combat.md").write_text(
        "{player_action}{enemy_name}{damage_dealt}{enemy_hp}{player_hp}"
    )
    (prompts_dir / "intro.md").write_text("Test Intro Prompt")
    (prompts_dir / "item_use.md").write_text(
        "{item_name}{item_description}{room_context}"
    )
    (prompts_dir / "npc.md").write_text(
        "{npc_name}{npc_context}{history}{player_message}"
    )
    (prompts_dir / "rest.md").write_text("{player_hp}{player_max_hp}")
    (prompts_dir / "room.md").write_text(
        "{previous_context}{room_type_name}{room_type_desc}"
        "{exits_str}{enemies_str}{npcs_str}{items_str}"
    )

    return Theme.from_path(theme_path)


def test_robust_markdown_parsing(tmp_path: Path) -> None:
    """Test that the markdown parser handles different formats correctly."""
    mock_content = """
- Item 1 : Desc 1
 * Item 2:Desc 2
-   Item 3  :   Desc 3
"""
    theme_path = tmp_path / "test-theme"
    theme_path.mkdir()
    (theme_path / "enemies.md").write_text("- Enemy: Desc\n")
    (theme_path / "items.md").write_text(mock_content)
    (theme_path / "npcs.md").write_text("- NPC: Desc\n")
    (theme_path / "rooms.md").write_text("- Room: Desc\n")

    prompts_dir = theme_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "combat.md").write_text(
        "{player_action}{enemy_name}{damage_dealt}{enemy_hp}{player_hp}"
    )
    (prompts_dir / "intro.md").write_text("Test Intro Prompt")
    (prompts_dir / "item_use.md").write_text(
        "{item_name}{item_description}{room_context}"
    )
    (prompts_dir / "npc.md").write_text(
        "{npc_name}{npc_context}{history}{player_message}"
    )
    (prompts_dir / "rest.md").write_text("{player_hp}{player_max_hp}")
    (prompts_dir / "room.md").write_text(
        "{previous_context}{room_type_name}{room_type_desc}"
        "{exits_str}{enemies_str}{npcs_str}{items_str}"
    )

    theme = Theme.from_path(theme_path)

    assert len(theme.items) == 3
    assert theme.items[0] == {"name": "Item 1", "description": "Desc 1"}
    assert theme.items[1] == {"name": "Item 2", "description": "Desc 2"}
    assert theme.items[2] == {"name": "Item 3", "description": "Desc 3"}


def test_item_mechanics_balancing(tmp_path: Path) -> None:
    """Test that item mechanics are correctly balanced through generate_mechanics."""
    theme_path = tmp_path / "test-theme"
    theme_path.mkdir()
    (theme_path / "enemies.md").write_text("- Enemy: Desc\n")
    (theme_path / "npcs.md").write_text("- NPC: Desc\n")
    (theme_path / "rooms.md").write_text("- Room: Desc\n")

    prompts_dir = theme_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "combat.md").write_text(
        "{player_action}{enemy_name}{damage_dealt}{enemy_hp}{player_hp}"
    )
    (prompts_dir / "intro.md").write_text("Test Intro Prompt")
    (prompts_dir / "item_use.md").write_text(
        "{item_name}{item_description}{room_context}"
    )
    (prompts_dir / "npc.md").write_text(
        "{npc_name}{npc_context}{history}{player_message}"
    )
    (prompts_dir / "rest.md").write_text("{player_hp}{player_max_hp}")
    (prompts_dir / "room.md").write_text(
        "{previous_context}{room_type_name}{room_type_desc}"
        "{exits_str}{enemies_str}{npcs_str}{items_str}"
    )

    # Healing item
    (theme_path / "items.md").write_text("- Health Potion: Heals you. : healing\n")
    theme = Theme.from_path(theme_path)
    with patch("random.random", return_value=0.1):  # force item spawn
        mechanics = generate_mechanics(floor=1, theme=theme)
        assert len(mechanics["items"]) == 1
        assert mechanics["items"][0]["effect_type"] == "healing"
        assert mechanics["items"][0]["stat_effect"] >= 20

    # Weapon item
    (theme_path / "items.md").write_text("- Iron Sword: A sharp blade. : weapon\n")
    theme = Theme.from_path(theme_path)
    with patch("random.random", return_value=0.1):
        mechanics = generate_mechanics(floor=1, theme=theme)
        assert len(mechanics["items"]) == 1
        assert mechanics["items"][0]["effect_type"] == "weapon"
        assert mechanics["items"][0]["stat_effect"] == 7

    # Junk item
    (theme_path / "items.md").write_text("- Old Boot: Smelly.\n")
    theme = Theme.from_path(theme_path)
    with patch("random.random", return_value=0.1):
        mechanics = generate_mechanics(floor=1, theme=theme)
        assert len(mechanics["items"]) == 1
        assert mechanics["items"][0]["effect_type"] == "none"
        assert mechanics["items"][0]["stat_effect"] == 0


@patch("game.ai.chat")
def test_query_model_error_handling(mock_chat: MagicMock, theme: Theme) -> None:
    """Test that _query_model does not silently hide errors."""
    mock_chat.side_effect = Exception("AI Service Down")

    with pytest.raises(Exception, match="AI Service Down"):
        AIGenerator(model="test", theme=theme)._query_model("prompt")


@patch("game.ai.chat")
def test_query_model_empty_response(mock_chat: MagicMock, theme: Theme) -> None:
    """Test that _query_model raises an error on empty responses."""
    mock_response = MagicMock()
    mock_response.message.content = ""
    mock_chat.return_value = mock_response

    with pytest.raises(ValueError, match="AI returned an empty response."):
        AIGenerator(model="test", theme=theme)._query_model("prompt")


def test_engine_propagates_room_generation_error(theme: Theme) -> None:
    """Test that room generation errors propagate rather than silently falling back."""
    with patch(
        "game.ai.AIGenerator.generate_room", side_effect=Exception("API failure")
    ):
        engine = GameEngine(theme=theme, mock_input=["quit"])
        with pytest.raises(Exception, match="API failure"):
            engine.enter_new_room("start")


def test_ui_abstraction() -> None:
    """Verify that GameUI methods correctly proxy calls to the console."""
    mock_console = MagicMock()
    ui = GameUI(console=mock_console)

    ui.print("Hello", style="bold")
    mock_console.print.assert_called_with("Hello", style="bold", markup=True)

    ui.print_error("Danger")
    mock_console.print.assert_called_with("Danger", style="red", markup=False)
