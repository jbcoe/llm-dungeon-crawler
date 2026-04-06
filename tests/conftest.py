"""Shared test fixtures for the game."""

from typing import Any, Generator
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_ai_api() -> Generator[tuple[Any, ...], None, None]:
    """Mock the AI API calls and console output for tests."""
    with (
        patch("game.engine.generate_room") as mock_gen_room,
        patch("game.engine.narrate_combat") as mock_narrate,
        patch("game.engine.generate_npc_response") as mock_npc_resp,
        patch("game.engine.generate_intro") as mock_intro,
        patch("game.engine.narrate_item_use") as mock_item_use,
        patch("game.engine.GameUI.print") as mock_print,
    ):
        mock_room_data: dict[str, Any] = {
            "description": "A mocked room.",
            "room_type": {"name": "Mock Room", "description": "A mocked room."},
            "exits": ["north", "south"],
            "items": list[dict[str, Any]](),
            "enemies": list[dict[str, Any]](),
            "npcs": list[dict[str, Any]](),
        }
        mock_gen_room.return_value = mock_room_data
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
