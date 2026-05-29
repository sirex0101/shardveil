from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, TypeVar

import arcade

from sv.core.config import Settings
from sv.core.player_resources import PlayerCarryover, apply_player_carryover
from sv.entities import Player, Skeleton
from sv.items import DEFAULT_ITEM_DEFINITIONS, MapItem
from sv.world.level_generator import LevelGenerator


TILE_SIZE = Settings.TILE_SIZE
SampleItem = TypeVar("SampleItem")


class RandomSampler(Protocol):
    def sample(self, population: list[SampleItem], k: int) -> list[SampleItem]: ...


@dataclass(slots=True)
class SceneBuildResult:
    level: list[list[int]]
    scene: arcade.Scene
    player: Player
    stairs_xy: tuple[int, int]
    world_width: int
    world_height: int


def load_tile_textures(
    *,
    tile_size: int = TILE_SIZE,
    tileset_image: str = ":assets:/sprites/tileset.png",
):
    tiles = arcade.load_spritesheet(tileset_image)
    textures = tiles.get_texture_grid((tile_size, tile_size), columns=3, count=3)
    return textures[0], textures[1], textures[2]


def build_level_scene(
    *,
    depth: int,
    player_carryover: PlayerCarryover | None = None,
    level_generator_factory: Callable[..., LevelGenerator] = LevelGenerator,
    tile_textures=None,
    rng: RandomSampler = random,
    tile_size: int = TILE_SIZE,
) -> SceneBuildResult:
    generator = level_generator_factory(width=64, height=48)
    level, spawn_xy, stairs_xy = generator.generate()
    world_width = len(level[0]) * tile_size
    world_height = len(level) * tile_size

    scene = arcade.Scene()
    scene.add_sprite_list("Ground")
    scene.add_sprite_list("Walls")
    scene.add_sprite_list("Items")
    scene.add_sprite_list("Player")
    scene.add_sprite_list("Skeleton")

    floor_texture, wall_texture, stairs_texture = tile_textures or load_tile_textures(tile_size=tile_size)
    _add_tiles(scene, level, floor_texture, wall_texture, stairs_texture, tile_size=tile_size)

    player = Player(tile_x=spawn_xy[0], tile_y=spawn_xy[1])
    apply_player_carryover(player, player_carryover)
    scene.add_sprite("Player", player)

    floor_tiles = [
        (x, y)
        for y in range(len(level))
        for x in range(len(level[0]))
        if level[y][x] in (1, 3)
        and (x, y) != spawn_xy
        and (x, y) != stairs_xy
    ]
    enemy_count = min(6, 1 + depth // 2)
    enemy_tiles = rng.sample(floor_tiles, k=min(enemy_count, len(floor_tiles)))
    for sx, sy in enemy_tiles:
        scene.add_sprite("Skeleton", Skeleton(tile_x=sx, tile_y=sy))

    occupied_tiles = set(enemy_tiles)
    item_tiles = [tile for tile in floor_tiles if tile not in occupied_tiles]
    item_count = min(4, 1 + depth // 2)
    item_definitions = tuple(DEFAULT_ITEM_DEFINITIONS.values())
    for index, (sx, sy) in enumerate(rng.sample(item_tiles, k=min(item_count, len(item_tiles)))):
        definition = item_definitions[index % len(item_definitions)]
        scene.add_sprite("Items", MapItem(definition, sx, sy))

    return SceneBuildResult(
        level=level,
        scene=scene,
        player=player,
        stairs_xy=stairs_xy,
        world_width=world_width,
        world_height=world_height,
    )


def _add_tiles(
    scene: arcade.Scene,
    level,
    floor_texture,
    wall_texture,
    stairs_texture,
    *,
    tile_size: int,
) -> None:
    for y in range(len(level)):
        for x in range(len(level[0])):
            tile = level[y][x]
            world_x = x * tile_size
            world_y = y * tile_size

            if tile == 0:
                continue
            if tile == 1:
                texture = floor_texture
                list_name = "Ground"
            elif tile == 3:
                texture = stairs_texture
                list_name = "Ground"
            elif tile == 2:
                texture = wall_texture
                list_name = "Walls"
            else:
                continue

            sprite = arcade.Sprite()
            sprite.texture = texture
            sprite.center_x = world_x + tile_size / 2
            sprite.center_y = world_y + tile_size / 2
            scene[list_name].append(sprite)
