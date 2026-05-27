from __future__ import annotations

import arcade

from sv.core.movement_input import MovementInputState
from sv.core.player_resources import PLAYER_WAIT_LIGHT_RECOVERY, recover_player_light


PLAYER_INPUT_DIAGONAL_WINDOW = 0.02
PLAYER_HORIZONTAL_KEYS = {
    arcade.key.A: -1,
    arcade.key.LEFT: -1,
    arcade.key.D: 1,
    arcade.key.RIGHT: 1,
}
PLAYER_VERTICAL_KEYS = {
    arcade.key.W: 1,
    arcade.key.UP: 1,
    arcade.key.S: -1,
    arcade.key.DOWN: -1,
}
PLAYER_DIRECTION_KEYS = tuple(PLAYER_HORIZONTAL_KEYS) + tuple(PLAYER_VERTICAL_KEYS)


class PlayerInputController:
    def __init__(self, state, turn_controller) -> None:
        self.state = state
        self.turn_controller = turn_controller
        self.movement_input = MovementInputState(
            PLAYER_HORIZONTAL_KEYS,
            PLAYER_VERTICAL_KEYS,
            diagonal_window=PLAYER_INPUT_DIAGONAL_WINDOW,
        )

    def clear(self) -> None:
        self.movement_input.clear()

    def handle_direction_press(self, symbol: int, now: float) -> bool:
        if symbol not in PLAYER_DIRECTION_KEYS:
            return False
        self.movement_input.press(symbol, now)
        self.process_movement(now)
        return True

    def release(self, symbol: int, now: float) -> None:
        self.movement_input.release(symbol, now)

    def wait_turn(self, player) -> None:
        recover_player_light(player, PLAYER_WAIT_LIGHT_RECOVERY)
        self.turn_controller.wait_player_turn()

    def process_movement(self, now: float) -> None:
        if not self.state.is_player_turn():
            return

        move = self.movement_input.resolve_move(now)
        if move is None:
            return

        dx, dy = move
        res, _ = self.turn_controller.try_player_move(dx, dy)
        if self.turn_controller.is_wall_block(res):
            self.movement_input.mark_blocked(dx, dy)
