from pathlib import Path

import requests

from smith.clients.replicate import Replicate
from smith.models.wiki import WikiType
from smith.utils.paths import get_model_path


wiki_type = WikiType.CHARACTER


def build_3d(character_path: str, image_urls: list[str]) -> None:
    trellis_input = {
        "seed": 0,
        "images": image_urls,
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