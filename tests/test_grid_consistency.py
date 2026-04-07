"""Tests for grid consistency in room generation."""

from unittest.mock import MagicMock, patch

from game.engine import GameEngine
from game.models import Room


def test_bidirectional_exits() -> None:
    """Verify that moving into a new room creates a back-exit."""
    engine = GameEngine(model="test-model")
    engine.ai._query_model = MagicMock(return_value="A test room description.")

    # Start at (0,0). Force no enemies/items to simplify movement.
    with patch("random.random", return_value=0.9):
        engine.enter_new_room("start")
    start_room = engine.grid[(0, 0)]

    # Ensure start_room has a north exit so we can move there
    if "north" not in start_room.exits:
        start_room.exits.append("north")

    # Move North to (0,1)
    with patch("random.random", return_value=0.9):
        engine.handle_go(["go", "north"])

    assert (0, 1) in engine.grid
    north_room = engine.grid[(0, 1)]

    # The room at (0,1) MUST have a south exit because we came from (0,0) north
    assert "south" in north_room.exits


def test_complex_grid_consistency() -> None:
    """Verify that a new room connects to all existing neighbors correctly."""
    engine = GameEngine(model="test-model")
    engine.ai._query_model = MagicMock(return_value="A test room description.")

    # Manually populate grid to create a 'U' shape around (0,1)
    # (0,0) -> North exit
    engine.grid[(0, 0)] = Room(name="South Room", description="S", exits=["north"])
    # (1,1) -> West exit
    engine.grid[(1, 1)] = Room(name="East Room", description="E", exits=["west"])
    # (0,2) -> South exit
    engine.grid[(0, 2)] = Room(name="North Room", description="N", exits=["south"])

    # Now move to (0,1) from (0,0)
    engine.x, engine.y = 0, 0
    engine.current_room = engine.grid[(0, 0)]

    # generate_mechanics checks neighbors in order: north, south, east, west.
    # (0,2) is north, (0,0) is south, (1,1) is east, (-1,1) is west.
    # For (0,2), (0,0), (1,1), the neighbor exists, so random.random()
    # is NOT called.
    # For (-1,1), the neighbor does NOT exist, so random.random()
    # IS called for the exit.

    # Note: random.random() is also called for enemies, items, etc. in
    # generate_mechanics. We want to ensure no enemies spawn so we
    # can move, and no random 'west' exit.

    with patch("random.random", return_value=0.9):
        engine.handle_go(["go", "north"])

    room_0_1 = engine.grid[(0, 1)]

    # (0,1) should have:
    # - south exit (to (0,0)) because (0,0) has north
    # - east exit (to (1,1)) because (1,1) has west
    # - north exit (to (0,2)) because (0,2) has south
    assert "south" in room_0_1.exits
    assert "east" in room_0_1.exits
    assert "north" in room_0_1.exits
    assert "west" not in room_0_1.exits
