"""Procedural map generation for the dungeon layout."""

import random
from enum import Enum

import numpy as np
import numpy.typing as npt


class Direction(Enum):
    """Cardinal directions and their (dx, dy) coordinate offsets."""

    NORTH = (0, 1)
    SOUTH = (0, -1)
    EAST = (1, 0)
    WEST = (-1, 0)

    @property
    def dx(self) -> int:
        """X-axis offset."""
        return self.value[0]

    @property
    def dy(self) -> int:
        """Y-axis offset."""
        return self.value[1]


class Coordinate:
    """Represents a coordinate in the map."""

    def __init__(self, x: int, y: int) -> None:
        """Initialize the coordinate."""
        self.x = x
        self.y = y

    def step(self, direction: Direction) -> "Coordinate":
        """Return a new coordinate moved by a direction."""
        return Coordinate(self.x + direction.dx, self.y + direction.dy)

    def __repr__(self) -> str:
        """Return a string representation of the coordinate."""
        return f"Coordinate({self.x}, {self.y})"

    def __eq__(self, obj: object) -> bool:
        """Check if two coordinates represent the same point."""
        if not isinstance(obj, Coordinate):
            return False
        return self.x == obj.x and self.y == obj.y

    def __hash__(self) -> int:
        """Return the hash value for the coordinate."""
        return hash((self.x, self.y))


class Digger:
    """Agent that digs through the map to create paths."""

    def __init__(
        self, dungeon_map: "Map", location: Coordinate, seed: int = 101
    ) -> None:
        """Initialize the digger agent."""
        random.seed(seed)
        self.dungeon_map = dungeon_map
        self.location = location
        self.dungeon_map.enter_cell(location)
        self.walk: list[Coordinate] = [location]

    def build_map(self) -> None:
        """Walk and dig the map using a randomized depth-first search."""
        while len(self.walk) > 0:
            possible_steps = self.dungeon_map.available_steps(self.location)
            if len(possible_steps) == 0:
                self.location = self.walk.pop()
                continue
            next_step = random.choice(possible_steps)
            self.dungeon_map.dig_step(self.location, next_step)
            self.location = next_step
            self.walk.append(self.location)


class Map:
    """Represents the generated map grid."""

    def __init__(self, size: int = 8, seed: int | None = None) -> None:
        """Initialize and generate the map of a given size."""
        self.size = size
        # True means path/visitable, False means wall
        self.space: npt.NDArray[np.bool_] = np.zeros((size, size), dtype=bool)

        self.visitable_cells: set[Coordinate] = {
            Coordinate(x, y)
            for x in range(1, self.size - 1)
            for y in range(1, self.size - 1)
        }

        if seed is None:
            seed = random.randint(0, 1000000)

        Digger(self, Coordinate(1, 1), seed).build_map()

    def enter_cell(self, location: Coordinate) -> None:
        """Mark a cell as entered/path."""
        self.space[location.x, location.y] = True
        self.visitable_cells.discard(location)

    def dig_step(self, location: Coordinate, new_location: Coordinate) -> None:
        """Dig from one cell to another."""
        self.space[new_location.x, new_location.y] = True
        self.visitable_cells.discard(new_location)

    def available_steps(self, location: Coordinate) -> list[Coordinate]:
        """Find valid neighboring cells to dig into without creating loops."""
        possible_cells = [location.step(d) for d in Direction]
        possible_cells = [c for c in possible_cells if c in self.visitable_cells]

        step_cells: list[Coordinate] = []
        for c in possible_cells:
            neighbours = [c.step(d) for d in Direction]
            valid = True
            for n in neighbours:
                # Don't double back or join up existing paths.
                if n != location and self.space[n.x, n.y]:
                    valid = False
                    break
            if valid:
                step_cells.append(c)

        return step_cells

    def get_exits(self, x: int, y: int) -> list[str]:
        """Get the available exits (paths) from a given coordinate."""
        if not (0 <= x < self.size and 0 <= y < self.size) or not self.space[x, y]:
            return []

        exits: list[str] = []
        for direction in Direction:
            nx, ny = x + direction.dx, y + direction.dy
            if 0 <= nx < self.size and 0 <= ny < self.size and self.space[nx, ny]:
                exits.append(direction.name.lower())
        return exits
