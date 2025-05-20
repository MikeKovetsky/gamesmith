from __future__ import annotations

import asyncio
from typing import Any

from smith.assetsmith.object import create_object
from smith.models.node import Node
from smith.models.asset import Asset, AssetType
from smith.assetsmith.texture import create_texture
from smith.models.wiki import WikiType
from smith.utils.paths import get_node_map

__all__ = [
    "create_scene",
]


async def _create_asset(node: Node, asset: Asset) -> Any:
    """Dispatch asset creation based on *type*.

    Audio assets are currently ignored.
    """
    match asset.type:
        case AssetType.Texture:
            return await asyncio.to_thread(create_texture, node, asset)
        case AssetType.Object:
            return await asyncio.to_thread(create_object, node, asset)
        case AssetType.Audio:
            # Skip audio for now – return None so the caller knows it was ignored.
            return None
        case _:
            raise ValueError(f"Unsupported AssetType: {asset.type}")


async def create_assets(node_name: str) -> Node:

    node = get_node_map(WikiType.LOCATION, node_name)
    
    if not node.assets:
        raise ValueError(f"No assets found in map for node: {node_name}")

    tasks = [
        asyncio.create_task(_create_asset(node, asset)) for asset in node.assets
    ]

    await asyncio.gather(*tasks)

    return node


if __name__ == "__main__":
    asyncio.run(create_assets("caladyn/aroth-kai"))