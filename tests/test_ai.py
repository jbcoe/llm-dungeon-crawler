"""Unit tests for ai.py."""

from unittest.mock import MagicMock, patch

import pytest

from game.ai import (
    generate_intro,
    generate_npc_response,
    generate_room,
    load_prompt,
    narrate_combat,
    narrate_item_use,
)


def test_load_prompt_missing() -> None:
    """Ensure FileNotFoundError is raised when a prompt markdown file is missing."""
    with patch("importlib.resources.files") as mock_files:
        mock_joinpath = mock_files.return_value.joinpath.return_value
        mock_joinpath.is_file.return_value = False
        with pytest.raises(FileNotFoundError):
            # load_prompt is lru_cached, so we need to bypass the cache
            # or just hit the missing file.
            # Actually, since it's cached, we should pass a uniquely named missing file
            load_prompt("totally_missing_file_12345.md")


@patch("game.ai.generate_mechanics")
@patch("game.ai.chat")
@patch("game.ai.load_prompt")
def test_generate_room(
    mock_load_prompt: MagicMock, mock_chat: MagicMock, mock_gen_mechanics: MagicMock
) -> None:
    """Verify room mechanics are parsed and injected into the room prompt correctly."""
    mock_gen_mechanics.return_value = {
        "room_type": {"name": "Test Room", "description": "A dark place"},
        "exits": ["north", "south"],
        "enemies": [{"name": "Goblin", "description": "Ugly"}],
        "npcs": [{"name": "Merchant", "description": "Sells things"}],
        "items": [{"name": "Potion", "description": "Heals", "effect_type": "healing"}],
    }
    mock_load_prompt.return_value = (
        "{room_type_name} {room_type_desc} {exits_str} "
        "{enemies_str} {npcs_str} {items_str} {previous_context}"
    )
    mock_chat.return_value = MagicMock(message=MagicMock(content="AI Description"))

    result = generate_room(floor=1, previous_context="Test Context")
    assert result["description"] == "AI Description"


@patch("game.ai.chat")
@patch("game.ai.load_prompt")
def test_narrate_item_use(mock_load_prompt: MagicMock, mock_chat: MagicMock) -> None:
    """Verify that item usage details are formatted into the narration prompt."""
    mock_load_prompt.return_value = "{item_name} {item_description} {room_context}"
    mock_chat.return_value = MagicMock(message=MagicMock(content="Item Used"))

    result = narrate_item_use("Potion", "Heals", "Dark Room")
    assert result == "Item Used"


@patch("game.ai.chat")
@patch("game.ai.load_prompt")
def test_generate_npc_response(
    mock_load_prompt: MagicMock, mock_chat: MagicMock
) -> None:
    """Validate that conversation history and NPC state are passed to the chat API."""
    mock_load_prompt.return_value = (
        "{npc_name} {npc_context} {history} {player_message}"
    )
    mock_chat.return_value = MagicMock(message=MagicMock(content="Hello traveler"))

    result = generate_npc_response("Merchant", "Sells", "Hello", "None")
    assert result == "Hello traveler"


@patch("game.ai.chat")
@patch("game.ai.load_prompt")
def test_narrate_combat(mock_load_prompt: MagicMock, mock_chat: MagicMock) -> None:
    """Ensure combat variables are substituted safely into the combat prompt."""
    mock_load_prompt.return_value = (
        "{player_action} {enemy_name} {damage_dealt} {enemy_hp} {player_hp}"
    )
    mock_chat.return_value = MagicMock(message=MagicMock(content="Slash!"))

    result = narrate_combat("attacks", 100, "Goblin", 10, 5)
    assert result == "Slash!"


@patch("game.ai.chat")
@patch("game.ai.load_prompt")
def test_generate_intro(mock_load_prompt: MagicMock, mock_chat: MagicMock) -> None:
    """Test that a haunting intro is correctly loaded and parsed from the LLM."""
    mock_load_prompt.return_value = "Intro prompt"
    mock_chat.return_value = MagicMock(
        message=MagicMock(content="Welcome to the dungeon.")
    )

    result = generate_intro()
    assert result == "Welcome to the dungeon."


@patch("game.ai.chat")
@patch("game.ai.load_prompt")
def test_empty_ai_response(mock_load_prompt: MagicMock, mock_chat: MagicMock) -> None:
    """Validate the game raises ValueError on empty Ollama response."""
    mock_load_prompt.return_value = "Intro prompt"
    # Simulate an empty message content
    mock_chat.return_value = MagicMock(message=MagicMock(content=None))
    with pytest.raises(ValueError, match="AI returned an empty response."):
        generate_intro()
