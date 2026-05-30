import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sv.core.state_manager import GamePhase, StateManager
from sv.core.turn_controller import TurnController
from sv.core.collision import MoveResult
from sv.items import DEFAULT_ITEM_DEFINITIONS


class FakeMessageLog:
    def __init__(self):
        self.messages = []

    def push(self, text, kind):
        self.messages.append((text, kind))


class FakeScene:
    def __init__(self, skeletons=None, player=None, items=None, chests=None):
        self._lists = {
            "Skeleton": skeletons or [],
            "Player": [player] if player is not None else [],
            "Items": items or [],
            "Chests": chests or [],
        }

    def get_sprite_list(self, name):
        return self._lists.get(name, [])

    def add_sprite(self, name, sprite):
        self._lists.setdefault(name, []).append(sprite)


class FakePlayer:
    def __init__(self, tile_x=0, tile_y=0, hp=3):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.hp = hp
        self.max_hp = hp
        self.light = 3
        self.removed = False
        self.moving = False
        self.inventory = None

    def spend_light(self, amount=1):
        spent = min(self.light, amount)
        self.light -= spent
        return spent


class FakeEnemy:
    def __init__(self, tile_x=1, tile_y=0, damage=1):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.hp = 1
        self.removed = False
        self.damage = damage

    def attack(self, target):
        target.hp = max(0, target.hp - self.damage)


class FakeMovingPlayer(FakePlayer):
    def __init__(self, blocker, **kwargs):
        super().__init__(**kwargs)
        self.blocker = blocker

    def attempt_move(self, dx, dy, level, scene):
        return MoveResult.BLOCKED_ENTITY, self.blocker


class FakeAddResult:
    def __init__(self, added=True, reason=None):
        self.added = added
        self.reason = reason


class FakeInventory:
    def __init__(self, *, added=True):
        self.added = added
        self.added_stacks = []

    def add_stack(self, stack):
        self.added_stacks.append(stack)
        return FakeAddResult(self.added, "Инвентарь заполнен.")


class FakeStack:
    definition = DEFAULT_ITEM_DEFINITIONS["potion"]
    name = definition.name
    quantity = 1


class FakeItem:
    def __init__(self, tile_x=0, tile_y=0):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.stack = FakeStack()
        self.removed = False
        self.blocking = False

    def remove_from_sprite_lists(self):
        self.removed = True


class FakeChest(FakeItem):
    def __init__(self, tile_x=0, tile_y=0):
        super().__init__(tile_x, tile_y)
        self.blocking = True


class TurnControllerTests(unittest.TestCase):
    def _controller(self, state, message_log=None):
        dead_calls = []
        depth_calls = []
        controller = TurnController(
            state,
            message_log or FakeMessageLog(),
            on_player_dead=lambda: dead_calls.append(True),
            on_depth_advance=lambda: depth_calls.append(True),
        )
        return controller, dead_calls, depth_calls

    def test_empty_enemy_queue_returns_player_turn(self):
        state = StateManager()
        state.enter_game(GamePhase.ENEMY_TURN)
        player = FakePlayer()
        controller, _, _ = self._controller(state)
        controller.configure([[1]], FakeScene(player=player), player)

        controller.process_enemy_turns()

        self.assertTrue(state.is_player_turn())

    def test_pause_blocks_enemy_turn_processing(self):
        state = StateManager()
        state.enter_game(GamePhase.ENEMY_TURN)
        state.pause()
        player = FakePlayer()
        enemy = FakeEnemy(damage=3)
        controller, dead_calls, _ = self._controller(state)
        controller.configure([[1, 1]], FakeScene([enemy], player), player)

        controller.process_enemy_turns()

        self.assertTrue(state.is_paused())
        self.assertEqual(player.hp, 3)
        self.assertEqual(dead_calls, [])

    def test_enemy_attack_can_trigger_player_death_callback(self):
        state = StateManager()
        state.enter_game(GamePhase.ENEMY_TURN)
        player = FakePlayer(hp=1)
        enemy = FakeEnemy(damage=1)
        log = FakeMessageLog()
        controller, dead_calls, _ = self._controller(state, log)
        controller.configure([[1, 1]], FakeScene([enemy], player), player)

        controller.process_enemy_turns()

        self.assertEqual(player.hp, 0)
        self.assertEqual(dead_calls, [True])
        self.assertEqual(log.messages, [("Враг атаковал вас", "combat")])

    def test_player_animation_completion_advances_to_enemy_turns(self):
        state = StateManager()
        state.enter_game(GamePhase.PLAYER_ANIM)
        player = FakePlayer()
        controller, _, _ = self._controller(state)
        controller.configure([[1]], FakeScene(player=player), player)

        handled = controller.advance_after_player_animation(stairs_xy=None)

        self.assertTrue(handled)
        self.assertTrue(state.is_player_turn())

    def test_auto_pickup_after_move_adds_stack_without_extra_turn(self):
        state = StateManager()
        state.enter_game(GamePhase.PLAYER_ANIM)
        player = FakePlayer(tile_x=2, tile_y=3)
        player.inventory = FakeInventory()
        item = FakeItem(tile_x=2, tile_y=3)
        log = FakeMessageLog()
        controller, _, _ = self._controller(state, log)
        controller.configure([[1]], FakeScene(player=player, items=[item]), player)

        handled = controller.advance_after_player_animation(stairs_xy=None)

        self.assertTrue(handled)
        self.assertTrue(item.removed)
        self.assertEqual(player.inventory.added_stacks, [item.stack])
        self.assertTrue(state.is_player_turn())
        self.assertEqual(log.messages, [("Вы подобрали Зелье", "loot")])

    def test_manual_pickup_adds_stack_and_spends_turn(self):
        state = StateManager()
        state.enter_game(GamePhase.PLAYER_TURN)
        player = FakePlayer(tile_x=2, tile_y=3)
        player.inventory = FakeInventory()
        item = FakeItem(tile_x=2, tile_y=3)
        log = FakeMessageLog()
        controller, _, _ = self._controller(state, log)
        controller.configure([[1]], FakeScene(player=player, items=[item]), player)

        picked_up = controller.pick_up_at_player()

        self.assertTrue(picked_up)
        self.assertTrue(item.removed)
        self.assertEqual(player.inventory.added_stacks, [item.stack])
        self.assertTrue(state.is_player_turn())
        self.assertEqual(log.messages, [("Вы подобрали Зелье", "loot")])

    def test_manual_pickup_failure_does_not_spend_turn(self):
        state = StateManager()
        state.enter_game(GamePhase.PLAYER_TURN)
        player = FakePlayer(tile_x=2, tile_y=3)
        player.inventory = FakeInventory(added=False)
        item = FakeItem(tile_x=2, tile_y=3)
        log = FakeMessageLog()
        controller, _, _ = self._controller(state, log)
        controller.configure([[1]], FakeScene(player=player, items=[item]), player)

        picked_up = controller.pick_up_at_player()

        self.assertFalse(picked_up)
        self.assertFalse(item.removed)
        self.assertTrue(state.is_player_turn())
        self.assertEqual(log.messages, [("Инвентарь заполнен.", "info")])

    def test_manual_pickup_does_not_open_adjacent_chest(self):
        state = StateManager()
        state.enter_game(GamePhase.PLAYER_TURN)
        player = FakePlayer(tile_x=2, tile_y=3)
        player.inventory = FakeInventory()
        chest = FakeChest(tile_x=3, tile_y=3)
        log = FakeMessageLog()
        controller, _, _ = self._controller(state, log)
        controller.configure([[1]], FakeScene(player=player, chests=[chest]), player)

        opened = controller.pick_up_at_player()

        self.assertFalse(opened)
        self.assertFalse(chest.removed)
        self.assertEqual(player.inventory.added_stacks, [])
        self.assertTrue(state.is_player_turn())
        self.assertEqual(log.messages, [("Здесь ничего нет", "info")])

    def test_bumping_chest_opens_and_drops_loot(self):
        state = StateManager()
        state.enter_game(GamePhase.PLAYER_TURN)
        chest = FakeChest(tile_x=3, tile_y=3)
        player = FakeMovingPlayer(chest, tile_x=2, tile_y=3)
        player.inventory = FakeInventory()
        log = FakeMessageLog()
        controller, _, _ = self._controller(state, log)
        controller.configure([[1]], FakeScene(player=player, chests=[chest]), player)

        result, blocker = controller.try_player_move(1, 0)

        self.assertEqual(result, MoveResult.BLOCKED_ENTITY)
        self.assertIs(blocker, chest)
        self.assertTrue(chest.removed)
        self.assertEqual(player.inventory.added_stacks, [])
        self.assertEqual(len(controller.scene.get_sprite_list("Items")), 1)
        dropped_item = controller.scene.get_sprite_list("Items")[0]
        self.assertEqual((dropped_item.tile_x, dropped_item.tile_y), (3, 3))
        self.assertIs(dropped_item.stack.definition, chest.stack.definition)
        self.assertEqual(player.light, 2)
        self.assertTrue(state.is_player_turn())
        self.assertEqual(log.messages, [])

    def test_chest_opening_does_not_require_inventory_space(self):
        state = StateManager()
        state.enter_game(GamePhase.PLAYER_TURN)
        chest = FakeChest(tile_x=2, tile_y=3)
        player = FakeMovingPlayer(chest, tile_x=1, tile_y=3)
        player.inventory = FakeInventory(added=False)
        log = FakeMessageLog()
        controller, _, _ = self._controller(state, log)
        controller.configure([[1]], FakeScene(player=player, chests=[chest]), player)

        result, blocker = controller.try_player_move(1, 0)

        self.assertEqual(result, MoveResult.BLOCKED_ENTITY)
        self.assertIs(blocker, chest)
        self.assertTrue(chest.removed)
        self.assertEqual(player.inventory.added_stacks, [])
        self.assertEqual(len(controller.scene.get_sprite_list("Items")), 1)
        self.assertEqual(player.light, 2)
        self.assertTrue(state.is_player_turn())
        self.assertEqual(log.messages, [])

    def test_player_on_stairs_triggers_depth_advance(self):
        state = StateManager()
        state.enter_game(GamePhase.PLAYER_ANIM)
        player = FakePlayer(tile_x=2, tile_y=3)
        controller, _, depth_calls = self._controller(state)
        controller.configure([[1]], FakeScene(player=player), player)

        handled = controller.advance_after_player_animation(stairs_xy=(2, 3))

        self.assertTrue(handled)
        self.assertEqual(depth_calls, [True])


if __name__ == "__main__":
    unittest.main()
