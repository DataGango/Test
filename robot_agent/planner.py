"""Turn goals into sequences of primitive steps."""

from __future__ import annotations

from collections import deque

from .steps import Drop, Move, Pick, Step, Turn
from .world import Direction, Position, Robot, World


class PlanningError(RuntimeError):
    """Raised when no plan can reach the goal."""


def _shortest_path(world: World, start: Position, goal: Position) -> list[Position]:
    if not world.is_free(goal):
        raise PlanningError(f"goal {goal} is not reachable")
    came_from: dict[Position, Position | None] = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for nxt in world.neighbors(current):
            if nxt not in came_from:
                came_from[nxt] = current
                queue.append(nxt)
    if goal not in came_from:
        raise PlanningError(f"no path from {start} to {goal}")
    path = []
    node: Position | None = goal
    while node is not None:
        path.append(node)
        node = came_from[node]
    return path[::-1]


def _turns(current: Direction, target: Direction) -> list[Step]:
    order = list(Direction)
    diff = (order.index(target) - order.index(current)) % 4
    if diff == 1:
        return [Turn("right")]
    if diff == 2:
        return [Turn("right"), Turn("right")]
    if diff == 3:
        return [Turn("left")]
    return []


def plan_path(
    world: World, start: Position, heading: Direction, goal: Position
) -> tuple[list[Step], Direction]:
    """Plan turns and moves from start to goal. Returns steps and final heading."""
    path = _shortest_path(world, start, goal)
    steps: list[Step] = []
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        needed = Direction((x1 - x0, y1 - y0))
        steps.extend(_turns(heading, needed))
        steps.append(Move())
        heading = needed
    return steps, heading


def plan_delivery(world: World, robot: Robot, item: str, destination: Position) -> list[Step]:
    """Plan: go to the item, pick it up, carry it to destination, drop it."""
    source = next((pos for pos, name in world.items.items() if name == item), None)
    if source is None:
        raise PlanningError(f"item {item!r} not found")
    to_item, heading = plan_path(world, robot.position, robot.heading, source)
    to_dest, _ = plan_path(world, source, heading, destination)
    return [*to_item, Pick(), *to_dest, Drop()]
