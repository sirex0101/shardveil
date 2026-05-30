import sys
from pathlib import Path
import unittest

import arcade


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sv.core.collision import MoveResult
from sv.core.player_input import PlayerInputController


class FakeState:
    def __init__(self, player_turn=True):
        self.player_turn = player_turn

    def is_player_turn(self):
        return self.player_turn


class FakeTurnController:
    def __init__(self, result=MoveResult.MOVED):
        self.result = result
        self.moves = []
        self.wait_calls = 0

    def try_player_move(self, dx, dy):
        self.moves.append((dx, dy))
        return self.result, None

    def is_wall_block(self, result):
        return result == MoveResult.BLOCKED_WALL

    def wait_player_turn(self):
        self.wait_calls += 1


class FakePlayer:
    def __init__(self):
        self.light = 5
        self.light_max = 10

    def recover_light(self, amount):
        before = self.light
        self.light = min(self.light_max, self.light + amount)
        return self.light - before


class PlayerInputControllerTests(unittest.TestCase):
    def test_direction_press_is_handled_and_resolves_after_diagonal_window(self):
        turn_controller = FakeTurnController()
        controller = PlayerInputController(FakeState(), turn_controller)

        handled = controller.handle_direction_press(arcade.key.D, 1.0)
        controller.process_movement(1.03)

        self.assertTrue(handled)
        self.assertEqual(turn_controller.moves, [(1, 0)])

    def test_unknown_key_is_not_handled(self):
        controller = PlayerInputController(FakeState(), FakeTurnController())

        self.assertFalse(controller.handle_direction_press(arcade.key.SPACE, 1.0))

    def test_wait_turn_recovers_player_light_and_delegates_turn(self):
        player = FakePlayer()
        turn_controller = FakeTurnController()
        controller = PlayerInputController(FakeState(), turn_controller)

        controller.wait_turn(player)

        self.assertEqual(player.light, 7)
        self.assertEqual(turn_controller.wait_calls, 1)

    def test_wall_block_marks_move_until_input_changes(self):
        turn_controller = FakeTurnController(result=MoveResult.BLOCKED_WALL)
        controller = PlayerInputController(FakeState(), turn_controller)

        controller.handle_direction_press(arcade.key.D, 1.0)
        controller.process_movement(1.03)
        controller.process_movement(1.04)

        self.assertEqual(turn_controller.moves, [(1, 0)])


if __name__ == "__main__":
    unittest.main()
