import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sv.entities.entity import Entity


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
    def test_take_damage_clamps_hp_and_marks_dead_entity_removed(self):
        entity = DummyEntity(hp=2)

        entity.take_damage(5)

        self.assertEqual(entity.hp, 0)
        self.assertFalse(entity.blocking)
        self.assertTrue(entity.removed)
        self.assertTrue(entity.removed_from_lists)


if __name__ == "__main__":
    unittest.main()
