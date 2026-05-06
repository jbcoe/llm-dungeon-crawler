"""Tests for grid consistency in the pre-generated map layout."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from game.engine import GameEngine
from game.theme import Theme


@pytest.fixture
def theme() -> Theme:
    """Return a pre-loaded Dark Fantasy theme."""
    return Theme.from_path(Path("themes/dark-fantasy"))


def test_bidirectional_exits(theme: Theme) -> None:
    """Verify that moving into a new room follows the pre-generated map correctly."""
    # Using a fixed seed ensures predictable map generation for testing
    engine = GameEngine(
        theme=theme,
        model="test-model",
        map_size=8,
        map_seed=42,
    )
    engine.ai._query_model = MagicMock(return_value="A test room description.")

    # Start at (1, 1).
    with patch("random.random", return_value=0.9):
        engine.enter_new_room("start")

    current_room = engine.current_room
    assert current_room is not None
    first_exit = current_room.exits[0]

    # Map opposite directions
    opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}

    # Move to the adjacent room
    with patch("random.random", return_value=0.9):
        engine.handle_go(["go", first_exit])

    new_room = engine.current_room
    assert new_room is not None
    assert new_room != current_room

    # Check that the new room has an exit back to the previous one
    assert opposite[first_exit] in new_room.exits


def test_complex_grid_consistency(theme: Theme) -> None:
    """Verify that Map generates internally consistent, bidirectional grids."""
    engine = GameEngine(
        theme=theme,
        model="test-model",
        map_size=8,
        map_seed=42,
    )

    dungeon_map = engine.map_grid

    # Iterate through every cell in the map
    for x in range(dungeon_map.size):
        for y in range(dungeon_map.size):
            # If this is a path cell...
            if dungeon_map.space[x, y]:
                exits = dungeon_map.get_exits(x, y)

                # For every exit from this cell...
                for direction_name in exits:
                    # Get target coordinates
                    dx, dy = 0, 0
                    if direction_name == "north":
                        dy = 1
                    elif direction_name == "south":
                        dy = -1
                    elif direction_name == "east":
                        dx = 1
                    elif direction_name == "west":
                        dx = -1

                    nx, ny = x + dx, y + dy

                    # The target cell must also be a path cell
                    assert dungeon_map.space[nx, ny], (
                        f"Exit {direction_name} from ({x},{y}) leads to "
                        f"a wall at ({nx},{ny})"
                    )

                    # The target cell must have a return exit
                    opposite = {
                        "north": "south",
                        "south": "north",
                        "east": "west",
                        "west": "east",
                    }
                    target_exits = dungeon_map.get_exits(nx, ny)
                    assert opposite[direction_name] in target_exits, (
                        f"Exit {direction_name} from ({x},{y}) has no "
                        f"return path from ({nx},{ny})"
                    )
