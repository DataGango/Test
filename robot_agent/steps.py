"""Primitive steps the robot can execute.

Each step checks its preconditions against the current world and robot
state, then applies its effect. A failed precondition raises StepError and
leaves the state untouched.
"""

from __future__ import annotations

from dataclasses import dataclass

from .world import Robot, World


class StepError(RuntimeError):
    """Raised when a step cannot be executed in the current state."""


class Step:
    def execute(self, robot: Robot, world: World) -> str:
        raise NotImplementedError

    def describe(self) -> str:
        return type(self).__name__.lower()


@dataclass(frozen=True)
class Move(Step):
    """Move one cell forward in the current heading."""

    def execute(self, robot: Robot, world: World) -> str:
        target = robot.ahead()
        if not world.is_free(target):
            raise StepError(f"cannot move to {target}: blocked")
        robot.position = target
        return f"moved to {target}"

    def describe(self) -> str:
        return "move forward"


@dataclass(frozen=True)
class Turn(Step):
    """Rotate 90 degrees in place."""

    direction: str  # "left" or "right"

    def __post_init__(self) -> None:
        if self.direction not in ("left", "right"):
            raise ValueError("direction must be 'left' or 'right'")

    def execute(self, robot: Robot, world: World) -> str:
        if self.direction == "left":
            robot.heading = robot.heading.turn_left()
        else:
            robot.heading = robot.heading.turn_right()
        return f"now facing {robot.heading.name.lower()}"

    def describe(self) -> str:
        return f"turn {self.direction}"


@dataclass(frozen=True)
class Pick(Step):
    """Pick up the item on the robot's current cell."""

    def execute(self, robot: Robot, world: World) -> str:
        if robot.holding is not None:
            raise StepError(f"already holding {robot.holding}")
        item = world.items.pop(robot.position, None)
        if item is None:
            raise StepError(f"no item at {robot.position}")
        robot.holding = item
        return f"picked up {item}"

    def describe(self) -> str:
        return "pick up item"


@dataclass(frozen=True)
class Drop(Step):
    """Drop the held item on the robot's current cell."""

    def execute(self, robot: Robot, world: World) -> str:
        if robot.holding is None:
            raise StepError("not holding anything")
        if robot.position in world.items:
            raise StepError(f"cell {robot.position} is occupied")
        world.items[robot.position] = robot.holding
        item, robot.holding = robot.holding, None
        return f"dropped {item} at {robot.position}"

    def describe(self) -> str:
        return "drop item"
