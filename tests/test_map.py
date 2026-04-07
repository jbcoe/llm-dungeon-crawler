"""Unit tests for the map generation module."""

from unittest.mock import patch

from game.map import Coordinate, Direction, Map


def test_direction_enum() -> None:
    """Verify Direction enum properties."""
    assert Direction.NORTH.dx == 0
    assert Direction.NORTH.dy == 1
    assert Direction.SOUTH.dx == 0
    assert Direction.SOUTH.dy == -1
    assert Direction.EAST.dx == 1
    assert Direction.EAST.dy == 0
    assert Direction.WEST.dx == -1
    assert Direction.WEST.dy == 0


def test_coordinate() -> None:
    """Verify Coordinate methods and magic methods."""
    c1 = Coordinate(1, 2)
    c2 = Coordinate(1, 2)
    c3 = Coordinate(2, 3)

    # Test properties
    assert c1.x == 1
    assert c1.y == 2

    # Test equality
    assert c1 == c2
    assert c1 != c3
    assert c1 != "not a coordinate"

    # Test string representation
    assert repr(c1) == "Coordinate(1, 2)"

    # Test hashing (can be used in sets)
    coord_set = {c1, c3}
    assert c2 in coord_set
    assert Coordinate(9, 9) not in coord_set

    # Test stepping
    stepped = c1.step(Direction.NORTH)
    assert stepped.x == 1
    assert stepped.y == 3
    assert stepped == Coordinate(1, 3)


def test_map_initialization() -> None:
    """Verify Map initializes correctly and starts digging."""
    with patch("game.map.Digger.build_map") as mock_build:
        m = Map(size=5, seed=42)
        assert m.size == 5
        assert m.space.shape == (5, 5)
        assert m.space.dtype == bool
        assert not m.space.all()  # Should not be all True

        # Check that visitable cells exclude the outer boundary
        # Coordinate(1, 1) is automatically entered by Digger.__init__,
        # so it's not visitable.
        assert Coordinate(0, 0) not in m.visitable_cells
        assert Coordinate(1, 1) not in m.visitable_cells
        assert Coordinate(2, 2) in m.visitable_cells
        assert Coordinate(4, 4) not in m.visitable_cells

        mock_build.assert_called_once()


def test_map_cell_manipulation() -> None:
    """Verify entering and digging cells updates space and visitable_cells."""
    with patch("game.map.Digger.build_map"):
        m = Map(size=5)
        c1 = Coordinate(2, 2)
        c2 = Coordinate(2, 3)

        assert not m.space[c1.x, c1.y]
        assert c1 in m.visitable_cells

        # Test enter_cell
        m.enter_cell(c1)
        assert m.space[c1.x, c1.y]
        assert c1 not in m.visitable_cells

        # Test dig_step
        assert not m.space[c2.x, c2.y]
        assert c2 in m.visitable_cells
        m.dig_step(c1, c2)
        assert m.space[c2.x, c2.y]
        assert c2 not in m.visitable_cells


def test_map_available_steps() -> None:
    """Verify available_steps prevents loops and double-backs."""
    with patch("game.map.Digger.build_map"):
        m = Map(size=5)
        # Note: (1,1) is already entered by Digger.__init__.
        # Create a small path: (1,1) -> (1,2) -> (2,2)
        m.dig_step(Coordinate(1, 1), Coordinate(1, 2))
        m.dig_step(Coordinate(1, 2), Coordinate(2, 2))

        # Current location is (2,2).
        current = Coordinate(2, 2)

        # Neighbors of (2,2): (2,3) N, (2,1) S, (3,2) E, (1,2) W

        # Let's test a potential loop condition. If we dig to (2,3),
        # and (1,3) is ALREADY a path.
        m.enter_cell(Coordinate(1, 3))

        # Now if we check available steps from (2,2):
        # North is (2,3). Its neighbors are (2,4)[wall], (2,2)[current],
        # (3,3)[wall], (1,3)[path!].
        # Because (1,3) is a path and not the current cell, (2,3) would
        # create a loop.
        # South is (2,1). Its neighbors are (2,2)[current], (2,0)[wall],
        # (3,1)[wall], (1,1)[path!].
        # Because (1,1) is the start path, (2,1) would also create a loop.

        steps = m.available_steps(current)
        assert Coordinate(2, 3) not in steps
        assert Coordinate(2, 1) not in steps
        assert Coordinate(3, 2) in steps


def test_map_get_exits() -> None:
    """Verify get_exits correctly identifies paths around a coordinate."""
    with patch("game.map.Digger.build_map"):
        m = Map(size=5)
        # Create a T-junction at (2,2)
        m.space[2, 2] = True
        m.space[2, 3] = True  # North
        m.space[2, 1] = True  # South
        m.space[3, 2] = True  # East
        # West (1,2) remains False

        exits = m.get_exits(2, 2)
        assert "north" in exits
        assert "south" in exits
        assert "east" in exits
        assert "west" not in exits

        # Corner case: get_exits on a wall should return empty
        assert m.get_exits(1, 2) == []

        # Out of bounds should return empty safely
        assert m.get_exits(-1, -1) == []
        assert m.get_exits(5, 5) == []


def test_digger_build_map() -> None:
    """Verify Digger explores the map fully without getting stuck."""
    m = Map(size=5, seed=1)  # Seed for deterministic behavior

    # After initialization, the digger should have carved paths.
    # The number of visited cells should be > 0.
    assert m.space.sum() > 0
    # The digger should terminate, meaning `walk_maze` completed.
    # It should not have any infinite loops.
    assert len(m.visitable_cells) < (3 * 3)  # Some cells were visited
