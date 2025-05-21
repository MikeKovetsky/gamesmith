import asyncio
from typing import Any
from smith.assetsmith.mesh import build_mesh
from smith.models.asset import Asset, AssetType
from smith.models.node import Node
from smith.models.wiki import WikiType
from smith.utils.paths import get_node_map


wiki_type = WikiType.LOCATION


def create_location_assets(node_name: str):
    asyncio.run(create_assets(node_name))


async def _create_asset(node_name: str, asset: Asset) -> Any:
    """Dispatch asset creation based on *type*.

    Audio assets are currently ignored.
    """
    match asset.type:
        case AssetType.Texture:
            pass
            # return await asyncio.to_thread(create_texture, node, asset)
        case AssetType.Object:
            return await asyncio.to_thread(build_mesh, node_name, wiki_type)
        case AssetType.Audio:
            # Skip audio for now – return None so the caller knows it was ignored.
            return None
        case _:
            raise ValueError(f"Unsupported AssetType: {asset.type}")


async def create_assets(node_name: str) -> Node:

    node = get_node_map(wiki_type, node_name)
    
    if not node.assets:
        raise ValueError(f"No assets found in map for node: {node_name}")

    tasks = [
        asyncio.create_task(_create_asset(node_name, asset)) for asset in node.assets
    ]

    await asyncio.gather(*tasks)

    return node