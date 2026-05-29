import sys
from pathlib import Path

import arcade
from arcade.gl.enums import NEAREST

from sv.game import Game


def find_asset_dir() -> Path:
    standalone_asset_dir = Path(sys.executable).resolve().parent / "assets"
    if standalone_asset_dir.is_dir():
        return standalone_asset_dir

    source_asset_dir = Path(__file__).resolve().parents[1] / "assets"
    if source_asset_dir.is_dir():
        return source_asset_dir

    raise FileNotFoundError(
        "Could not find Shardveil assets. Expected an 'assets' directory next to "
        "the standalone executable or at the project root."
    )


def configure_assets() -> None:
    arcade.resources.add_resource_handle("assets", find_asset_dir())


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
