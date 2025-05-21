from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from smith.assetsmith.mesh_references import prepare_mesh_references
from smith.assetsmith.mesh import build_mesh
from smith.character.prompt import build_prompt
from smith.models.wiki import WikiType
from smith.utils.paths import (
    get_art_url,
    get_node_arts,
    get_node_map_path,
    get_node_path,
)


wiki_type = WikiType.CHARACTER


def create_character(character_name: str, custom_prompt: str = "") -> dict:
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
    
    print(f"Creating character: {character_name}")

    metadata_path = get_node_map_path(wiki_type, character_name)
    existing_metadata: Optional[dict] = None
    if metadata_path.exists():
        try:
            existing_metadata = json.loads(metadata_path.read_text())
        except json.JSONDecodeError:
            print(f"⚠️  Existing map.json for '{character_name}' is not valid JSON – it will be ignored and regenerated.")

    user_prompt = build_prompt(character_name, existing_metadata, custom_prompt)

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

    build_mesh(character_name, wiki_type)

    return response


if __name__ == "__main__":
    mobs = [
        "dustmother",
    ]

    character_names = [f"caladyn/ashwalkers/{mob}" for mob in mobs]

    # Use a thread-pool to run network-bound tasks concurrently.
    max_workers = min(4, len(character_names))  # avoid spawning excessive threads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(create_character, name): name for name in character_names
        }

        for future in as_completed(future_to_path):
            name = future_to_path[future]
            try:
                future.result()
                print(f"✅ Finished {name}")
            except Exception as exc:
                print(f"❌ Error processing {name}: {exc}")
