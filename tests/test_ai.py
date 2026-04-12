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
    # Test-only version of the prompt to ensure all variables are passed
    mock_load_prompt.return_value = (
        "ROOM: {room_type_name} | DESC: {room_type_desc} | EXITS: {exits_str} | "
        "ENEMIES: {enemies_str} | NPCS: {npcs_str} | "
        "ITEMS: {items_str} | CTX: {previous_context}"
    )
    mock_chat.return_value = MagicMock(message=MagicMock(content="AI Description"))

    result = AIGenerator().generate_room(floor=1, previous_context="Test Context")

    assert result["description"] == "AI Description"

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    assert prompt_sent == (
        "ROOM: Test Room | DESC: A dark place | EXITS: north, south | "
        "ENEMIES: Goblin | NPCS: Merchant | ITEMS: Potion | CTX: Test Context"
    )


@patch("game.ai.chat")
@patch("game.ai.load_prompt")
def test_narrate_item_use(mock_load_prompt: MagicMock, mock_chat: MagicMock) -> None:
    """Verify that item usage details are formatted into the narration prompt."""
    mock_load_prompt.return_value = (
        "ITEM: {item_name} | DESC: {item_description} | CTX: {room_context}"
    )
    mock_chat.return_value = MagicMock(message=MagicMock(content="Item Used"))

    result = AIGenerator().narrate_item_use("Potion", "Heals", "Dark Room")
    assert result == "Item Used"

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    assert prompt_sent == "ITEM: Potion | DESC: Heals | CTX: Dark Room"


@patch("game.ai.chat")
@patch("game.ai.load_prompt")
def test_generate_npc_response(
    mock_load_prompt: MagicMock, mock_chat: MagicMock
) -> None:
    """Validate that conversation history and NPC state are passed to the chat API."""
    mock_load_prompt.return_value = (
        "NPC: {npc_name} | CTX: {npc_context} | MSG: {player_message} | HIST: {history}"
    )
    mock_chat.return_value = MagicMock(message=MagicMock(content="Hello traveler"))

    result = AIGenerator().generate_npc_response("Merchant", "Sells", "Hello", "None")
    assert result == "Hello traveler"

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    assert prompt_sent == "NPC: Merchant | CTX: Sells | MSG: Hello | HIST: None"


@patch("game.ai.chat")
@patch("game.ai.load_prompt")
def test_narrate_combat(mock_load_prompt: MagicMock, mock_chat: MagicMock) -> None:
    """Ensure combat variables are substituted safely into the combat prompt."""
    mock_load_prompt.return_value = (
        "ACT: {player_action} | P_HP: {player_hp} | "
        "ENM: {enemy_name} | E_HP: {enemy_hp} | DMG: {damage_dealt}"
    )
    mock_chat.return_value = MagicMock(message=MagicMock(content="Slash!"))

    result = AIGenerator().narrate_combat("attacks", 100, "Goblin", 10, 5)
    assert result == "Slash!"

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    assert prompt_sent == "ACT: attacks | P_HP: 100 | ENM: Goblin | E_HP: 10 | DMG: 5"


@patch("game.ai.chat")
@patch("game.ai.load_prompt")
def test_generate_intro(mock_load_prompt: MagicMock, mock_chat: MagicMock) -> None:
    """Test that a haunting intro is correctly loaded and parsed from the LLM."""
    mock_load_prompt.return_value = "Test Intro Prompt"
    mock_chat.return_value = MagicMock(
        message=MagicMock(content="Welcome to the dungeon.")
    )

    result = AIGenerator().generate_intro()
    assert result == "Welcome to the dungeon."

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    assert prompt_sent == "Test Intro Prompt"


@patch("game.ai.chat")
def test_empty_ai_response(mock_chat: MagicMock) -> None:
    """Validate the game raises ValueError on empty Ollama response."""
    # Simulate an empty message content
    mock_chat.return_value = MagicMock(message=MagicMock(content=None))
    with pytest.raises(ValueError, match="AI returned an empty response."):
        AIGenerator().generate_intro()


@patch("game.ai.generate_mechanics")
@patch("game.ai.chat")
def test_generate_room_real_prompt(
    mock_chat: MagicMock, mock_gen_mechanics: MagicMock
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

    AIGenerator().generate_room(floor=1, previous_context="Test Context")

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
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


@patch("game.ai.chat")
def test_narrate_item_use_real_prompt(mock_chat: MagicMock) -> None:
    """Verify that item usage details are formatted into the real narration prompt."""
    mock_chat.return_value = MagicMock(message=MagicMock(content="Item Used"))

    AIGenerator().narrate_item_use("Potion", "Heals", "Dark Room")

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    expected_prompt = load_prompt("item_use.md").format(
        item_name="Potion",
        item_description="Heals",
        room_context="Dark Room",
    )
    assert prompt_sent == expected_prompt


@patch("game.ai.chat")
def test_generate_npc_response_real_prompt(mock_chat: MagicMock) -> None:
    """Validate history and NPC state are passed to the real chat API prompt."""
    mock_chat.return_value = MagicMock(message=MagicMock(content="Hello traveler"))

    AIGenerator().generate_npc_response("Merchant", "Sells", "Hello", "None")

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    expected_prompt = load_prompt("npc.md").format(
        npc_name="Merchant",
        npc_context="Sells",
        history="None",
        player_message="Hello",
    )
    assert prompt_sent == expected_prompt


@patch("game.ai.chat")
def test_narrate_combat_real_prompt(mock_chat: MagicMock) -> None:
    """Ensure combat variables are substituted safely into the real combat prompt."""
    mock_chat.return_value = MagicMock(message=MagicMock(content="Slash!"))

    AIGenerator().narrate_combat("attacks", 100, "Goblin", 10, 5)

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    expected_prompt = load_prompt("combat.md").format(
        player_action="attacks",
        player_hp=100,
        enemy_name="Goblin",
        enemy_hp=10,
        damage_dealt=5,
    )
    assert prompt_sent == expected_prompt


@patch("game.ai.chat")
def test_generate_intro_real_prompt(mock_chat: MagicMock) -> None:
    """Test that a haunting intro is correctly loaded from the real LLM prompt."""
    mock_chat.return_value = MagicMock(
        message=MagicMock(content="Welcome to the dungeon.")
    )

    AIGenerator().generate_intro()

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    expected_prompt = load_prompt("intro.md")
    assert prompt_sent == expected_prompt


@patch("game.ai.generate_final_room_mechanics")
@patch("game.ai.chat")
@patch("game.ai.load_prompt")
def test_generate_final_room(
    mock_load_prompt: MagicMock,
    mock_chat: MagicMock,
    mock_gen_final: MagicMock,
) -> None:
    """Verify final room mechanics are injected into the final_room prompt correctly."""
    mock_gen_final.return_value = {
        "room_type": {"name": "Throne of Bones", "description": "A hall of skulls"},
        "exits": ["south"],
        "enemies": [
            {
                "name": "The Lich King",
                "description": "Undead sorcerer",
                "is_boss": True,
            }
        ],
        "npcs": list[dict[str, str]](),
        "items": [{"name": "Magic Sword", "description": "Glows blue"}],
        "is_final_room": True,
    }
    mock_load_prompt.return_value = (
        "BOSS: {boss_name} | DESC: {boss_description} | ROOM: {room_type_name} | "
        "RDESC: {room_type_desc} | ITEMS: {items_str} | CTX: {previous_context}"
    )
    mock_chat.return_value = MagicMock(message=MagicMock(content="Final Room Desc"))

    result = AIGenerator().generate_final_room(
        floor=5, previous_context="Long journey", exits=["south"]
    )

    assert result["description"] == "Final Room Desc"
    assert result["is_final_room"] is True
    assert result["name"] == "Throne of Bones"

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    assert "The Lich King" in prompt_sent
    assert "Long journey" in prompt_sent
    assert "Magic Sword" in prompt_sent


@patch("game.ai.generate_final_room_mechanics")
@patch("game.ai.chat")
def test_generate_final_room_real_prompt(
    mock_chat: MagicMock,
    mock_gen_final: MagicMock,
) -> None:
    """Verify boss details are injected into the real final_room prompt."""
    mock_gen_final.return_value = {
        "room_type": {
            "name": "Sanctum of the Abyss",
            "description": "A void-ringed chamber",
        },
        "exits": ["north"],
        "enemies": [
            {
                "name": "Shadow Empress",
                "description": "A dark fey queen",
                "is_boss": True,
            }
        ],
        "npcs": list[dict[str, str]](),
        "items": list[dict[str, str]](),
        "is_final_room": True,
    }
    mock_chat.return_value = MagicMock(message=MagicMock(content="Darkness descends."))

    AIGenerator().generate_final_room(floor=3, previous_context="Test Journey")

    prompt_sent = mock_chat.call_args[1]["messages"][0]["content"]
    expected_prompt = load_prompt("final_room.md").format(
        previous_context="Test Journey",
        room_type_name="Sanctum of the Abyss",
        room_type_desc="A void-ringed chamber",
        boss_name="Shadow Empress",
        boss_description="A dark fey queen",
        items_str="None",
    )
    assert prompt_sent == expected_prompt
