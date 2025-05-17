from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, List

from smith.assetsmith.object import create_object
from smith.models.node import Scene
from smith.models.asset import Asset, AssetType
from smith.assetsmith.texture import create_texture
from smith.utils.paths import get_scene_wiki

__all__ = [
    "create_scene",
]


async def _create_asset(scene: Scene, asset: Asset) -> Any:
    """Dispatch asset creation based on *type*.

    Audio assets are currently ignored.
    """
    match asset.type:
        case AssetType.Texture:
            return await asyncio.to_thread(create_texture, scene, asset)
        case AssetType.Object:
            return await asyncio.to_thread(create_object, scene, asset)
        case AssetType.Audio:
            # Skip audio for now – return None so the caller knows it was ignored.
            return None
        case _:
            raise ValueError(f"Unsupported AssetType: {asset.type}")


async def create_scene(location_name: str, scene_name: str) -> Scene:
    """Create all the assets described in *scene_wiki* in parallel.

    The function reads the *scene_wiki.json* file, validates it against the
    ``Scene`` Pydantic model and then concurrently spawns the creation of each
    asset with :pyfunc:`_create_asset`.

    Parameters
    ----------
    scene_wiki_path : str | pathlib.Path
        Path to the *scene_wiki.json* file.

    Returns
    -------
    Scene
        The validated scene model. The caller may inspect / mutate it to attach
        references to the generated assets.
    """

    scene = get_scene_wiki(location_name, scene_name)

    tasks = [
        asyncio.create_task(_create_asset(scene, asset)) for asset in scene.assets
    ]

    await asyncio.gather(*tasks)

    return scene


if __name__ == "__main__":
    asyncio.run(create_scene("caladyn", "cala/market"))