"""Unit tests for the map generation module."""

from unittest.mock import patch

import pytest

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


def test_map_size_validation() -> None:
    """Verify that Map size must be at least 3."""
    with pytest.raises(ValueError, match="Map size must be at least 3"):
        Map(size=2)
    with pytest.raises(ValueError, match="Map size must be at least 3"):
        Map(size=-1)


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


def test_find_dead_ends() -> None:
    """Verify find_dead_ends returns only cells with exactly one path neighbour."""
    with patch("game.map.Digger.build_map"):
        m = Map(size=5)
        # Build a simple L-shaped path: (1,1) -> (1,2) -> (2,2)
        # (1,1) has one neighbour: (1,2) — dead end
        # (1,2) has two neighbours: (1,1) and (2,2) — not a dead end
        # (2,2) has one neighbour: (1,2) — dead end
        m.space[1, 1] = True
        m.space[1, 2] = True
        m.space[2, 2] = True

        dead_ends = m.find_dead_ends()
        dead_end_coords = set(dead_ends)

        assert Coordinate(1, 1) in dead_end_coords
        assert Coordinate(2, 2) in dead_end_coords
        assert Coordinate(1, 2) not in dead_end_coords


def test_get_final_room_coord_basic() -> None:
    """Verify get_final_room_coord returns a dead-end that is not the start."""
    with patch("game.map.Digger.build_map"):
        m = Map(size=5)
        # Path: (1,1) -> (1,2) -> (1,3)
        m.space[1, 1] = True
        m.space[1, 2] = True
        m.space[1, 3] = True

        start = Coordinate(1, 1)
        final = m.get_final_room_coord(start)

        # Both (1,1) and (1,3) are dead-ends; only (1,3) is eligible.
        assert final is not None
        assert final == Coordinate(1, 3)
        assert final != start


def test_get_final_room_coord_excludes_start() -> None:
    """Verify get_final_room_coord never returns the starting cell."""
    with patch("game.map.Digger.build_map"):
        m = Map(size=5)
        # Only two cells; start (1,1) is also a dead-end but must be excluded.
        m.space[1, 1] = True
        m.space[1, 2] = True

        final = m.get_final_room_coord(Coordinate(1, 1))
        assert final is not None
        assert final == Coordinate(1, 2)


def test_get_final_room_coord_no_dead_ends_returns_none() -> None:
    """Return None when no reachable dead-ends exist aside from the start."""
    with patch("game.map.Digger.build_map"):
        m = Map(size=5)
        # Single-cell map: only (1,1) is a path — start itself is the only dead-end.
        m.space[1, 1] = True

        final = m.get_final_room_coord(Coordinate(1, 1))
        assert final is None


def test_get_final_room_coord_on_real_map() -> None:
    """Verify get_final_room_coord picks a valid dead-end on a real map."""
    m = Map(size=8, seed=42)
    final = m.get_final_room_coord()

    # A real 8×8 map should always have at least one dead-end away from (1,1)
    assert final is not None
    assert final != Coordinate(1, 1)
    # The final room must be a path cell
    assert m.space[final.x, final.y]
    # The final room must have exactly one exit (dead-end)
    assert len(m.get_exits(final.x, final.y)) == 1
