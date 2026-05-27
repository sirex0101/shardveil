from __future__ import annotations

from collections import deque
from collections.abc import Callable

from sv.ai import decide_enemy_action
from sv.core.collision import MoveResult
from sv.core.player_resources import (
    PLAYER_ACTION_LIGHT_COST,
    consume_player_light,
)
from sv.core.state_manager import GamePhase, StateManager


class TurnController:
    def __init__(
        self,
        state: StateManager,
        message_log,
        *,
        on_player_dead: Callable[[], None],
        on_depth_advance: Callable[[], None],
    ) -> None:
        self.state = state
        self.message_log = message_log
        self.on_player_dead = on_player_dead
        self.on_depth_advance = on_depth_advance
        self.level = None
        self.scene = None
        self.player = None
        self._enemy_queue: deque = deque()
        self._current_enemy = None

    def configure(self, level, scene, player) -> None:
        self.level = level
        self.scene = scene
        self.player = player
        self.clear()

    def clear(self) -> None:
        self._enemy_queue.clear()
        self._current_enemy = None

    @staticmethod
    def is_wall_block(result) -> bool:
        return result == MoveResult.BLOCKED_WALL

    def get_entity_at(self, tile_x: int, tile_y: int, list_name: str | None = None):
        if self.scene is None:
            return None
        if list_name:
            sprites = self.scene.get_sprite_list(list_name)
            if sprites:
                for sprite in sprites:
                    if getattr(sprite, "tile_x", None) == tile_x and getattr(sprite, "tile_y", None) == tile_y:
                        return sprite
            return None

        for name in ("Player", "Skeleton"):
            sprites = self.scene.get_sprite_list(name)
            if sprites:
                for sprite in sprites:
                    if getattr(sprite, "tile_x", None) == tile_x and getattr(sprite, "tile_y", None) == tile_y:
                        return sprite
        return None

    def is_player_dead(self) -> bool:
        return (
            self.player is None
            or getattr(self.player, "hp", 0) <= 0
            or getattr(self.player, "removed", False)
        )

    def player_on_stairs(self, stairs_xy: tuple[int, int] | None) -> bool:
        if self.player is None or stairs_xy is None:
            return False
        return (self.player.tile_x, self.player.tile_y) == stairs_xy

    def advance_after_player_animation(self, stairs_xy: tuple[int, int] | None) -> bool:
        if not self.state.is_player_anim():
            return False
        if getattr(self.player, "moving", False):
            return False
        if self.player_on_stairs(stairs_xy):
            self.on_depth_advance()
            return True
        self.state.set_phase(GamePhase.ENEMY_TURN)
        self.process_enemy_turns()
        return True

    def wait_player_turn(self) -> None:
        self.message_log.push("Вы пропустили ход", "info")
        self.state.set_phase(GamePhase.ENEMY_TURN)
        self.process_enemy_turns()

    def move_with_fallback(self, entity, dx, dy):
        res, blocker = entity.attempt_move(dx, dy, self.level, self.scene)
        if res == MoveResult.MOVED:
            return res, blocker
        if dx != 0 and dy != 0 and res == MoveResult.BLOCKED_WALL:
            res2, blocker2 = entity.attempt_move(dx, 0, self.level, self.scene)
            if res2 == MoveResult.MOVED:
                return res2, blocker2
            res3, blocker3 = entity.attempt_move(0, dy, self.level, self.scene)
            return res3, blocker3
        return res, blocker

    def try_player_move(self, dx, dy):
        player = self.player
        if player is None:
            return None, None

        res, blocker = self.move_with_fallback(player, dx, dy)
        if res is None:
            return None, None
        if res == MoveResult.BLOCKED_WALL:
            return res, blocker
        if res == MoveResult.BLOCKED_ENTITY:
            if blocker is not None and hasattr(player, "attack"):
                player.attack(blocker)
                if getattr(blocker, "hp", 1) <= 0 or getattr(blocker, "removed", False):
                    self.message_log.push("Враг повержен", "combat")
                else:
                    self.message_log.push("Вы атаковали врага", "combat")
                consume_player_light(player, PLAYER_ACTION_LIGHT_COST)
            self.state.set_phase(GamePhase.ENEMY_TURN)
            self.process_enemy_turns()
            return res, blocker
        if res == MoveResult.MOVED:
            consume_player_light(player, PLAYER_ACTION_LIGHT_COST)
            self.state.set_phase(GamePhase.PLAYER_ANIM)
            return res, blocker
        return res, blocker

    def process_enemy_turns(self):
        if self.state.is_paused() or self.scene is None:
            return
        enemies = list(self.scene.get_sprite_list("Skeleton") or [])
        self._enemy_queue = deque(e for e in enemies if not getattr(e, "removed", False))
        self._current_enemy = None
        self._process_next_enemy()

    def _process_next_enemy(self):
        if self.state.is_paused():
            return

        while self._enemy_queue:
            enemy = self._enemy_queue.popleft()
            if getattr(enemy, "removed", False):
                continue
            action = decide_enemy_action(enemy, self.player, self.level, self.scene)

            if action.kind == "wait":
                continue

            if action.kind == "attack":
                if hasattr(enemy, "attack"):
                    self.message_log.push("Враг атаковал вас", "combat")
                    enemy.attack(self.player)
                    if self.is_player_dead():
                        self.on_player_dead()
                        return
                continue

            if action.kind != "move":
                continue

            res, blocker = self.move_with_fallback(enemy, action.dx, action.dy)
            if res == MoveResult.BLOCKED_WALL:
                continue
            if res == MoveResult.BLOCKED_ENTITY:
                if blocker is self.player:
                    enemy.attack(self.player)
                    if self.is_player_dead():
                        self.on_player_dead()
                        return
                continue
            if res == MoveResult.MOVED:
                self._current_enemy = enemy

                def _make_callback(e):
                    def cb():
                        e.on_move_complete = None
                        self._current_enemy = None
                        self._process_next_enemy()

                    return cb

                enemy.on_move_complete = _make_callback(enemy)
                return
            continue

        self.state.set_phase(GamePhase.PLAYER_TURN)
