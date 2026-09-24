"""Demo: python -m robot_agent"""

from .agent import RobotAgent, StepResult
from .world import World


def main() -> None:
    world = World(
        width=7,
        height=5,
        obstacles={(2, 0), (2, 1), (2, 2), (4, 2), (4, 3), (4, 4)},
        items={(3, 4): "box"},
    )
    destination = (6, 0)

    def report(result: StepResult) -> None:
        status = "ok " if result.ok else "ERR"
        print(f"step {result.index:2d} [{status}] {result.step.describe():<14} -> {result.message}")

    agent = RobotAgent(world, on_step=report)
    print("Start:\n" + world.render(agent.robot) + "\n")
    success = agent.deliver("box", destination)
    print("\nEnd:\n" + world.render(agent.robot))
    print(f"\nDelivered: {success} in {len(agent.history)} steps")


if __name__ == "__main__":
    main()
