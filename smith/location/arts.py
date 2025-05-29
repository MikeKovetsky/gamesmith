from pathlib import Path
import requests
from config import config
from smith.clients.openai import OpenAI
from smith.clients.replicate import Replicate
from smith.models.asset import Asset
from smith.utils.paths import get_node_arts, get_art_url, get_node_map, get_node_path
from smith.models.wiki import WikiType
import concurrent.futures


def create_location_arts(location_node_name: str):
    arts_names = get_node_arts(WikiType.LOCATION, location_node_name)
    location_arts_urls = [get_art_url(WikiType.LOCATION, location_node_name, art_name) for art_name in arts_names]
    location_map = get_node_map(WikiType.LOCATION, location_node_name)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_asset = {
            executor.submit(_create_asset_art, asset, location_arts_urls): asset 
            for asset in location_map.assets
        }
        for future in concurrent.futures.as_completed(future_to_asset):
            asset = future_to_asset[future]
            asset_art_url = future.result()
            _save_image(asset_art_url, asset.name, location_node_name)


def _create_asset_art(asset: Asset, location_arts_urls: list[str]):
    print(f"Creating art for {asset.name}")
    prompt = (
        f"""
        You are an art director for a game. You are given: 
        - a list of images that show the location. 
        - a prompt that includes one of the assets from the location
        You need to create one image that shows the asset in the location.
        The image should be a single asset, not a combination of assets.
        The image should be in the style of the location.
        The asset is a {asset.type} called {asset.name}. 
        The visual prompt is {asset.prompt}. 
        The placement notes are {asset.placement_notes}.
        """
    )
    response = _build_image(prompt, location_arts_urls)
    return response


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
    first = replicate_response[0]
    image_url = first.url if hasattr(first, "url") else first.get("url")
    return image_url


def _save_image(image_url: str, asset_name: str, location_node_name: str) -> None:
    image_bytes = requests.get(image_url).content
    prepared_path = get_node_path(WikiType.LOCATION, location_node_name) / asset_name / "arts" / "art.png"
    prepared_path.parent.mkdir(parents=True, exist_ok=True)
    with open(prepared_path, "wb") as fp:
        fp.write(image_bytes)
    print(f"Prepared art saved to {prepared_path.relative_to(Path.cwd())} (source: {image_url})")
