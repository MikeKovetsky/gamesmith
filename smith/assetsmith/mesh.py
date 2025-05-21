from pathlib import Path
import subprocess

import requests

from smith.assetsmith.mesh_references import prepare_mesh_references
from smith.clients.replicate import Replicate
from smith.models.wiki import WikiType
from smith.utils.paths import get_art_url, get_model_path, get_node_arts, get_node_path


def build_mesh(node_name: str, wiki_type: WikiType) -> None:
    node_path = get_node_path(wiki_type, node_name)
    art_names = get_node_arts(wiki_type, node_name)
    art_urls = [
        get_art_url(wiki_type, node_name, name) for name in art_names
    ]

    if not art_urls:
        raise RuntimeError(f"No concept-art images found for character '{node_name}'.")

    mesh_references_urls = prepare_mesh_references(node_path, wiki_type, art_urls)
    trellis_input = {
        "seed": 0,
        "images": mesh_references_urls,
        "texture_size": 2048,
        "mesh_simplify": 0.9,
        "generate_color": True,
        "generate_model": True,
        "randomize_seed": True,
        "generate_normal": False,
        "save_gaussian_ply": True,
        "ss_sampling_steps": 50,
        "slat_sampling_steps": 50,
        "return_no_background": False,
        "ss_guidance_strength": 10,
        "slat_guidance_strength": 10,
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

    models_dir = get_model_path(wiki_type, node_name)
    models_dir.mkdir(parents=True, exist_ok=True)
    model_file_path = models_dir / f"{node_name}.glb"

    with open(model_file_path, "wb") as fp:
        fp.write(model_bytes)
    print(f"3-D model stored at {model_file_path.relative_to(Path.cwd())}")
    convert_glb_to_fbx(model_file_path)


def convert_glb_to_fbx(glb_path: Path, blender_exec: str = "/Applications/Blender.app/Contents/MacOS/Blender"):
    fbx_path = glb_path.with_suffix(".fbx")
    python_expr = f"""
import bpy

# Ensure Blender is in OBJECT mode
if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
elif not bpy.context.active_object and bpy.ops.object.mode_set.poll(): # If no active object, try to set mode if possible
    bpy.ops.object.mode_set(mode='OBJECT')

# Select all objects
bpy.ops.object.select_all(action='SELECT')

# Delete selected objects (this will clear the default cube, camera, light)
if bpy.context.selected_objects: # Check if there are any objects selected to delete
    bpy.ops.object.delete()

# Import the GLTF model
bpy.ops.import_scene.gltf(filepath=r'{glb_path}')

# Export the scene to FBX
bpy.ops.export_scene.fbx(
    filepath=r'{fbx_path}',
    embed_textures=True,
    path_mode='COPY'
)
"""
    subprocess.run([
        blender_exec,
        "--background",
        "--python-expr", python_expr
    ], check=True)
    print(f"Exported FBX to {fbx_path}")


if __name__ == "__main__":
    convert_glb_to_fbx(Path("/Users/mike/repos/gamesmith/wiki/characters/caladyn/ashwalkers/dustmother/assets/models/dustmother.glb"))
