"""World model: the grid, its obstacles and items, and the robot's state."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

Position = tuple[int, int]


class Direction(Enum):
    NORTH = (0, -1)
    EAST = (1, 0)
    SOUTH = (0, 1)
    WEST = (-1, 0)

    @property
    def dx(self) -> int:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]

    def turn_left(self) -> Direction:
        order = list(Direction)
        return order[(order.index(self) - 1) % 4]

    def turn_right(self) -> Direction:
        order = list(Direction)
        return order[(order.index(self) + 1) % 4]


@dataclass
class Robot:
    position: Position = (0, 0)
    heading: Direction = Direction.EAST
    holding: str | None = None

    def ahead(self) -> Position:
        x, y = self.position
        return (x + self.heading.dx, y + self.heading.dy)


@dataclass
class World:
    width: int
    height: int
    obstacles: set[Position] = field(default_factory=set)
    items: dict[Position, str] = field(default_factory=dict)

    def in_bounds(self, pos: Position) -> bool:
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def is_free(self, pos: Position) -> bool:
        return self.in_bounds(pos) and pos not in self.obstacles

    def neighbors(self, pos: Position) -> list[Position]:
        x, y = pos
        candidates = [(x + d.dx, y + d.dy) for d in Direction]
        return [p for p in candidates if self.is_free(p)]

    def render(self, robot: Robot) -> str:
        arrows = {
            Direction.NORTH: "^",
            Direction.EAST: ">",
            Direction.SOUTH: "v",
            Direction.WEST: "<",
        }
        rows = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                pos = (x, y)
                if pos == robot.position:
                    row.append(arrows[robot.heading])
                elif pos in self.obstacles:
                    row.append("#")
                elif pos in self.items:
                    row.append(self.items[pos][0].upper())
                else:
                    row.append(".")
            rows.append(" ".join(row))
        return "\n".join(rows)
