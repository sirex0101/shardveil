import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sv.core.rendering import GameRenderer, RenderingFactories


class FakeSettings:
    screen_width = 800
    screen_height = 600


class FakeCamera:
    def __init__(self, *, position, zoom):
        self.position = position
        self.zoom = zoom
        self.use_calls = 0
        self.match_window_calls = 0

    def use(self):
        self.use_calls += 1

    def match_window(self):
        self.match_window_calls += 1


class FakeCameraController:
    def __init__(self, camera, *, world_width, world_height, initial_zoom):
        self.camera = camera
        self.world_width = world_width
        self.world_height = world_height
        self.zoom = initial_zoom
        self.resize_calls = []
        self.update_calls = []
        self.zoom_in_calls = 0
        self.zoom_out_calls = 0

    def on_resize(self, width, height):
        self.resize_calls.append((width, height))

    def update(self, position, delta_time):
        self.update_calls.append((position, delta_time))

    def zoom_in(self):
        self.zoom_in_calls += 1
        self.zoom += 1

    def zoom_out(self):
        self.zoom_out_calls += 1
        self.zoom -= 1


class FakeLightLayer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.background_color = None
        self.lights = []
        self.resize_calls = []
        self.draw_calls = []
        self.enter_count = 0

    def set_background_color(self, color):
        self.background_color = color

    def add(self, light):
        self.lights.append(light)

    def resize(self, width, height):
        self.resize_calls.append((width, height))

    def draw(self, *, ambient_color):
        self.draw_calls.append(ambient_color)

    def __enter__(self):
        self.enter_count += 1
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeLight:
    def __init__(self, x, y, *, radius, color, mode):
        self.position = (x, y)
        self.radius = radius
        self.color = color
        self.mode = mode


class FakePlayer:
    def __init__(self):
        self.position = (10.0, 20.0)
        self.center_x = 10.0
        self.center_y = 20.0
        self.light = 5
        self.light_max = 10

    def light_ratio(self):
        return self.light / self.light_max


class FakeSprite:
    def __init__(self, x, y, *, moving):
        self.center_x = x
        self.center_y = y
        self.moving = moving

    @property
    def position(self):
        return self.center_x, self.center_y

    @position.setter
    def position(self, value):
        self.center_x, self.center_y = value


class FakeScene:
    def __init__(self):
        self.draw_calls = 0
        self.sprite_lists = {
            "Actors": [
                FakeSprite(10.2, 5.49, moving=True),
                FakeSprite(1.2, 2.4, moving=False),
            ]
        }

    def draw(self):
        self.draw_calls += 1


class FakeBuildResult:
    def __init__(self):
        self.scene = FakeScene()
        self.player = FakePlayer()
        self.world_width = 640
        self.world_height = 480


class GameRendererTests(unittest.TestCase):
    def _renderer(self):
        renderer = GameRenderer(
            FakeSettings(),
            factories=RenderingFactories(
                camera=FakeCamera,
                camera_controller=FakeCameraController,
                light_layer=FakeLightLayer,
                light=FakeLight,
            ),
        )
        build_result = FakeBuildResult()
        renderer.configure(build_result, zoom=3.0)
        return renderer, build_result

    def test_current_zoom_returns_configured_zoom(self):
        renderer, _ = self._renderer()

        self.assertEqual(renderer.current_zoom, 3.0)
        self.assertEqual(renderer.zoom, 3.0)

    def test_zoom_controls_delegate_to_camera_controller(self):
        renderer, _ = self._renderer()

        renderer.zoom_in()
        renderer.zoom_out()

        self.assertEqual(renderer.camera_controller.zoom_in_calls, 1)
        self.assertEqual(renderer.camera_controller.zoom_out_calls, 1)
        self.assertEqual(renderer.current_zoom, 3.0)

    def test_resize_delegates_to_camera_controller_and_light_layer(self):
        renderer, _ = self._renderer()

        renderer.resize(1024, 768)

        self.assertEqual(renderer.camera_controller.resize_calls, [(1024, 768)])
        self.assertEqual(renderer.light_layer.resize_calls, [(1024, 768)])

    def test_update_tracks_player_snaps_moving_sprites_and_updates_light(self):
        renderer, build_result = self._renderer()
        player = build_result.player
        moving_sprite = build_result.scene.sprite_lists["Actors"][0]
        static_sprite = build_result.scene.sprite_lists["Actors"][1]

        renderer.update(player, 0.25)

        self.assertEqual(renderer.camera_controller.update_calls, [((10.0, 20.0), 0.25)])
        self.assertEqual(moving_sprite.position, (10.333333333333334, 5.333333333333333))
        self.assertEqual(static_sprite.position, (1.2, 2.4))
        self.assertEqual(renderer.player_light.position, (10.0, 20.0))
        self.assertEqual(renderer.player_light.radius, 177.5)

    def test_draw_uses_light_layer_camera_and_scene(self):
        renderer, build_result = self._renderer()

        renderer.draw(build_result.scene)

        self.assertEqual(renderer.light_layer.enter_count, 1)
        self.assertEqual(renderer.camera.use_calls, 1)
        self.assertEqual(build_result.scene.draw_calls, 1)
        self.assertEqual(renderer.light_layer.draw_calls, [(28, 24, 34, 255)])


if __name__ == "__main__":
    unittest.main()
