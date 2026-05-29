import sys
from pathlib import Path
import unittest

import arcade


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

arcade.resources.add_resource_handle("assets", ROOT / "assets")

from sv.world.scene_builder import build_level_scene


class FixedGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def generate(self):
        return (
            [
                [1, 2, 0],
                [1, 3, 1],
            ],
            (0, 0),
            (1, 1),
        )


class LargeFloorGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def generate(self):
        return ([[1 for _ in range(10)] for _ in range(2)], (0, 0), (9, 1))


class FirstItemsSampler:
    def sample(self, population, k):
        return list(population)[:k]


class SceneBuilderTests(unittest.TestCase):
    def _textures(self):
        test_id = self.id()
        return (
            arcade.Texture.create_empty(f"{test_id}-floor", (32, 32)),
            arcade.Texture.create_empty(f"{test_id}-wall", (32, 32)),
            arcade.Texture.create_empty(f"{test_id}-stairs", (32, 32)),
        )

    def test_build_level_scene_creates_expected_sprite_lists(self):
        result = build_level_scene(
            depth=1,
            level_generator_factory=FixedGenerator,
            tile_textures=self._textures(),
            rng=FirstItemsSampler(),
        )

        self.assertEqual(result.stairs_xy, (1, 1))
        self.assertEqual(result.world_width, 96)
        self.assertEqual(result.world_height, 64)
        self.assertEqual(len(result.scene["Ground"]), 4)
        self.assertEqual(len(result.scene["Walls"]), 1)
        self.assertEqual(len(result.scene["Items"]), 1)
        self.assertEqual(len(result.scene["Player"]), 1)
        self.assertEqual(len(result.scene["Skeleton"]), 1)
        self.assertIs(result.player, result.scene["Player"][0])
        self.assertEqual((result.player.tile_x, result.player.tile_y), (0, 0))

    def test_depth_controls_enemy_count_with_current_cap(self):
        result = build_level_scene(
            depth=10,
            level_generator_factory=LargeFloorGenerator,
            tile_textures=self._textures(),
            rng=FirstItemsSampler(),
        )

        self.assertEqual(len(result.scene["Skeleton"]), 6)
        self.assertEqual(len(result.scene["Items"]), 4)


if __name__ == "__main__":
    unittest.main()
