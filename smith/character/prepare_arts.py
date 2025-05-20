import concurrent.futures
from pathlib import Path

import requests
from smith.clients.replicate import Replicate
from smith.models.wiki import WikiType
from smith.utils.paths import get_prepared_assets_path
from config import config


wiki_type = WikiType.CHARACTER


def prepare_arts(character_path: str, art_urls: list[str]) -> list[str]:
    """Ensure a prepared art PNG exists and return its remote URL for Trellis.

    The image is generated via Replicate `openai/gpt-image-1`, stored locally in
    `prepared_arts`, and its CDN URL is returned so Trellis can reference it.
    If the image already exists and no new generation happens, returns ``None``.
    """

    if not art_urls:
        return []

    prepared_image_urls = _build_images(character_path, art_urls)
    return prepared_image_urls


def _build_images(character_path: str, art_urls: list[str]) -> list[str]:
    character_name = character_path.split("/")[-1].replace("_", " ")
    prepared_dir = get_prepared_assets_path(wiki_type, character_path)
    prepared_dir.mkdir(parents=True, exist_ok=True)
    angles = ["front", "back", "side"]
    
    def process_angle(angle):
        prepared_path = prepared_dir / f"{character_name}_{angle}.png"
        prompt = (f"Create a full-body illustration of {character_name} standing on a completely transparent background; "
                f"if the character is humanoid, depict them in a neutral T-pose (arms extended horizontally) from the {angle} view. "
                f"Keep the style of the original image. No background, only the character with alpha transparency. "
                f"Keep the size and aspect ratio of the original image.")
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
            "aspect_ratio": "1:1",
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