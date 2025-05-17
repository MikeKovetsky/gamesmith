import base64
from smith.models.asset import Asset
from smith.models.node import Scene
from smith.utils.paths import get_scene_path
from smith.clients.openai import OpenAI


def create_texture(scene: Scene, asset: Asset) -> str:
    """Create a texture asset via OpenAI's image generation endpoint."""
    
    print(f"Creating texture for {asset.name} in {scene.location} / {scene.name}")

    output_dir = get_scene_path(scene.location, scene.name) / "textures"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{asset.name}.png"
    dest_path = output_dir / filename
    
    if dest_path.exists():
        print(f"Texture {asset.name} already exists in {scene.location} / {scene.name}")
        return dest_path

    b64_image = OpenAI.create_image(prompt=asset.prompt, size="1024x1024")
    img_bytes = base64.b64decode(b64_image)
    dest_path.write_bytes(img_bytes)
    print(f"Saved texture to {dest_path}")