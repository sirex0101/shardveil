from __future__ import annotations

from sv.entities.base import Entity


class Enemy(Entity):
    def __init__(self, texture, tile_x: int, tile_y: int, hp: int = 3) -> None:
        super().__init__(texture, tile_x, tile_y, hp)
        self.notice_radius = 8
        self.search_turn_limit = 3
        self.is_alerted = False
        self.last_seen_player_tile: tuple[int, int] | None = None
        self.search_turns_left = 0


class Skeleton(Enemy):
    def __init__(self, tile_x: int, tile_y: int) -> None:
        texture = ":assets:/sprites/skeleton.png"
        super().__init__(texture, tile_x, tile_y, hp=4)
