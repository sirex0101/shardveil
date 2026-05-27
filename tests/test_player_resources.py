import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sv.core.player_resources import (
    PlayerCarryover,
    apply_player_carryover,
    consume_player_light,
    next_depth,
    player_light_ratio,
    recover_player_light,
)


class FakeCameraController:
    zoom = 3.0


class FakePlayer:
    def __init__(self):
        self.inventory = ["potion"]
        self.hp = 7
        self.max_hp = 10
        self.light = 4
        self.light_max = 10

    def spend_light(self, amount=1):
        spent = min(self.light, amount)
        self.light -= spent
        return spent

    def recover_light(self, amount=1):
        before = self.light
        self.light = min(self.light_max, self.light + amount)
        return self.light - before

    def light_ratio(self):
        return self.light / self.light_max


class PlayerResourcesTests(unittest.TestCase):
    def test_next_depth_resets_or_advances(self):
        self.assertEqual(next_depth(7, keep_player=False), 1)
        self.assertEqual(next_depth(7, keep_player=True), 8)

    def test_carryover_capture_uses_defaults_without_keep_player(self):
        player = FakePlayer()

        carryover = PlayerCarryover.capture(player, FakeCameraController(), keep_player=False)

        self.assertIsNone(carryover.inventory)
        self.assertIsNone(carryover.hp)
        self.assertIsNone(carryover.light)
        self.assertEqual(carryover.zoom, 2.0)

    def test_carryover_capture_preserves_player_state_and_zoom(self):
        player = FakePlayer()

        carryover = PlayerCarryover.capture(player, FakeCameraController(), keep_player=True)

        self.assertIs(carryover.inventory, player.inventory)
        self.assertEqual(carryover.hp, 7)
        self.assertEqual(carryover.light, 4)
        self.assertEqual(carryover.zoom, 3.0)

    def test_apply_player_carryover_clamps_hp_and_light(self):
        player = FakePlayer()
        player.hp = 1
        player.light = 1

        apply_player_carryover(
            player,
            PlayerCarryover(inventory=["torch"], hp=99, light=-4, zoom=2.0),
        )

        self.assertEqual(player.inventory, ["torch"])
        self.assertEqual(player.hp, 10)
        self.assertEqual(player.light, 0)

    def test_light_helpers_delegate_with_safe_defaults(self):
        player = FakePlayer()

        self.assertEqual(consume_player_light(player, 2), 2)
        self.assertEqual(player.light, 2)
        self.assertEqual(recover_player_light(player, 20), 8)
        self.assertEqual(player.light, 10)
        self.assertEqual(player_light_ratio(player), 1.0)
        self.assertEqual(consume_player_light(None, 2), 0)
        self.assertEqual(recover_player_light(None, 2), 0)
        self.assertEqual(player_light_ratio(None), 0.0)


if __name__ == "__main__":
    unittest.main()
