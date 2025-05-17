import base64

import requests
from smith.clients.openai import OpenAI
from smith.clients.replicate import Replicate
from smith.models.asset import Asset
from smith.models.node import Scene
from config import config
from smith.utils.paths import get_scene_path


def create_object(scene: Scene, game_object: Asset) -> str:
     output_dir = get_scene_path(scene.location, scene.name) / "models"
     output_dir.mkdir(parents=True, exist_ok=True)
     path = output_dir / f"{game_object.name}.glb"
     
     if path.exists():
          print(f"Object {game_object.name} already exists in {scene.location} / {scene.name}")
          return path
     
     print(f"Creating a reference image for {game_object.name}")
     reference_image_url = _create_reference_image(game_object)
     print(f"Creating object for {game_object.name} in {scene.location}/{scene.name} from {reference_image_url}")
     asset_url = _create_object(reference_image_url)
     print(f"Saved object from {asset_url}")
     bytes = requests.get(asset_url).content
     with open(path, "wb") as f:
          f.write(bytes)
     return path
     
     
def _create_reference_image(game_object: Asset) -> str:
     response = Replicate.run_replicate(
          model="openai/gpt-image-1", 
          input={
               "prompt": game_object.prompt,
               "quality": "high",
               "background": "transparent",
               "moderation": "auto",
               "aspect_ratio": "1:1",
               "output_format": "png",
               "number_of_images": 1,
               "openai_api_key": config.openai_api_key,
               "output_compression": 90
          })
     return response[0].url
     
     
def _create_object(reference_image_url: str) -> str:
     response = Replicate.run_replicate(
          model="firtoz/trellis:e8f6c45206993f297372f5436b90350817bd9b4a0d52d2a76df50c1c8afa2b3c", 
          input={
               "seed": 0,
               "images": [reference_image_url],
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
               "slat_guidance_strength": 3
          }
     )
     return response["model_file"]