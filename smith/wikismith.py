import json
from typing import List, Optional

from smith.clients.openai import OpenAI
from config import config
from smith.models.asset import Asset, asset_types
from smith.models.node import Node
from smith.utils.paths import get_node_arts, get_node_map, get_node_map_path, get_node_path


def create_node_map(node_name: str, custom_prompt: str = ""):
    node_map = get_node_map(node_name)
    arts_names = get_node_arts(node_name)
    arts_urls = [f"{config.wiki_cdn_url}/locations/{node_name}/assets/arts/{art_name}" for art_name in arts_names]

    user_prompt = build_prompt(node_name, custom_prompt)
    system_prompt = (
        f"You are a game development assistant specializing in Unreal Engine {config.unreal_engine_version} "
        "asset management and prompt engineering."
    )
    response = OpenAI.complete(system_prompt, user_prompt, arts_urls)

    assets = [Asset(**asset) for asset in response["assets"]]

    node_map.assets = assets
    node_map_path = get_node_map_path(node_name)

    with open(node_map_path, "w", encoding="utf-8") as f:
        f.write(node_map.model_dump_json(indent=2))

    print(f"Node map saved to {node_map_path}")
    return node_map


def build_prompt(node_name: str, user_prompt: str) -> str:
    
    node = get_node_map(node_name)
    
    sections: List[str] = [
        f"Edit and expand the location: {node_name}" if node else f"Create the location: {node_name}."
    ]

    guidelines: List[str] = [
        f"Answer with a detailed JSON description of all assets needed for the location called {node_name}."
        f"The assets will be used to produce assets for in Unreal Engine {config.unreal_engine_version}."
        "Look closely at the provided reference images.",
        f"Extract ALL atomic {asset_types} from the images provided.",
        "Include a wide variety of objects, textures, and audio suitable for this environment.",
        "Do not include NPCs or characters.",
        """For any asset with type \"object\", the prompt MUST:
          - Describe the asset as an isolated object centred in frame
          - Be fully transparent background (no shadows, no environment) to facilitate later mesh extraction.
          - Include a detailed description of the object's appearance, texture, color, and any other relevant details.
        """,
        """For any asset with type \"texture\", the prompt MUST:
          - Describe a seamless, tileable texture that can repeat in all directions without visible seams.
          - Be captured under neutral, shadow-free lighting to avoid baked-in highlights or shadows.
          - Include information about surface qualities (roughness, metalness, normal detail) so PBR maps can be derived.
          - Provide 2 varations of the texture if the texture belongs to a minor/medium object.
          - Provide 3 subtle varations of the texture if the texture belongs to a major object (e.g. landscape texture for the entire biome).
          - Provide the intended resolution or level of detail (e.g. 2 K, 4 K etc.).
        """,
        """For any asset with type \"audio\", the prompt MUST:
          - Describe the ambience or sound effect in detail (sources, mood, distance, activity level).
          - State the desired duration (e.g. 30 s loop, 5 s one-shot) and whether it should loop seamlessly.
          - Avoid referencing copyrighted material; all sounds must be original or royalty-free.
        """,
    ]
    
    sections.append("Guidelines:\n" + "\n".join(f"- {g}" for g in guidelines))

    sections.append(
        "Format the response as a valid JSON object following this structure:\n"
        + json.dumps(
            {
                "assets": [
                    {
                        "name": "asset_name_in_snake_case",
                        "description": f"detailed description of the {'/'.join(asset_types)}",
                        "type": "/".join(asset_types),
                        "prompt": "Detailed prompt that will be used as is in an AI model",
                        "quantity": 1,
                        "placement_notes": f"where/how to place the {asset_types}"
                    }
                ]
            },
            indent=2,
        )
    )

    sections.append(f"User instructions: {user_prompt}")

    return "\n\n".join(sections)
    

if __name__ == "__main__":
    create_node_map("caladyn/cala/market")


