"""Unit tests for ai.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from game.ai import AIGenerator
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


@patch("game.ai.generate_mechanics")
@patch("game.ai.chat")
def test_generate_room(
    mock_chat: MagicMock, mock_gen_mechanics: MagicMock, theme: Theme
) -> None:
    """Verify room mechanics are parsed and injected into the room prompt correctly."""
    mock_gen_mechanics.return_value = {
        "room_type": {"name": "Test Room", "description": "A dark place"},
        "exits": ["north", "south"],
        "enemies": [{"name": "Goblin", "description": "Ugly"}],
        "npcs": [{"name": "Merchant", "description": "Sells things"}],
        "items": [{"name": "Potion", "description": "Heals", "effect_type": "healing"}],
    }
    mock_chat.return_value = MagicMock(message=MagicMock(content="AI Description"))

    result = AIGenerator(model="test", theme=theme).generate_room(
        floor=1, previous_context="Test Context"
    )

    assert result["description"] == "AI Description"

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    assert "Test Room" in prompt_sent
    assert "A dark place" in prompt_sent
    assert "north, south" in prompt_sent
    assert "Goblin" in prompt_sent
    assert "Merchant" in prompt_sent
    assert "Potion" in prompt_sent
    assert "Test Context" in prompt_sent


@patch("game.ai.chat")
def test_narrate_item_use(mock_chat: MagicMock, theme: Theme) -> None:
    """Verify that item usage details are formatted into the narration prompt."""
    mock_chat.return_value = MagicMock(message=MagicMock(content="Item Used"))

    result = AIGenerator(model="test", theme=theme).narrate_item_use(
        "Potion", "Heals", "Dark Room"
    )
    assert result == "Item Used"

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    assert "Potion" in prompt_sent
    assert "Heals" in prompt_sent
    assert "Dark Room" in prompt_sent


@patch("game.ai.chat")
def test_generate_npc_response(mock_chat: MagicMock, theme: Theme) -> None:
    """Validate that conversation history and NPC state are passed to the chat API."""
    mock_chat.return_value = MagicMock(message=MagicMock(content="Hello traveler"))

    result = AIGenerator(model="test", theme=theme).generate_npc_response(
        "Merchant", "Sells", "Hello", "None"
    )
    assert result == "Hello traveler"

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    assert "Merchant" in prompt_sent
    assert "Sells" in prompt_sent
    assert "Hello" in prompt_sent
    assert "None" in prompt_sent


@patch("game.ai.chat")
def test_narrate_combat(mock_chat: MagicMock, theme: Theme) -> None:
    """Ensure combat variables are substituted safely into the combat prompt."""
    mock_chat.return_value = MagicMock(message=MagicMock(content="Slash!"))

    result = AIGenerator(model="test", theme=theme).narrate_combat(
        "attacks", 100, "Goblin", 10, 5
    )
    assert result == "Slash!"

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    assert "attacks" in prompt_sent
    assert "100" in prompt_sent
    assert "Goblin" in prompt_sent
    assert "10" in prompt_sent
    assert "5" in prompt_sent


@patch("game.ai.chat")
def test_generate_intro(mock_chat: MagicMock, theme: Theme) -> None:
    """Test that a haunting intro is correctly loaded and parsed from the LLM."""
    mock_chat.return_value = MagicMock(
        message=MagicMock(content="Welcome to the dungeon.")
    )

    result = AIGenerator(model="test", theme=theme).generate_intro()
    assert result == "Welcome to the dungeon."

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    assert prompt_sent == "Test Intro Prompt"


@patch("game.ai.chat")
def test_empty_ai_response(mock_chat: MagicMock, theme: Theme) -> None:
    """Validate the game raises ValueError on empty Ollama response."""
    # Simulate an empty message content
    mock_chat.return_value = MagicMock(message=MagicMock(content=None))
    with pytest.raises(ValueError, match="AI returned an empty response."):
        AIGenerator(model="test", theme=theme).generate_intro()


@patch("game.ai.generate_mechanics")
@patch("game.ai.chat")
def test_generate_room_real_prompt(
    mock_chat: MagicMock, mock_gen_mechanics: MagicMock, theme: Theme
) -> None:
    """Verify mechanics are parsed and injected into the real room prompt correctly."""
    mock_gen_mechanics.return_value = {
        "room_type": {"name": "Test Room", "description": "A dark place"},
        "exits": ["north", "south"],
        "enemies": [{"name": "Goblin", "description": "Ugly"}],
        "npcs": [{"name": "Merchant", "description": "Sells things"}],
        "items": [{"name": "Potion", "description": "Heals", "effect_type": "healing"}],
    }
    mock_chat.return_value = MagicMock(message=MagicMock(content="AI Description"))

    AIGenerator(model="test", theme=theme).generate_room(
        floor=1, previous_context="Test Context"
    )

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    expected_prompt = theme.room_prompt.format(
        previous_context="Test Context",
        room_type_name="Test Room",
        room_type_desc="A dark place",
        exits_str="north, south",
        enemies_str="Goblin",
        npcs_str="Merchant",
        items_str="Potion",
    )
    assert prompt_sent == expected_prompt


@patch("game.ai.chat")
def test_generate_npc_response_real_prompt(mock_chat: MagicMock, theme: Theme) -> None:
    """Validate history and NPC state are passed to the real chat API prompt."""
    mock_chat.return_value = MagicMock(message=MagicMock(content="Hello traveler"))

    AIGenerator(model="test", theme=theme).generate_npc_response(
        "Merchant", "Sells", "Hello", "None"
    )

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    expected_prompt = theme.npc_prompt.format(
        npc_name="Merchant",
        npc_context="Sells",
        history="None",
        player_message="Hello",
    )
    assert prompt_sent == expected_prompt


@patch("game.ai.chat")
def test_narrate_combat_real_prompt(mock_chat: MagicMock, theme: Theme) -> None:
    """Ensure combat variables are substituted safely into the real combat prompt."""
    mock_chat.return_value = MagicMock(message=MagicMock(content="Slash!"))

    AIGenerator(model="test", theme=theme).narrate_combat(
        "attacks", 100, "Goblin", 10, 5
    )

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    expected_prompt = theme.combat_prompt.format(
        player_action="attacks",
        player_hp=100,
        enemy_name="Goblin",
        enemy_hp=10,
        damage_dealt=5,
    )
    assert prompt_sent == expected_prompt


@patch("game.ai.chat")
def test_generate_intro_real_prompt(mock_chat: MagicMock, theme: Theme) -> None:
    """Test that a haunting intro is correctly loaded from the real LLM prompt."""
    mock_chat.return_value = MagicMock(
        message=MagicMock(content="Welcome to the dungeon.")
    )

    AIGenerator(model="test", theme=theme).generate_intro()

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    assert prompt_sent == theme.intro_prompt


@patch("game.ai.chat")
def test_narrate_item_use_real_prompt(mock_chat: MagicMock, theme: Theme) -> None:
    """Verify that item usage details are formatted into the real narration prompt."""
    mock_chat.return_value = MagicMock(message=MagicMock(content="Item Used"))

    AIGenerator(model="test", theme=theme).narrate_item_use(
        "Potion", "Heals", "Dark Room"
    )

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    expected_prompt = theme.item_use_prompt.format(
        item_name="Potion",
        item_description="Heals",
        room_context="Dark Room",
    )
    assert prompt_sent == expected_prompt
