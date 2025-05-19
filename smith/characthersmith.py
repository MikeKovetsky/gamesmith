from __future__ import annotations
import json
import requests
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import config
from smith.clients.replicate import Replicate
from smith.models.wiki import WikiType, wiki_type_to_path
from smith.utils.paths import (
    get_model_path,
    get_node_arts,
    get_node_map_path,
    get_prepared_assets_path,
)


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
        "  - replicas: empty list\n"
        "  - sounds: empty list.\n"
        "  - voice_id: always the string \"1\" (hard-coded for now).\n"
        "  - items_to_drop: an empty array.\n",
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
    
    print(f"Creating character: {character_path}")

    # ------------------------------------------------------------------
    # 1. Gather reference images (arts)
    # ------------------------------------------------------------------
    art_names = get_node_arts(wiki_type, character_path)
    # URLs of the original concept arts (remote)
    art_urls = [
        f"{config.wiki_cdn_url}/{wiki_type_to_path[wiki_type]}/{character_path}/assets/arts/{name}"
        for name in art_names
    ]

    if not art_urls:
        raise RuntimeError(f"No concept-art images found for character '{character_path}'.")

    # ------------------------------------------------------------------
    # 1b. Ensure prepared art exists and retrieve remote URL (transparent, T-pose if humanoid)
    # ------------------------------------------------------------------
    prepared_image_url = _ensure_prepared_art(character_path, art_names)

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

    user_prompt = _build_prompt(character_path, existing_metadata, custom_prompt)

    system_prompt = (
        "You are a creative game-writing assistant specialised in writing a config/metadata for NPCs and creatures."
    )

    response = {
        "replicas": [],
        "sounds": [],
        "voice_id": "1",
        "items_to_drop": [],
    }

    # Ensure mandatory keys are present / have expected values.
    response.setdefault("voice_id", "1")
    response.setdefault("items_to_drop", [])

    # ------------------------------------------------------------------
    # 3. Persist metadata to disk
    # ------------------------------------------------------------------
    metadata_path.write_text(json.dumps(response, indent=2), encoding="utf-8")
    print(f"Metadata saved to {metadata_path.relative_to(Path.cwd())}")

    # ------------------------------------------------------------------
    # 4. Build 3-D model with Trellis – use prepared arts when present
    # ------------------------------------------------------------------

    if prepared_image_url:
        trellis_images = [prepared_image_url]
    else:
        trellis_images = art_urls

    trellis_input = {
        "seed": 0,
        "images": trellis_images,
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

    models_dir = get_model_path(wiki_type, character_path)
    models_dir.mkdir(parents=True, exist_ok=True)
    model_file_path = models_dir / f"{character_path.split('/')[-1]}.glb"

    with open(model_file_path, "wb") as fp:
        fp.write(model_bytes)
    print(f"3-D model stored at {model_file_path.relative_to(Path.cwd())}")

    return response


def _ensure_prepared_art(character_path: str, art_names: List[str]) -> Optional[str]:
    """Ensure a prepared art PNG exists and return its remote URL for Trellis.

    The image is generated via Replicate `openai/gpt-image-1`, stored locally in
    `prepared_arts`, and its CDN URL is returned so Trellis can reference it.
    If the image already exists and no new generation happens, returns ``None``.
    """

    if not art_names:
        return None

    original_name: str = art_names[0]

    prepared_dir = get_prepared_assets_path(wiki_type, character_path)
    prepared_dir.mkdir(parents=True, exist_ok=True)
    prepared_path = prepared_dir / original_name

    if prepared_path.exists():
        print(f"Prepared art already exists → {prepared_path.relative_to(Path.cwd())}")
        return None

    print(f"Generating prepared art for '{character_path}' via Replicate (gpt-image-1)…")

    # Build a descriptive prompt – ensure transparent background and T-pose when applicable.
    char_name = character_path.split("/")[-1].replace("_", " ")
    prompt = (
        f"Full-body illustration of {char_name} standing on a completely transparent background; "
        f"if the character is humanoid, depict them in a neutral T-pose (arms extended horizontally). "
        f"Keep the style of the original image. No background, only the character with alpha transparency."
    )

    try:
        replicate_response = Replicate.run_replicate(
            model="openai/gpt-image-1",
            input={
                "prompt": prompt,
                "quality": "high",
                "background": "transparent",
                "moderation": "auto",
                "aspect_ratio": "1:1",
                "output_format": "png",
                "number_of_images": 1,
                "openai_api_key": config.openai_api_key,
                "output_compression": 90,
            },
        )

        # The response is a list; grab the first image URL (object or dict).
        first = replicate_response[0]
        image_url = first.url if hasattr(first, "url") else first.get("url")

        # Download and save locally for Trellis.
        image_bytes = requests.get(image_url).content
        with open(prepared_path, "wb") as fp:
            fp.write(image_bytes)
        print(f"Prepared art saved to {prepared_path.relative_to(Path.cwd())} (source: {image_url})")
        return image_url
    except Exception as exc:
        print(f"⚠️  Failed to generate prepared art for '{character_path}': {exc}")
        return None


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
