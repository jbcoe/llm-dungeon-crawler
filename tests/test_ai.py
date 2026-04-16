"""Unit tests for ai.py."""

from unittest.mock import MagicMock, patch

import pytest

from game.ai import AIGenerator, load_prompt


def test_load_prompt_missing() -> None:
    """Ensure FileNotFoundError is raised when a prompt markdown file is missing."""
    with patch("importlib.resources.files") as mock_files:
        mock_joinpath = mock_files.return_value.joinpath.return_value
        mock_joinpath.is_file.return_value = False
        with pytest.raises(FileNotFoundError):
            load_prompt("totally_missing_file_12345.md")


def _make_chat_response(content: str) -> MagicMock:
    """Build a minimal mock that looks like an openai ChatCompletion response."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


@patch("game.ai.generate_mechanics")
@patch("game.ai.load_prompt")
def test_generate_room(
    mock_load_prompt: MagicMock, mock_gen_mechanics: MagicMock
) -> None:
    """Verify room mechanics are parsed and injected into the room prompt correctly."""
    mock_gen_mechanics.return_value = {
        "room_type": {"name": "Test Room", "description": "A dark place"},
        "exits": ["north", "south"],
        "enemies": [{"name": "Goblin", "description": "Ugly"}],
        "npcs": [{"name": "Merchant", "description": "Sells things"}],
        "items": [{"name": "Potion", "description": "Heals", "effect_type": "healing"}],
    }
    # Test-only version of the prompt to ensure all variables are passed
    mock_load_prompt.return_value = (
        "ROOM: {room_type_name} | DESC: {room_type_desc} | EXITS: {exits_str} | "
        "ENEMIES: {enemies_str} | NPCS: {npcs_str} | "
        "ITEMS: {items_str} | CTX: {previous_context}"
    )

    ai = AIGenerator()
    ai.client = MagicMock()
    ai.client.chat.completions.create.return_value = _make_chat_response(
        "AI Description"
    )

    result = ai.generate_room(floor=1, previous_context="Test Context")

    assert result["description"] == "AI Description"

    call_kwargs = ai.client.chat.completions.create.call_args[1]
    prompt_sent = call_kwargs["messages"][0]["content"]
    assert prompt_sent == (
        "ROOM: Test Room | DESC: A dark place | EXITS: north, south | "
        "ENEMIES: Goblin | NPCS: Merchant | ITEMS: Potion | CTX: Test Context"
    )


@patch("game.ai.load_prompt")
def test_narrate_item_use(mock_load_prompt: MagicMock) -> None:
    """Verify that item usage details are formatted into the narration prompt."""
    mock_load_prompt.return_value = (
        "ITEM: {item_name} | DESC: {item_description} | CTX: {room_context}"
    )

    ai = AIGenerator()
    ai.client = MagicMock()
    ai.client.chat.completions.create.return_value = _make_chat_response("Item Used")

    result = ai.narrate_item_use("Potion", "Heals", "Dark Room")
    assert result == "Item Used"

    call_kwargs = ai.client.chat.completions.create.call_args[1]
    prompt_sent = call_kwargs["messages"][0]["content"]
    assert prompt_sent == "ITEM: Potion | DESC: Heals | CTX: Dark Room"


@patch("game.ai.load_prompt")
def test_generate_npc_response(mock_load_prompt: MagicMock) -> None:
    """Validate that conversation history and NPC state are passed to the chat API."""
    mock_load_prompt.return_value = (
        "NPC: {npc_name} | CTX: {npc_context} | MSG: {player_message} | HIST: {history}"
    )

    ai = AIGenerator()
    ai.client = MagicMock()
    ai.client.chat.completions.create.return_value = _make_chat_response(
        "Hello traveler"
    )

    result = ai.generate_npc_response("Merchant", "Sells", "Hello", "None")
    assert result == "Hello traveler"

    call_kwargs = ai.client.chat.completions.create.call_args[1]
    prompt_sent = call_kwargs["messages"][0]["content"]
    assert prompt_sent == "NPC: Merchant | CTX: Sells | MSG: Hello | HIST: None"


@patch("game.ai.load_prompt")
def test_narrate_combat(mock_load_prompt: MagicMock) -> None:
    """Ensure combat variables are substituted safely into the combat prompt."""
    mock_load_prompt.return_value = (
        "ACT: {player_action} | P_HP: {player_hp} | "
        "ENM: {enemy_name} | E_HP: {enemy_hp} | DMG: {damage_dealt}"
    )

    ai = AIGenerator()
    ai.client = MagicMock()
    ai.client.chat.completions.create.return_value = _make_chat_response("Slash!")

    result = ai.narrate_combat("attacks", 100, "Goblin", 10, 5)
    assert result == "Slash!"

    call_kwargs = ai.client.chat.completions.create.call_args[1]
    prompt_sent = call_kwargs["messages"][0]["content"]
    assert prompt_sent == "ACT: attacks | P_HP: 100 | ENM: Goblin | E_HP: 10 | DMG: 5"


@patch("game.ai.load_prompt")
def test_generate_intro(mock_load_prompt: MagicMock) -> None:
    """Test that a haunting intro is correctly loaded and parsed from the LLM."""
    mock_load_prompt.return_value = "Test Intro Prompt"

    ai = AIGenerator()
    ai.client = MagicMock()
    ai.client.chat.completions.create.return_value = _make_chat_response(
        "Welcome to the dungeon."
    )

    result = ai.generate_intro()
    assert result == "Welcome to the dungeon."

    call_kwargs = ai.client.chat.completions.create.call_args[1]
    prompt_sent = call_kwargs["messages"][0]["content"]
    assert prompt_sent == "Test Intro Prompt"


def test_empty_ai_response() -> None:
    """Validate the game raises ValueError on empty llama-server response."""
    ai = AIGenerator()
    ai.client = MagicMock()
    ai.client.chat.completions.create.return_value = _make_chat_response("")

    with pytest.raises(ValueError, match="AI returned an empty response."):
        ai.generate_intro()


@patch("game.ai.generate_mechanics")
def test_generate_room_real_prompt(mock_gen_mechanics: MagicMock) -> None:
    """Verify mechanics are parsed and injected into the real room prompt correctly."""
    mock_gen_mechanics.return_value = {
        "room_type": {"name": "Test Room", "description": "A dark place"},
        "exits": ["north", "south"],
        "enemies": [{"name": "Goblin", "description": "Ugly"}],
        "npcs": [{"name": "Merchant", "description": "Sells things"}],
        "items": [{"name": "Potion", "description": "Heals", "effect_type": "healing"}],
    }

    ai = AIGenerator()
    ai.client = MagicMock()
    ai.client.chat.completions.create.return_value = _make_chat_response(
        "AI Description"
    )

    ai.generate_room(floor=1, previous_context="Test Context")

    call_kwargs = ai.client.chat.completions.create.call_args[1]
    prompt_sent = call_kwargs["messages"][0]["content"]
    expected_prompt = load_prompt("room.md").format(
        previous_context="Test Context",
        room_type_name="Test Room",
        room_type_desc="A dark place",
        exits_str="north, south",
        enemies_str="Goblin",
        npcs_str="Merchant",
        items_str="Potion",
    )
    assert prompt_sent == expected_prompt


def test_narrate_item_use_real_prompt() -> None:
    """Verify that item usage details are formatted into the real narration prompt."""
    ai = AIGenerator()
    ai.client = MagicMock()
    ai.client.chat.completions.create.return_value = _make_chat_response("Item Used")

    ai.narrate_item_use("Potion", "Heals", "Dark Room")

    call_kwargs = ai.client.chat.completions.create.call_args[1]
    prompt_sent = call_kwargs["messages"][0]["content"]
    expected_prompt = load_prompt("item_use.md").format(
        item_name="Potion",
        item_description="Heals",
        room_context="Dark Room",
    )
    assert prompt_sent == expected_prompt


def test_generate_npc_response_real_prompt() -> None:
    """Validate history and NPC state are passed to the real chat API prompt."""
    ai = AIGenerator()
    ai.client = MagicMock()
    ai.client.chat.completions.create.return_value = _make_chat_response(
        "Hello traveler"
    )

    ai.generate_npc_response("Merchant", "Sells", "Hello", "None")

    call_kwargs = ai.client.chat.completions.create.call_args[1]
    prompt_sent = call_kwargs["messages"][0]["content"]
    expected_prompt = load_prompt("npc.md").format(
        npc_name="Merchant",
        npc_context="Sells",
        history="None",
        player_message="Hello",
    )
    assert prompt_sent == expected_prompt


def test_narrate_combat_real_prompt() -> None:
    """Ensure combat variables are substituted safely into the real combat prompt."""
    ai = AIGenerator()
    ai.client = MagicMock()
    ai.client.chat.completions.create.return_value = _make_chat_response("Slash!")

    ai.narrate_combat("attacks", 100, "Goblin", 10, 5)

    call_kwargs = ai.client.chat.completions.create.call_args[1]
    prompt_sent = call_kwargs["messages"][0]["content"]
    expected_prompt = load_prompt("combat.md").format(
        player_action="attacks",
        player_hp=100,
        enemy_name="Goblin",
        enemy_hp=10,
        damage_dealt=5,
    )
    assert prompt_sent == expected_prompt


def test_generate_intro_real_prompt() -> None:
    """Test that a haunting intro is correctly loaded from the real LLM prompt."""
    ai = AIGenerator()
    ai.client = MagicMock()
    ai.client.chat.completions.create.return_value = _make_chat_response(
        "Welcome to the dungeon."
    )

    ai.generate_intro()

    call_kwargs = ai.client.chat.completions.create.call_args[1]
    prompt_sent = call_kwargs["messages"][0]["content"]
    expected_prompt = load_prompt("intro.md")
    assert prompt_sent == expected_prompt
