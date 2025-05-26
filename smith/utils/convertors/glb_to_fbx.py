from pathlib import Path
import subprocess


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