from __future__ import annotations

import time

import arcade
from arcade import gui
from arcade.future.light import Light, LightLayer

from sv.core import (
    CameraController,
    MovementInputState,
    Settings,
    StateManager,
    snap_world_point,
)
from sv.core.player_resources import (
    DEPTH_LIGHT_RECOVERY,
    PLAYER_WAIT_LIGHT_RECOVERY,
    PlayerCarryover,
    next_depth,
    player_light_ratio,
    recover_player_light,
)
from sv.core.turn_controller import TurnController
from sv.ui import GameUI, HUDLayer, OverlayScreenId, ViewScreenId
from sv.world.scene_builder import build_level_scene


TILE_SIZE = Settings.TILE_SIZE
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


class Game(arcade.Window):
    def __init__(self):
        self.settings = Settings()
        super().__init__(
            width=self.settings.screen_width,
            height=self.settings.screen_height,
            title=self.settings.title,
        )

        self.ui_manager = gui.UIManager()
        self.hud_layer = HUDLayer()
        self.ui = GameUI(
            self.ui_manager,
            self.hud_layer,
            on_resume=self._resume_game,
            on_main_menu=self._return_to_main_menu,
            on_new_game=self.start_new_game,
            on_exit_game=self.close,
        )

        self.message_log = self.hud_layer.message_log

        self.level = None
        self.scene = None
        self.player_sprite = None
        self.camera = None
        self.camera_controller = None
        self.light_layer = None
        self.player_light = None
        self.stairs_xy = None
        self.depth = 1
        self.state = StateManager()
        self.turn_controller = TurnController(
            self.state,
            self.message_log,
            on_player_dead=self._show_game_over,
            on_depth_advance=self._advance_depth,
        )
        self.movement_input = MovementInputState(
            PLAYER_HORIZONTAL_KEYS,
            PLAYER_VERTICAL_KEYS,
            diagonal_window=PLAYER_INPUT_DIAGONAL_WINDOW,
        )

    def setup(self):
        self.ui.setup()
        self.ui.set_hud_visible(False)
        self.ui.show_view_screen(ViewScreenId.MAIN_MENU)

    def start_new_game(self, *, keep_player: bool = False) -> None:
        carryover = PlayerCarryover.capture(
            self.player_sprite,
            self.camera_controller,
            keep_player=keep_player,
        )

        self.depth = next_depth(self.depth, keep_player=keep_player)
        self.ui.clear_view_screen()
        self.ui.clear_overlay()
        self.ui.set_hud_visible(True)
        self.movement_input.clear()
        self.turn_controller.clear()

        built_scene = build_level_scene(depth=self.depth, player_carryover=carryover)
        self.level = built_scene.level
        self.scene = built_scene.scene
        self.player_sprite = built_scene.player
        self.stairs_xy = built_scene.stairs_xy

        self.camera = arcade.camera.Camera2D(
            position=self.player_sprite.position,
            zoom=carryover.zoom,
        )
        self.camera_controller = CameraController(
            self.camera,
            world_width=built_scene.world_width,
            world_height=built_scene.world_height,
            initial_zoom=carryover.zoom,
        )

        self.light_layer = LightLayer(self.settings.screen_width, self.settings.screen_height)
        self.light_layer.set_background_color((0, 0, 0, 255))
        self.player_light = Light(
            self.player_sprite.center_x,
            self.player_sprite.center_y,
            radius=180,
            color=(255, 244, 216),
            mode="soft",
        )
        self.light_layer.add(self.player_light)

        self.turn_controller.configure(self.level, self.scene, self.player_sprite)
        self.state.enter_game()
        self.message_log.clear()
        self.message_log.push(f"Глубина {self.depth}", "system")

    def on_resize(self, width, height):
        super().on_resize(width, height)
        if self.camera_controller is not None:
            self.camera_controller.on_resize(width, height)
        elif self.camera is not None:
            self.camera.match_window()
        if self.light_layer is not None:
            self.light_layer.resize(width, height)

    def on_draw(self):
        self.clear()
        if self.state.is_in_game() and self.light_layer is not None and self.camera is not None and self.scene is not None:
            with self.light_layer:
                self.camera.use()
                self.scene.draw()
            self.light_layer.draw(ambient_color=(28, 24, 34, 255))
        self.ui.draw()

    def on_update(self, delta_time):
        if self.state.is_in_game() and self.player_sprite is not None:
            self.ui.update_hud(
                self.player_sprite.hp / self.player_sprite.max_hp,
                player_light_ratio(self.player_sprite),
            )

        if not self.state.is_in_game() or self.state.is_paused():
            return

        if self.scene:
            self.scene.update(delta_time)

        if self.camera_controller is not None and self.player_sprite is not None:
            self.camera_controller.update(self.player_sprite.position, delta_time)

        self._snap_moving_sprites()
        self._sync_player_light()

        if self.turn_controller.advance_after_player_animation(self.stairs_xy):
            return

        if self.turn_controller.is_player_dead():
            self._show_game_over()
            return

        self._process_player_movement(time.time())

    def _sync_player_light(self) -> None:
        if self.player_light is None or self.player_sprite is None:
            return
        self.player_light.position = self.player_sprite.position
        ratio = player_light_ratio(self.player_sprite)
        self.player_light.radius = 160 + 35 * ratio

    def _advance_depth(self) -> None:
        recover_player_light(self.player_sprite, DEPTH_LIGHT_RECOVERY)
        self.start_new_game(keep_player=True)

    def _show_game_over(self) -> None:
        self.movement_input.clear()
        self.turn_controller.clear()
        self.state.enter_main_menu()
        self.ui.clear_overlay()
        self.ui.set_hud_visible(False)
        self.ui.show_view_screen(ViewScreenId.GAME_OVER)

    def get_entity_at(self, tile_x: int, tile_y: int, list_name: str | None = None):
        return self.turn_controller.get_entity_at(tile_x, tile_y, list_name)

    def on_key_press(self, symbol, modifiers):
        if self.ui.handle_key_press(symbol, modifiers):
            return
        if self.ui.has_active_overlay():
            return

        if symbol == arcade.key.ESCAPE:
            self._pause_game()
            return

        if symbol == arcade.key.I:
            self._toggle_inventory()
            return

        if not self.state.is_in_game():
            return

        if symbol in (arcade.key.PLUS, arcade.key.EQUAL):
            if self.camera_controller is not None:
                self.camera_controller.zoom_in()
            return
        if symbol in (arcade.key.MINUS, arcade.key.UNDERSCORE):
            if self.camera_controller is not None:
                self.camera_controller.zoom_out()
            return

        now = time.time()

        if symbol in PLAYER_DIRECTION_KEYS:
            self.movement_input.press(symbol, now)
            self._process_player_movement(now)
            return

        if not self.state.is_player_turn():
            return

        if symbol == arcade.key.SPACE:
            recover_player_light(self.player_sprite, PLAYER_WAIT_LIGHT_RECOVERY)
            self.turn_controller.wait_player_turn()
            return

    def on_key_release(self, symbol, modifiers):
        if not self.state.is_in_game() or self.ui.has_active_overlay():
            return
        self.movement_input.release(symbol, time.time())

    def _process_player_movement(self, now: float):
        if not self.state.is_player_turn():
            return

        move = self.movement_input.resolve_move(now)
        if move is None:
            return

        dx, dy = move
        res, _ = self.turn_controller.try_player_move(dx, dy)
        if self.turn_controller.is_wall_block(res):
            self.movement_input.mark_blocked(dx, dy)

    def _snap_moving_sprites(self):
        if self.scene is None:
            return

        zoom = self.camera_controller.zoom if self.camera_controller is not None else self.camera.zoom
        sprite_lists = getattr(self.scene, "sprite_lists", {})
        for sprites in sprite_lists.values():
            for sprite in sprites:
                if not getattr(sprite, "moving", False):
                    continue
                snapped_x, snapped_y = snap_world_point(sprite.center_x, sprite.center_y, zoom)
                sprite.position = (snapped_x, snapped_y)

    def _pause_game(self) -> None:
        if not self.state.pause():
            return
        self.movement_input.clear()
        self.ui.show_screen(OverlayScreenId.PAUSE)

    def _toggle_inventory(self) -> None:
        if not self.state.is_in_game() or self.player_sprite is None:
            return
        if self.ui.has_active_overlay():
            return
        if not self.state.pause():
            return
        inventory = getattr(self.player_sprite, "inventory", None)
        if inventory is None:
            self.state.resume()
            return
        self.movement_input.clear()
        self.ui.show_inventory(inventory)

    def _resume_game(self) -> None:
        if not self.state.resume():
            return
        self.movement_input.clear()
        self.ui.clear_overlay()

    def _return_to_main_menu(self) -> None:
        self.state.enter_main_menu()
        self.movement_input.clear()
        self.turn_controller.clear()
        self.ui.clear_overlay()
        self.ui.set_hud_visible(False)
        self.ui.show_view_screen(ViewScreenId.MAIN_MENU)
