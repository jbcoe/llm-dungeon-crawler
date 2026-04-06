"""Shared test fixtures for the game."""

from typing import Generator, Any
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_ai_api() -> Generator[tuple[Any, ...], None, None]:
    """Mock the AI API calls and console output globally for all tests."""
    with (
        patch("game.engine.generate_room") as mock_gen_room,
        patch("game.engine.narrate_combat") as mock_narrate,
        patch("game.engine.generate_npc_response") as mock_npc_resp,
        patch("game.engine.generate_intro") as mock_intro,
        patch("game.engine.narrate_item_use") as mock_item_use,
        patch("game.engine.console.print") as mock_print,
    ):
        mock_gen_room.return_value = {
            "description": "A mocked room.",
            "room_type": {"name": "Mock Room", "description": "A mocked room."},
            "exits": ["north", "south"],
            "items": [],
            "enemies": [],
            "npcs": [],
        }
        mock_narrate.return_value = "Mocked combat narration."
        mock_npc_resp.return_value = "Mocked NPC response."
        mock_intro.return_value = "Mocked intro text."
        mock_item_use.return_value = "Mocked item usage narration."

        yield (
            mock_gen_room,
            mock_narrate,
            mock_npc_resp,
            mock_intro,
            mock_item_use,
            mock_print,
        )
