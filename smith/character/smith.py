from __future__ import annotations
import json
import requests
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from smith.assetsmith.mesh_references import prepare_mesh_references
from smith.character.build_3d import build_3d
from smith.character.prompt import build_prompt
from smith.models.wiki import WikiType
from smith.utils.paths import (
    get_art_url,
    get_node_arts,
    get_node_map_path,
    get_node_path,
)


wiki_type = WikiType.CHARACTER


def create_character(character_path: str, custom_prompt: str = "") -> dict:
    """Generate (or update) the assets for *character_path*.

    1. Reads the concept art stored under ``wiki/characters/<character_path>/arts``.
    2. Calls the OpenAI Chat Completion endpoint to generate/update a *metadata.json* file.
    3. Uses the Trellis model (via Replicate) to build a 3-D model from the first
       concept-art image, saving the result inside a *models* folder.

    Returns
    -------
    dict
        The freshly generated metadata dictionary.
    """
    
    print(f"Creating character: {character_path}")

    # ------------------------------------------------------------------
    # 1. Gather reference images (arts)
    # ------------------------------------------------------------------
    art_names = get_node_arts(wiki_type, character_path)
    art_urls = [
        get_art_url(wiki_type, character_path, name) for name in art_names
    ]

    if not art_urls:
        raise RuntimeError(f"No concept-art images found for character '{character_path}'.")

    # ------------------------------------------------------------------
    # 1b. Ensure prepared art exists and retrieve remote URL
    # ------------------------------------------------------------------
    node_path = get_node_path(wiki_type, character_path)
    mesh_references_urls = prepare_mesh_references(node_path, art_urls)

    # ------------------------------------------------------------------
    # 2. Prepare / fetch existing metadata and build prompt
    # ------------------------------------------------------------------
    metadata_path = get_node_map_path(wiki_type, character_path)
    existing_metadata: Optional[dict] = None
    if metadata_path.exists():
        try:
            existing_metadata = json.loads(metadata_path.read_text())
        except json.JSONDecodeError:
            print(f"⚠️  Existing map.json for '{character_path}' is not valid JSON – it will be ignored and regenerated.")

    user_prompt = build_prompt(character_path, existing_metadata, custom_prompt)

    system_prompt = (
        "You are a creative game-writing assistant specialised in writing a config/metadata for NPCs and creatures."
    )

    response = {
        "replicas": [],
        "sounds": [],
        "voice_id": "1",
        "items_to_drop": [],
    }

    # ------------------------------------------------------------------
    # 3. Persist metadata to disk
    # ------------------------------------------------------------------
    metadata_path.write_text(json.dumps(response, indent=2), encoding="utf-8")
    print(f"Metadata saved to {metadata_path.relative_to(Path.cwd())}")

    # ------------------------------------------------------------------
    # 4. Build 3-D model with Trellis – use prepared arts when present
    # ------------------------------------------------------------------

    build_3d(character_path, mesh_references_urls)

    return response


if __name__ == "__main__":
    mobs = [
        "dustmother",
    ]

    character_paths = [f"caladyn/ashwalkers/{mob}" for mob in mobs]

    # Use a thread-pool to run network-bound tasks concurrently.
    max_workers = min(4, len(character_paths))  # avoid spawning excessive threads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(create_character, path): path for path in character_paths
        }

        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                future.result()
                print(f"✅ Finished {path}")
            except Exception as exc:
                print(f"❌ Error processing {path}: {exc}")
