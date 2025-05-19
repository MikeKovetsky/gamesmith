from __future__ import annotations
import json
import requests
from pathlib import Path
from typing import List, Optional

from config import config
from smith.clients.openai import OpenAI
from smith.clients.replicate import Replicate
from smith.models.wiki import WikiType, wiki_type_to_path
from smith.utils.paths import get_assets_path, get_node_arts


wiki_type = WikiType.CHARACTER


def _build_prompt(character_path: str, existing_metadata: Optional[dict], user_prompt: str) -> str:
    """Construct the user prompt that will be sent to OpenAI.

    Parameters
    ----------
    character_path
        Relative path of the character inside *wiki/characters*.
    existing_metadata
        Already existing *metadata.json* (if any) so we can instruct the model to
        preserve or update the information.
    user_prompt
        Any extra guidance coming from the caller.
    """
    sections: List[str] = []

    if existing_metadata:
        sections.append(
            "Update the list of replicas for the character "
            f"{character_path}. Existing replicas: {existing_metadata.get('replicas', [])}. "
            "Keep the existing replicas unless they are clearly wrong and add new ones as necessary."
        )
    else:
        sections.append(f"Create a list of replicas for the character {character_path}.")

    guidelines: List[str] = [
        "Answer with a *valid JSON object* with exactly the following keys *in the root*: \n"
        "  - replicas: array of strings containing lines the character may say during gameplay. Provide at least 10 unique lines.\n"
        "  - voice_id: always the string \"1\" (hard-coded for now).\n"
        "  - items_to_drop: an (initially) empty array.\n",
        "Keep the content appropriate for a T-rated fantasy RPG.",
        "Do NOT include any additional keys or comments outside the JSON object.",
    ]

    sections.append("Guidelines:\n" + "\n".join(f"- {g}" for g in guidelines))

    if user_prompt:
        sections.append(f"Important additional user instructions: {user_prompt}")

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Main entry-point
# ---------------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # 1. Gather reference images (arts)
    # ------------------------------------------------------------------
    art_names = get_node_arts(wiki_type, character_path)
    art_urls = [
        f"{config.wiki_cdn_url}/{wiki_type_to_path[wiki_type]}/{character_path}/arts/{name}"
        for name in art_names
    ]

    if not art_urls:
        raise RuntimeError(f"No concept-art images found for character '{character_path}'.")

    # ------------------------------------------------------------------
    # 2. Prepare / fetch existing metadata and build prompt
    # ------------------------------------------------------------------
    metadata_path = get_node_map_path(wiki_type, character_path)
    existing_metadata: Optional[dict] = None
    if metadata_path.exists():
        try:
            existing_metadata = json.loads(metadata_path.read_text())
        except json.JSONDecodeError:
            print(f"⚠️  Existing metadata.json for '{character_path}' is not valid JSON – it will be ignored and regenerated.")

    user_prompt = _build_prompt(character_path, existing_metadata, custom_prompt)

    system_prompt = (
        "You are a creative game-writing assistant specialised in bringing NPCs and "
        "creatures to life through engaging dialogue."
    )

    response = OpenAI.complete(system_prompt, user_prompt, art_urls)

    # Ensure mandatory keys are present / have expected values.
    response.setdefault("voice_id", "1")
    response.setdefault("items_to_drop", [])

    # ------------------------------------------------------------------
    # 3. Persist metadata to disk
    # ------------------------------------------------------------------
    metadata_path.write_text(json.dumps(response, indent=2), encoding="utf-8")
    print(f"Metadata saved to {metadata_path.relative_to(Path.cwd())}")

    # ------------------------------------------------------------------
    # 4. Build 3-D model with Trellis (skip if it already exists)
    # ------------------------------------------------------------------
    models_dir = get_assets_path(wiki_type, character_path)
    models_dir.mkdir(parents=True, exist_ok=True)
    model_file_path = models_dir / f"{character_path.split('/')[-1]}.glb"

    if model_file_path.exists():
        print(f"3-D model already exists → {model_file_path.relative_to(Path.cwd())}")
        return response

    print(f"Generating 3-D model for '{character_path}' with Trellis…")
    trellis_input = {
        "seed": 0,
        "images": art_urls,  # We pass *all* concept-art images to Trellis
        "texture_size": 2048,
        "mesh_simplify": 0.9,
        "generate_color": True,
        "generate_model": True,
        "randomize_seed": True,
        "generate_normal": False,
        "save_gaussian_ply": True,
        "ss_sampling_steps": 38,
        "slat_sampling_steps": 12,
        "return_no_background": False,
        "ss_guidance_strength": 7.5,
        "slat_guidance_strength": 3,
    }

    trellis_response = Replicate.run_replicate(
        model="firtoz/trellis:e8f6c45206993f297372f5436b90350817bd9b4a0d52d2a76df50c1c8afa2b3c",
        input=trellis_input,
    )

    model_url: str = trellis_response["model_file"]

    try:
        model_bytes = requests.get(model_url).content
    except Exception as exc:
        raise RuntimeError(f"Failed to download Trellis model from {model_url!r}: {exc}")

    with open(model_file_path, "wb") as fp:
        fp.write(model_bytes)
    print(f"3-D model stored at {model_file_path.relative_to(Path.cwd())}")

    return response


if __name__ == "__main__":
    create_character("mobs/crab")
