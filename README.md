# Test

## Robotic agent

`robot_agent` is a small grid-world robot that executes a plan **step by step**.

- **World** (`robot_agent/world.py`): a grid with obstacles and items, plus the robot's position, heading and held item.
- **Steps** (`robot_agent/steps.py`): primitive actions (`Move`, `Turn("left"|"right")`, `Pick`, `Drop`). Each checks its preconditions before changing state.
- **Planner** (`robot_agent/planner.py`): BFS path planning, turned into steps; `plan_delivery` builds a fetch-and-deliver plan.
- **Agent** (`robot_agent/agent.py`): `RobotAgent` runs steps one at a time, records a `StepResult` for each, and stops at the first failure.

```python
from robot_agent import RobotAgent, World, Move, Turn, Pick

# Run explicit steps
agent = RobotAgent(World(5, 5, items={(1, 0): "box"}))
agent.run([Move(), Pick(), Turn("right"), Move()])

# Or let the planner build the steps
agent = RobotAgent(World(5, 5, items={(1, 0): "box"}))
agent.deliver("box", (4, 4))
```

Run the demo: `python -m robot_agent`
Run the tests: `python -m unittest`
