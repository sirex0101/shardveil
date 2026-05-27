from __future__ import annotations

import arcade

from sv.core.config import Settings


TILE_SIZE = Settings.TILE_SIZE


class Entity(arcade.Sprite):
    """Base entity for objects that exist on the tile grid."""

    def __init__(
        self,
        texture,
        tile_x: int,
        tile_y: int,
        hp: int = 1,
        blocking: bool = True,
    ) -> None:
        super().__init__(str(texture))

        self.hp = hp
        self.max_hp = hp
        self.tile_x = int(tile_x)
        self.tile_y = int(tile_y)

        self.center_x = self.tile_x * TILE_SIZE + TILE_SIZE // 2
        self.center_y = self.tile_y * TILE_SIZE + TILE_SIZE // 2

        self.blocking = bool(blocking)
        self.removed = False

        self.moving = False
        self._move_from = (self.center_x, self.center_y)
        self._move_to = (self.center_x, self.center_y)
        self._move_elapsed = 0.0
        self._move_duration = 0.18
        self.on_move_complete = None

    def move_to(self, tile_x: int, tile_y: int) -> None:
        self.tile_x = int(tile_x)
        self.tile_y = int(tile_y)
        self.center_x = self.tile_x * TILE_SIZE + TILE_SIZE // 2
        self.center_y = self.tile_y * TILE_SIZE + TILE_SIZE // 2

    def start_move(
        self,
        target_tile_x: int,
        target_tile_y: int,
        duration: float | None = None,
    ) -> None:
        if duration is not None:
            self._move_duration = float(duration)
        self.moving = True
        self._move_elapsed = 0.0
        self._move_from = (self.center_x, self.center_y)
        self._move_to = (
            target_tile_x * TILE_SIZE + TILE_SIZE // 2,
            target_tile_y * TILE_SIZE + TILE_SIZE // 2,
        )

    def attempt_move(self, dx: int, dy: int, level, scene):
        try:
            from sv.core.collision import MoveResult, can_move, commit_tile
        except Exception:
            return None, None

        res, blocker, target_tx, target_ty = can_move(self, dx, dy, level, scene)
        if res != MoveResult.MOVED:
            return res, blocker
        if target_tx is None or target_ty is None:
            return MoveResult.BLOCKED_WALL, None

        committed = commit_tile(self, target_tx, target_ty)
        if not committed:
            return MoveResult.BLOCKED_WALL, None

        self.start_move(target_tx, target_ty)
        return MoveResult.MOVED, None

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)
        if self.hp <= 0:
            self.die()

    def die(self) -> None:
        self.blocking = False
        self.removed = True
        self.remove_from_sprite_lists()

    def update(self, *args, **kwargs) -> None:
        if self.moving:
            delta_time = 1 / 60
            if len(args) > 0 and isinstance(args[0], (int, float)):
                delta_time = float(args[0])

            self._move_elapsed += delta_time
            t = min(1.0, self._move_elapsed / max(1e-6, self._move_duration))
            eased = 1 - (1 - t) * (1 - t)
            sx, sy = self._move_from
            ex, ey = self._move_to
            self.center_x = sx + (ex - sx) * eased
            self.center_y = sy + (ey - sy) * eased

            if t >= 1.0:
                self.center_x = ex
                self.center_y = ey
                self.moving = False
                try:
                    if callable(self.on_move_complete):
                        self.on_move_complete()
                except Exception:
                    pass

        super().update(*args, **kwargs)

    def attack(self, target: "Entity", damage: int = 1) -> None:
        if target is None:
            return
        if target is self:
            return
        if not isinstance(target, Entity):
            return
        target.take_damage(damage)
