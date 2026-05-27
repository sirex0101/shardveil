import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sv.entities import Enemy, Entity, Player, Skeleton
from sv.entities.base import Entity as BaseEntity
from sv.entities.enemy import Enemy as EnemyEntity
from sv.entities.enemy import Skeleton as SkeletonEntity
from sv.entities.entity import Entity as LegacyEntity
from sv.entities.player import Player as PlayerEntity


class DummyEntity(Entity):
    def __init__(self, hp: int = 3):
        self.hp = hp
        self.max_hp = hp
        self.blocking = True
        self.removed = False
        self.removed_from_lists = False

    def remove_from_sprite_lists(self):
        self.removed_from_lists = True


class EntityTests(unittest.TestCase):
    def test_entity_exports_remain_compatible(self):
        self.assertIs(Entity, BaseEntity)
        self.assertIs(Player, PlayerEntity)
        self.assertIs(Enemy, EnemyEntity)
        self.assertIs(Skeleton, SkeletonEntity)
        self.assertIs(LegacyEntity, BaseEntity)

    def test_take_damage_clamps_hp_and_marks_dead_entity_removed(self):
        entity = DummyEntity(hp=2)

        entity.take_damage(5)

        self.assertEqual(entity.hp, 0)
        self.assertFalse(entity.blocking)
        self.assertTrue(entity.removed)
        self.assertTrue(entity.removed_from_lists)

    def test_player_initializes_health_light_and_inventory(self):
        player = Player(tile_x=2, tile_y=3)

        self.assertEqual(player.hp, 10)
        self.assertEqual(player.max_hp, 10)
        self.assertEqual(player.light, 10)
        self.assertEqual(player.light_max, 10)
        self.assertEqual((player.tile_x, player.tile_y), (2, 3))
        self.assertIsNotNone(player.inventory)

    def test_player_light_methods_clamp_values(self):
        player = Player(tile_x=0, tile_y=0)

        self.assertEqual(player.spend_light(3), 3)
        self.assertEqual(player.light, 7)
        self.assertEqual(player.spend_light(99), 7)
        self.assertEqual(player.light, 0)
        self.assertEqual(player.recover_light(4), 4)
        self.assertEqual(player.light_ratio(), 0.4)
        self.assertEqual(player.recover_light(99), 6)
        self.assertEqual(player.light_ratio(), 1.0)

    def test_enemy_initializes_ai_state_defaults(self):
        enemy = Enemy(":assets:/sprites/skeleton.png", tile_x=1, tile_y=2)

        self.assertEqual(enemy.hp, 3)
        self.assertEqual(enemy.notice_radius, 8)
        self.assertEqual(enemy.search_turn_limit, 3)
        self.assertFalse(enemy.is_alerted)
        self.assertIsNone(enemy.last_seen_player_tile)
        self.assertEqual(enemy.search_turns_left, 0)

    def test_skeleton_uses_skeleton_stats(self):
        skeleton = Skeleton(tile_x=4, tile_y=5)

        self.assertEqual(skeleton.hp, 4)
        self.assertEqual(skeleton.max_hp, 4)
        self.assertEqual((skeleton.tile_x, skeleton.tile_y), (4, 5))


if __name__ == "__main__":
    unittest.main()
