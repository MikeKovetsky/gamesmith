import concurrent.futures
import io
from pathlib import Path

import requests
from smith.clients.replicate import Replicate
from config import config
from PIL import Image

from smith.models.wiki import WikiType


def prepare_mesh_references(node_path: Path, wiki_type: WikiType, art_urls: list[str]) -> list[str]:
    """Ensure a prepared art PNG exists and return its remote URL for Trellis.

    The image is generated via Replicate `openai/gpt-image-1`, stored locally in
    `prepared_arts`, and its CDN URL is returned so Trellis can reference it.
    If the image already exists and no new generation happens, returns ``None``.
    """

    if not art_urls:
        return []

    prepared_image_urls = _build_images(node_path, wiki_type, art_urls)
    return prepared_image_urls


def _build_images(node_path: Path, wiki_type: WikiType, art_urls: list[str]) -> list[str]:
    prepared_dir = node_path / "assets" / "mesh_references"
    prepared_dir.mkdir(parents=True, exist_ok=True)
    angles = ["front", "back", "side"]
    
    def process_angle(angle):
        prepared_path = prepared_dir / f"{node_path.name}_{angle}.png"
        prompt = ""
        
        if wiki_type == WikiType.CHARACTER:
            prompt = (
                f"Create a full-body illustration of {node_path.name} standing on a completely transparent background; "
                f"Show the character in a neutral T-pose (arms extended horizontally) from the {angle} view. "
                f"Remove any weapons or other objects from the hands. "
            )
        elif wiki_type == WikiType.LOCATION:
            prompt = (
                f"Create a full-body location asset "
            )

        prompt = (
            f"Keep the style of the attached reference images. No background, only the character with alpha transparency. "
            f"Show the {wiki_type.value} from the {angle} view."
            f"Keep the size and aspect ratio of the attached reference images."
            f"Don't add any shadows, reflections, particles, flying objects, or other visual effects."
            f"This image will be used to generate a 3D model."
            f"Ensure the {wiki_type.value} is centered in the frame and positioned symmetrically. "
            f"Show the {wiki_type.value} with in perfect lighting like there is no shadows. "
            f"Keep details crisp and clear, especially around edges and features. "
            f"If the {wiki_type.value} has any distinctive features, accessories, or markings, ensure they are visible and accurate. "
            f"Make sure the {wiki_type.value}'s proportions are anatomically correct and consistent with the original reference."
            f"Never draw floors, walls, or other background elements."
        )

        image_url = _build_image(prompt, art_urls)
        _save_image(image_url, prepared_path)
        return image_url
    
    prepared_image_urls = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_angle = {executor.submit(process_angle, angle): angle for angle in angles}
        for future in concurrent.futures.as_completed(future_to_angle):
            prepared_image_urls.append(future.result())
    
    return prepared_image_urls


def _build_image(prompt: str, art_urls: list[str]) -> str:
    replicate_response = Replicate.run_replicate(
        model="openai/gpt-image-1",
        input={
            "prompt": prompt,
            "quality": "high",
            "background": "transparent",
            "moderation": "auto",
            "aspect_ratio": _get_aspect_ratio(art_urls),
            "output_format": "png",
            "number_of_images": 1,
            "input_images": art_urls,
            "openai_api_key": config.openai_api_key,
            "output_compression": 90,
        },
    )

    # The response is a list; grab the first image URL (object or dict).
    first = replicate_response[0]
    image_url = first.url if hasattr(first, "url") else first.get("url")
    return image_url


def _save_image(image_url: str, prepared_path: Path) -> None:
    image_bytes = requests.get(image_url).content
    with open(prepared_path, "wb") as fp:
        fp.write(image_bytes)
    print(f"Prepared art saved to {prepared_path.relative_to(Path.cwd())} (source: {image_url})")


def _get_aspect_ratio(art_urls: list[str]) -> str:
    if not art_urls:
        return "1:1"
        
    first_image = requests.get(art_urls[0]).content
    img = Image.open(io.BytesIO(first_image))
    width, height = img.size
    
    ratio = width / height
    if 0.9 <= ratio <= 1.1:
        return "1:1"
    elif ratio > 1.1:
        return "3:2"
    else:
        return "2:3"