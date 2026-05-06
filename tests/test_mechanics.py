"""Unit tests for mechanics.py."""

from pathlib import Path
from unittest.mock import patch

import pytest

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


def test_generate_mechanics_empty_exits(theme: Theme) -> None:
    """Verify that an empty list of exits is treated as None."""
    # When exits=[], it should generate random exits
    mechanics = generate_mechanics(floor=1, exits=[], theme=theme)
    assert len(mechanics["exits"]) > 0
    assert all(e in ["north", "south", "east", "west"] for e in mechanics["exits"])


def test_generate_mechanics(tmp_path: Path) -> None:
    """Validate procedural room generation structure and probabilities."""
    theme_path = tmp_path / "test-theme"
    theme_path.mkdir()
    (theme_path / "enemies.md").write_text("- Goblin: Ugly\n")
    (theme_path / "npcs.md").write_text("- Merchant: Sells\n")
    (theme_path / "items.md").write_text("- Health Potion: Heals\n")
    (theme_path / "rooms.md").write_text("- Cave: Dark\n")

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

    # Test generation and make sure we get the expected types and structure.
    with patch("random.random", return_value=0.1):  # force items and enemies to spawn
        mechanics = generate_mechanics(floor=1, theme=theme)

        assert mechanics["room_type"] == {"name": "Cave", "description": "Dark"}
        assert len(mechanics["enemies"]) == 1
        assert mechanics["enemies"][0]["name"] == "Goblin"
        assert len(mechanics["npcs"]) == 0
        assert len(mechanics["items"]) == 1
        assert mechanics["items"][0]["name"] == "Health Potion"
        assert mechanics["items"][0]["effect_type"] == "healing"

    with patch("random.random", return_value=0.1):  # force npcs to spawn
        # Re-load theme with no enemies to test NPC spawning
        (theme_path / "enemies.md").write_text("")
        theme = Theme.from_path(theme_path)
        mechanics = generate_mechanics(floor=1, theme=theme)
        assert len(mechanics["enemies"]) == 0
        assert len(mechanics["npcs"]) == 1
        assert mechanics["npcs"][0]["name"] == "Merchant"

    with patch("random.random", return_value=0.9):  # force nothing to spawn
        # Restore enemies file and re-load
        (theme_path / "enemies.md").write_text("- Goblin: Ugly\n")
        theme = Theme.from_path(theme_path)
        mechanics = generate_mechanics(floor=1, theme=theme)
        assert len(mechanics["enemies"]) == 0
        assert len(mechanics["npcs"]) == 0
        assert len(mechanics["items"]) == 0


def test_generate_mechanics_weapons(tmp_path: Path) -> None:
    """Ensure weapons generated procedurally have valid weapon effects."""
    theme_path = tmp_path / "test-theme"
    theme_path.mkdir()
    (theme_path / "enemies.md").write_text("- Enemy: Desc\n")
    (theme_path / "npcs.md").write_text("- NPC: Desc\n")
    (theme_path / "items.md").write_text("- Iron Sword: Sharp\n")
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

    with patch("random.random", return_value=0.1):  # item will spawn
        mechanics = generate_mechanics(floor=2, theme=theme)
        assert len(mechanics["items"]) == 1
        assert mechanics["items"][0]["effect_type"] == "weapon"
        assert mechanics["items"][0]["stat_effect"] > 0


def test_generate_mechanics_junk(tmp_path: Path) -> None:
    """Verify random flavor items lack mechanical combat properties."""
    theme_path = tmp_path / "test-theme"
    theme_path.mkdir()
    (theme_path / "enemies.md").write_text("- Enemy: Desc\n")
    (theme_path / "npcs.md").write_text("- NPC: Desc\n")
    (theme_path / "items.md").write_text("- Random Junk: Junk\n")
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

    with patch("random.random", return_value=0.1):  # item will spawn
        mechanics = generate_mechanics(floor=2, theme=theme)
        assert len(mechanics["items"]) == 1
        assert mechanics["items"][0]["effect_type"] == "none"
        assert mechanics["items"][0]["stat_effect"] == 0
