from __future__ import annotations

import time

import arcade
from arcade import gui

from sv.core import (
    Settings,
    StateManager,
)
from sv.core.player_resources import (
    DEPTH_LIGHT_RECOVERY,
    PlayerCarryover,
    next_depth,
    player_light_ratio,
    recover_player_light,
)
from sv.core.player_input import PlayerInputController
from sv.core.rendering import GameRenderer
from sv.core.turn_controller import TurnController
from sv.ui import GameUI, HUDLayer, OverlayScreenId, ViewScreenId
from sv.world.scene_builder import build_level_scene


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
        self.renderer = GameRenderer(self.settings)
        self.stairs_xy = None
        self.depth = 1
        self.state = StateManager()
        self.turn_controller = TurnController(
            self.state,
            self.message_log,
            on_player_dead=self._show_game_over,
            on_depth_advance=self._advance_depth,
        )
        self.player_input = PlayerInputController(self.state, self.turn_controller)

    def setup(self):
        self.ui.setup()
        self.ui.set_hud_visible(False)
        self.ui.show_view_screen(ViewScreenId.MAIN_MENU)

    def start_new_game(self, *, keep_player: bool = False) -> None:
        carryover = PlayerCarryover.capture(
            self.player_sprite,
            self.renderer,
            keep_player=keep_player,
        )

        self.depth = next_depth(self.depth, keep_player=keep_player)
        self.ui.clear_view_screen()
        self.ui.clear_overlay()
        self.ui.set_hud_visible(True)
        self.player_input.clear()
        self.turn_controller.clear()

        built_scene = build_level_scene(depth=self.depth, player_carryover=carryover)
        self.level = built_scene.level
        self.scene = built_scene.scene
        self.player_sprite = built_scene.player
        self.stairs_xy = built_scene.stairs_xy

        self.renderer.configure(built_scene, zoom=carryover.zoom)
        self.turn_controller.configure(self.level, self.scene, self.player_sprite)
        self.state.enter_game()
        self.message_log.clear()
        self.message_log.push(f"Глубина {self.depth}", "system")

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.renderer.resize(width, height)

    def on_draw(self):
        self.clear()
        if self.state.is_in_game():
            self.renderer.draw(self.scene)
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

        self.renderer.update(self.player_sprite, delta_time)

        if self.turn_controller.advance_after_player_animation(self.stairs_xy):
            return

        if self.turn_controller.is_player_dead():
            self._show_game_over()
            return

        self.player_input.process_movement(time.time())

    def _advance_depth(self) -> None:
        recover_player_light(self.player_sprite, DEPTH_LIGHT_RECOVERY)
        self.start_new_game(keep_player=True)

    def _show_game_over(self) -> None:
        self.player_input.clear()
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
            self.renderer.zoom_in()
            return
        if symbol in (arcade.key.MINUS, arcade.key.UNDERSCORE):
            self.renderer.zoom_out()
            return

        now = time.time()

        if self.player_input.handle_direction_press(symbol, now):
            return

        if not self.state.is_player_turn():
            return

        if symbol == arcade.key.SPACE:
            self.player_input.wait_turn(self.player_sprite)
            return
        if symbol == arcade.key.C:
            self.turn_controller.pick_up_at_player()
            return

    def on_key_release(self, symbol, modifiers):
        if not self.state.is_in_game() or self.ui.has_active_overlay():
            return
        self.player_input.release(symbol, time.time())

    def _pause_game(self) -> None:
        if not self.state.pause():
            return
        self.player_input.clear()
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
        self.player_input.clear()
        self.ui.show_inventory(inventory)

    def _resume_game(self) -> None:
        if not self.state.resume():
            return
        self.player_input.clear()
        self.ui.clear_overlay()

    def _return_to_main_menu(self) -> None:
        self.state.enter_main_menu()
        self.player_input.clear()
        self.turn_controller.clear()
        self.ui.clear_overlay()
        self.ui.set_hud_visible(False)
        self.ui.show_view_screen(ViewScreenId.MAIN_MENU)
