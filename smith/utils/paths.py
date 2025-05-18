import os
from pathlib import Path
from typing import Optional

from config import config
from smith.models.node import Node


def get_node_path(level_path: str) -> Path:
    """Return an absolute path inside the wiki for the given *level_path*.

    The *level_path* must be specified relative to the ``locations`` folder and
    may point either to a **location** folder (e.g. ``"caladyn"``).
    """
    return Path(config.wiki_path) / "locations" / level_path


def get_node_map_path(node_name: str) -> Path:
    return get_node_path(node_name) / "map.json"


def get_assets_path(node_name: str) -> Path:
    return get_node_path(node_name) / "assets"


def get_node_arts(node_name: str) -> list[str]:
    node_path = get_node_path(node_name)
    arts_path = node_path / "assets" / "arts"
    return [f.name for f in arts_path.glob("*.png")]


def get_node_map(node_name: str) -> Node:
    path = get_node_path(node_name)
    map_path = path / "map.json"
    if map_path.exists():
        return Node.model_validate_json(map_path.read_text())
    else:
        raise FileNotFoundError(f"Node map not found for {node_name}")