import sys
from pathlib import Path

import arcade
from arcade.gl.enums import NEAREST

from sv.game import Game


def configure_assets() -> None:
    asset_dir = Path(sys.argv[0]).resolve().parents[1] / "assets"
    arcade.resources.add_resource_handle("assets", asset_dir)


def configure_rendering() -> None:
    arcade.SpriteList.DEFAULT_TEXTURE_FILTER = NEAREST, NEAREST


def main() -> None:
    configure_assets()
    configure_rendering()
    game = Game()
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()
