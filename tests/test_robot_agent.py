import unittest

from robot_agent import Direction, Drop, Move, Pick, Robot, RobotAgent, Turn, World, plan_path
from robot_agent.planner import PlanningError


class StepTests(unittest.TestCase):
    def test_move_and_turn(self):
        agent = RobotAgent(World(3, 3))
        self.assertTrue(agent.run([Move(), Turn("right"), Move()]))
        self.assertEqual(agent.robot.position, (1, 1))
        self.assertEqual(agent.robot.heading, Direction.SOUTH)

    def test_move_into_obstacle_fails_and_stops(self):
        agent = RobotAgent(World(3, 3, obstacles={(1, 0)}))
        self.assertFalse(agent.run([Move(), Turn("left")]))
        self.assertEqual(len(agent.history), 1)
        self.assertEqual(agent.robot.position, (0, 0))

    def test_move_off_grid_fails(self):
        agent = RobotAgent(World(3, 3), Robot(heading=Direction.WEST))
        self.assertFalse(agent.step(Move()).ok)

    def test_pick_and_drop(self):
        world = World(3, 3, items={(0, 0): "box"})
        agent = RobotAgent(world)
        self.assertTrue(agent.run([Pick(), Move(), Drop()]))
        self.assertEqual(world.items, {(1, 0): "box"})
        self.assertIsNone(agent.robot.holding)

    def test_pick_empty_cell_fails(self):
        self.assertFalse(RobotAgent(World(3, 3)).step(Pick()).ok)

    def test_drop_without_item_fails(self):
        self.assertFalse(RobotAgent(World(3, 3)).step(Drop()).ok)

    def test_invalid_turn(self):
        with self.assertRaises(ValueError):
            Turn("up")


class PlannerTests(unittest.TestCase):
    def test_plan_path_routes_around_obstacles(self):
        world = World(3, 3, obstacles={(1, 0), (1, 1)})
        steps, _ = plan_path(world, (0, 0), Direction.EAST, (2, 0))
        agent = RobotAgent(world)
        self.assertTrue(agent.run(steps))
        self.assertEqual(agent.robot.position, (2, 0))

    def test_unreachable_goal(self):
        world = World(3, 3, obstacles={(1, 0), (1, 1), (1, 2)})
        with self.assertRaises(PlanningError):
            plan_path(world, (0, 0), Direction.EAST, (2, 0))

    def test_deliver(self):
        world = World(5, 5, obstacles={(2, 1), (2, 2), (2, 3)}, items={(4, 4): "box"})
        agent = RobotAgent(world)
        self.assertTrue(agent.deliver("box", (4, 0)))
        self.assertEqual(world.items, {(4, 0): "box"})
        self.assertTrue(all(r.ok for r in agent.history))

    def test_deliver_missing_item(self):
        with self.assertRaises(PlanningError):
            RobotAgent(World(3, 3)).deliver("box", (1, 1))


if __name__ == "__main__":
    unittest.main()
