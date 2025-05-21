from pathlib import Path

from config import config
from smith.models.node import Node
from smith.models.wiki import WikiType, wiki_type_to_path


def get_node_path(wiki_type: WikiType, node_name: str) -> Path:
    """Return an absolute path inside the wiki for the given *level_path*.

    The *level_path* must be specified relative to the ``locations`` folder and
    may point either to a **location** folder (e.g. ``"caladyn"``).
    """
    return Path(config.wiki_path) / wiki_type_to_path[wiki_type] / node_name


def get_node_map_path(wiki_type: WikiType, node_name: str) -> Path:
    return get_node_path(wiki_type, node_name) / "map.json"


def get_assets_path(wiki_type: WikiType, node_name: str) -> Path:
    return get_node_path(wiki_type, node_name) / "assets"


def get_model_path(wiki_type: WikiType, node_name: str) -> Path:
    return get_assets_path(wiki_type, node_name) / "models"


def get_texture_path(wiki_type: WikiType, node_name: str) -> Path:
    return get_assets_path(wiki_type, node_name) / "textures"


def get_node_arts(wiki_type: WikiType, node_name: str) -> list[str]:
    node_path = get_node_path(wiki_type, node_name)
    arts_path = node_path / "assets" / "arts"
    return [f.name for f in arts_path.glob("*.png")]


def get_art_url(wiki_type: WikiType, node_name: str, art_name: str) -> str:
    return f"{config.wiki_cdn_url}/{wiki_type_to_path[wiki_type]}/{node_name}/assets/arts/{art_name}"


def get_node_map(wiki_type: WikiType, node_name: str) -> Node:
    path = get_node_path(wiki_type, node_name)
    map_path = path / "map.json"
    if map_path.exists():
        return Node.model_validate_json(map_path.read_text())
    else:
        raise FileNotFoundError(f"Node map not found for {node_name}")


def get_prepared_assets_path(wiki_type: WikiType, node_name: str) -> Path:
    """Return the *prepared_arts* directory for a given node.

    The folder sits next to ``assets/arts`` and stores images that have been
    automatically processed (e.g. background-removed, T-pose, transparent).
    """
    return get_assets_path(wiki_type, node_name) / "prepared_arts"