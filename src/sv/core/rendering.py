from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import arcade
from arcade.future.light import Light, LightLayer

from sv.core.camera_controller import CameraController, snap_world_point
from sv.core.config import Settings
from sv.core.player_resources import DEFAULT_CAMERA_ZOOM, player_light_ratio


PLAYER_LIGHT_BASE_RADIUS = 160
PLAYER_LIGHT_RADIUS_BONUS = 35
PLAYER_LIGHT_COLOR = (255, 244, 216)
AMBIENT_COLOR = (28, 24, 34, 255)
LIGHT_BACKGROUND_COLOR = (0, 0, 0, 255)


@dataclass(slots=True)
class RenderingFactories:
    camera: Callable[..., object] = arcade.camera.Camera2D
    camera_controller: Callable[..., CameraController] = CameraController
    light_layer: Callable[..., object] = LightLayer
    light: Callable[..., object] = Light


class GameRenderer:
    def __init__(
        self,
        settings: Settings,
        *,
        factories: RenderingFactories | None = None,
    ) -> None:
        self.settings = settings
        self.factories = factories or RenderingFactories()
        self.scene = None
        self.camera = None
        self.camera_controller = None
        self.light_layer = None
        self.player_light = None

    @property
    def current_zoom(self) -> float:
        if self.camera_controller is not None:
            return self.camera_controller.zoom
        if self.camera is not None:
            return self.camera.zoom
        return DEFAULT_CAMERA_ZOOM

    @property
    def zoom(self) -> float:
        return self.current_zoom

    def configure(self, scene_build_result, zoom: float = DEFAULT_CAMERA_ZOOM) -> None:
        self.scene = scene_build_result.scene
        player = scene_build_result.player
        self.camera = self.factories.camera(position=player.position, zoom=zoom)
        self.camera_controller = self.factories.camera_controller(
            self.camera,
            world_width=scene_build_result.world_width,
            world_height=scene_build_result.world_height,
            initial_zoom=zoom,
        )

        self.light_layer = self.factories.light_layer(
            self.settings.screen_width,
            self.settings.screen_height,
        )
        self.light_layer.set_background_color(LIGHT_BACKGROUND_COLOR)
        self.player_light = self.factories.light(
            player.center_x,
            player.center_y,
            radius=180,
            color=PLAYER_LIGHT_COLOR,
            mode="soft",
        )
        self.light_layer.add(self.player_light)

    def resize(self, width: int, height: int) -> None:
        if self.camera_controller is not None:
            self.camera_controller.on_resize(width, height)
        elif self.camera is not None:
            self.camera.match_window()
        if self.light_layer is not None:
            self.light_layer.resize(width, height)

    def update(self, player, delta_time: float) -> None:
        if self.camera_controller is not None and player is not None:
            self.camera_controller.update(player.position, delta_time)
        self._snap_moving_sprites()
        self._sync_player_light(player)

    def draw(self, scene=None) -> None:
        scene = scene if scene is not None else self.scene
        if scene is None or self.light_layer is None or self.camera is None:
            return
        with self.light_layer:
            self.camera.use()
            scene.draw()
        self.light_layer.draw(ambient_color=AMBIENT_COLOR)

    def zoom_in(self) -> None:
        if self.camera_controller is not None:
            self.camera_controller.zoom_in()

    def zoom_out(self) -> None:
        if self.camera_controller is not None:
            self.camera_controller.zoom_out()

    def _sync_player_light(self, player) -> None:
        if self.player_light is None or player is None:
            return
        self.player_light.position = player.position
        ratio = player_light_ratio(player)
        self.player_light.radius = PLAYER_LIGHT_BASE_RADIUS + PLAYER_LIGHT_RADIUS_BONUS * ratio

    def _snap_moving_sprites(self) -> None:
        if self.scene is None:
            return

        zoom = self.current_zoom
        sprite_lists = getattr(self.scene, "sprite_lists", {})
        for sprites in sprite_lists.values():
            for sprite in sprites:
                if not getattr(sprite, "moving", False):
                    continue
                snapped_x, snapped_y = snap_world_point(sprite.center_x, sprite.center_y, zoom)
                sprite.position = (snapped_x, snapped_y)
