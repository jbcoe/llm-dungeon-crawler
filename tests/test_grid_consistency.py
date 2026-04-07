"""Tests for grid consistency in the pre-generated map layout."""

from unittest.mock import MagicMock, patch

from game.engine import GameEngine


def test_bidirectional_exits() -> None:
    """Verify that moving into a new room follows the pre-generated map correctly."""
    # Mocking random seed ensures predictable map generation
    engine = GameEngine(model="test-model", map_size=8)
    engine.ai._query_model = MagicMock(return_value="A test room description.")

    # Start at (1, 1).
    with patch("random.random", return_value=0.9):
        engine.enter_new_room("start")

    assert (1, 1) in engine.grid
    start_room = engine.grid[(1, 1)]

    # The map guarantees at least one exit from the start unless it's trapped
    # (which the generator avoids by digging).
    assert len(start_room.exits) > 0
    first_exit = start_room.exits[0]

    # Move in the direction of the first exit
    with patch("random.random", return_value=0.9):
        engine.handle_go(["go", first_exit])

    # Check new coordinates
    new_x, new_y = 1, 1
    if first_exit == "north":
        new_y += 1
    elif first_exit == "south":
        new_y -= 1
    elif first_exit == "east":
        new_x += 1
    elif first_exit == "west":
        new_x -= 1

    assert (new_x, new_y) in engine.grid
    new_room = engine.grid[(new_x, new_y)]

    # The new room MUST have an exit pointing back
    opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}
    assert opposite[first_exit] in new_room.exits


def test_complex_grid_consistency() -> None:
    """Verify that Map generates internally consistent, bidirectional grids."""
    engine = GameEngine(model="test-model", map_size=8)

    dungeon_map = engine.map_grid

    # Iterate through every cell in the map
    for x in range(dungeon_map.size):
        for y in range(dungeon_map.size):
            if dungeon_map.space[x, y]:
                exits = dungeon_map.get_exits(x, y)
                # If it has a north exit, the cell to the north must have a south exit
                if "north" in exits:
                    assert "south" in dungeon_map.get_exits(x, y + 1)
                if "south" in exits:
                    assert "north" in dungeon_map.get_exits(x, y - 1)
                if "east" in exits:
                    assert "west" in dungeon_map.get_exits(x + 1, y)
                if "west" in exits:
                    assert "east" in dungeon_map.get_exits(x - 1, y)
