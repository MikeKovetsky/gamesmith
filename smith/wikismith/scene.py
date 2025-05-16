import os
import json
from pathlib import Path
from typing import List

from smith.clients.openai import OpenAI
from config import config
from smith.models.location import Location
from smith.models.scene import Scene
from smith.models.game_object import object_types


def create_scene_wiki(location_name: str, scene: str, prompt: str):
    """
    Creates a JSON file describing all assets needed for a location in Unreal Engine 5.5.
    
    Args:
        location_name (str): Name of the location
        scene (str): Name of the scene
        prompt (str): Prompt to use for the location
    Returns:
        Location: The created location data as a Pydantic model
    """
    location_path = _get_location_path(location_name)
    scene_path = _get_scene_path(location_name, scene)
    scene_wiki_path = scene_path / "scene_wiki.json"
    arts_path = scene_path / "arts"
    arts_names = [f.name for f in arts_path.glob("*.png")]
    arts_urls = [f"{config.wiki_cdn_url}/locations/{location_name}/scenes/{scene}/arts/{art_name}" for art_name in arts_names]
    
    location_wiki = _get_location_wiki(location_name)
    scene_wiki = _get_scene_wiki(location_name, scene)

    user_prompt = build_prompt(
        location_wiki=location_wiki,
        scene_wiki=scene_wiki,
        user_prompt=prompt,
    )
    
    system_prompt = f"You are a game development assistant specializing in Unreal Engine {config.unreal_engine_version} asset management and prompt engineering."
    location_data_dict = OpenAI.complete(system_prompt, user_prompt, arts_urls)
    location_data = Scene(**location_data_dict)
    location_path.mkdir(parents=True, exist_ok=True)
    
    with open(scene_wiki_path, 'w', encoding='utf-8') as f:
        f.write(location_data.model_dump_json(indent=2))
    
    print(f"Scene wiki saved to {scene_wiki_path}")
    return location_data


def build_prompt(location_wiki: Location, scene_wiki: Scene, user_prompt: str) -> str:
    """Compose the prompt sent to the LLM from smaller reusable sections.

    Args:
        location_wiki: Metadata read from ``location_wiki.json``.
        scene_wiki: Metadata read from ``scene_wiki.json``.
        user_prompt: Any additional instructions coming from the caller.
        existing_map: Parsed JSON data if this location already exists.

    Returns:
        A single string ready to be delivered to the LLM.
    """


    is_edit = scene_wiki.objects is not None and len(scene_wiki.objects) > 0
    sections: List[str] = [f"Edit and expand the scene" if is_edit else f"Create the scene."]
    guidelines: List[str] = [
        f"Answer with a detailed JSON description of all assets needed for a scene called '{scene_wiki}' in location '{location_wiki}' for use in Unreal Engine {config.unreal_engine_version}."
        "Look closely at the provided images of the scene."
        f"Extract ALL atomic {object_types} from the scene."
        f"Each object in 'objects' must include: name, description, type ({'/'.join(object_types)}), and an extensive 'prompt'.",
        """For any game object with type \"object\", the prompt MUST:
          - Describe the asset as an isolated object centred in frame
          - Be fully transparent background (no shadows, no environment) to facilitate later mesh extraction.
          - Include a detailed description of the object's appearance, texture, color, and any other relevant details.
        """,
        """For any game object with type \"texture\", the prompt MUST:
          - Describe a seamless, tileable texture that can repeat in all directions without visible seams.
          - Be captured under neutral, shadow-free lighting to avoid baked-in highlights or shadows.
          - Include information about surface qualities (roughness, metalness, normal detail) so PBR maps can be derived.
          - Provide the intended resolution or level of detail (e.g. 2 K, 4 K etc.).
        """,
        """For any game object with type \"audio\", the prompt MUST:
          - Describe the ambience or sound effect in detail (sources, mood, distance, activity level).
          - State the desired duration (e.g. 30 s loop, 5 s one-shot) and whether it should loop seamlessly.
          - Avoid referencing copyrighted material; all sounds must be original or royalty-free.
        """,
    ]

    if not is_edit:
        # Extra guidelines that only apply during creation
        guidelines = [
            "Do not include NPCs or characters.",
            "Include a wide variety of objects, textures, and audio suitable for this environment.",
        ] + guidelines

    sections.append("Guidelines:\n" + "\n".join(f"- {g}" for g in guidelines))

    # 5. JSON schema example for new locations
    if not is_edit:
        sections.append(
            "Format the response as a valid JSON object following this structure:\n" +
            json.dumps(
                {
                    "objects": [
                        {
                            "name": "object_name_in_snake_case",
                            "description": f"detailed description of the {'/'.join(object_types)}",
                            "type": "/".join(object_types),
                            "prompt": "Detailed prompt that will be used as is in an AI model",
                            "quantity": 1,
                            "placement_notes": f"where/how to place the {object_types}"
                        }
                    ]
                },
                indent=2
            )
        )

    # 6. User-supplied instructions
    sections.append(f"User instructions: {user_prompt}")

    return "\n\n".join(sections)
    


def _get_location_path(location_name: str) -> Path:
    folder = Path(os.path.abspath(__file__)).parent
    return folder / config.wiki_path / "locations" / location_name


def _get_scene_path(location_name: str, scene: str) -> Path:
    location_path = _get_location_path(location_name)
    return location_path / "scenes" / scene


def _get_location_wiki(location_name: str) -> Location:
    location_path = _get_location_path(location_name)
    metadata_path = location_path / "location_wiki.json"
    if metadata_path.exists():
        return Location.model_validate_json(metadata_path.read_text())
    return None


def _get_scene_wiki(location_name: str, scene: str) -> Scene:
    scene_path = _get_scene_path(location_name, scene)
    metadata_path = scene_path / "scene_wiki.json"
    if metadata_path.exists():
        return Scene.model_validate_json(metadata_path.read_text())
    return None


if __name__ == "__main__":
    create_scene_wiki(location_name="caladyn", scene="cala/market", prompt="")
