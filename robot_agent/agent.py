"""The robotic agent: runs a plan one step at a time and records each result."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .planner import plan_delivery
from .steps import Step, StepError
from .world import Position, Robot, World


@dataclass(frozen=True)
class StepResult:
    index: int
    step: Step
    ok: bool
    message: str
    position: Position


class RobotAgent:
    def __init__(
        self,
        world: World,
        robot: Robot | None = None,
        on_step: Callable[[StepResult], None] | None = None,
    ) -> None:
        self.world = world
        self.robot = robot or Robot()
        self.on_step = on_step
        self.history: list[StepResult] = []

    def step(self, step: Step) -> StepResult:
        """Execute a single step and record the outcome."""
        try:
            message = step.execute(self.robot, self.world)
            ok = True
        except StepError as exc:
            message = str(exc)
            ok = False
        result = StepResult(len(self.history) + 1, step, ok, message, self.robot.position)
        self.history.append(result)
        if self.on_step:
            self.on_step(result)
        return result

    def run(self, steps: Iterable[Step]) -> bool:
        """Execute steps in order, stopping at the first failure."""
        return all(self.step(s).ok for s in steps)

    def deliver(self, item: str, destination: Position) -> bool:
        """Plan and execute fetching an item and bringing it to destination."""
        return self.run(plan_delivery(self.world, self.robot, item, destination))
