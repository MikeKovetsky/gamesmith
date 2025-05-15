import os
import json
import openai
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union, Dict, Any

def build_prompt(*, location_name: str, location_description: str, user_prompt: str, existing_data: Optional[Dict[str, Any]] = None) -> str:
    """Compose the prompt sent to the LLM from smaller reusable sections.

    Args:
        location_name: The name of the location.
        location_description: Text description read from ``description.txt``.
        user_prompt: Any additional instructions coming from the caller.
        existing_data: Parsed JSON data if this location already exists.

    Returns:
        A single string ready to be delivered to the LLM.
    """

    sections: List[str] = []

    is_edit = existing_data is not None

    # 1. Opening directive
    if is_edit:
        sections.append(
            f"Edit and expand the definition of the location '{location_name}' for use in Unreal Engine 5.5."
        )
    else:
        sections.append(
            f"Create a detailed JSON description of all assets needed for a location called '{location_name}' in Unreal Engine 5.5."
        )

    # 2. Location description provided by the user
    sections.append(
        "Here is the location description:\n```\n" + location_description + "\n```"
    )

    # 3. Existing data, if any
    if is_edit:
        sections.append(
            "Here is the existing location data:\n```\n" + json.dumps(existing_data, indent=2) + "\n```"
        )

    # 4. Guidelines (shared across modes)
    guidelines: List[str] = [
        "Maintain the same JSON structure (top-level keys: name, description, objects).",
        "Each object in 'objects' must include: name, description, type (object, texture, or audio), and an extensive 'prompt'.",
        "For any game object with type \"object\", the prompt MUST describe the asset as an isolated object centred in frame on a fully transparent background (no shadows, no environment) to facilitate later mesh extraction.",
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
                    "name": location_name,
                    "description": "Detailed description of the location",
                    "objects": [
                        {
                            "name": "object_name",
                            "description": "detailed description",
                            "type": "object",
                            "prompt": "Detailed generation prompt (isolated object, transparent background, etc.)",
                            "quantity": 1,
                            "placement_notes": "where/how to place the object"
                        }
                    ]
                },
                indent=2
            )
        )

    # 6. User-supplied instructions
    sections.append(f"User instructions: {user_prompt}")

    return "\n\n".join(sections)

class GameObject(BaseModel):
    name: str
    description: str
    type: Literal["object", "texture", "audio"]
    prompt: str
    quantity: Optional[int] = None
    placement_notes: Optional[str] = None
    application: Optional[str] = None
    duration: Optional[str] = None
    loop: Optional[bool] = None


class Location(BaseModel):
    name: str
    description: str
    objects: List[GameObject]
    


def create_location_wiki(location_name: str, prompt: str):
    """
    Creates a JSON file describing all assets needed for a location in Unreal Engine 5.5.
    
    Args:
        location_name (str): Name of the location
        prompt (str): Prompt to use for the location
    Returns:
        Location: The created location data as a Pydantic model
    """
    # Set up OpenAI API (ensure API key is set in environment variables)
    client = openai.OpenAI()
    
    # Define path for the location file
    folder = Path(os.path.abspath(__file__)).parent
    location_path = folder / location_name
    wiki_path = location_path / "location.json"
    description_path = location_path / "description.txt"
    
    # Check if we're in edit mode and if the location file exists
    existing_data = None
    if wiki_path.exists():
        try:
            with open(wiki_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            print(f"Loaded existing data for location '{location_name}'")
        except Exception as e:
            print(f"Warning: Could not load existing data: {str(e)}")
    

    location_description = description_path.read_text()

    # Use helper to build prompt.
    prompt = build_prompt(
        location_name=location_name,
        location_description=location_description,
        user_prompt=prompt,
        existing_data=existing_data,
    )
    
    # Call the OpenAI API
    system_prompt = "You are a game development assistant specializing in Unreal Engine 5.5 asset management and prompt engineering."
    if existing_data:
        system_prompt += " You are enhancing and expanding an existing location definition."
    
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    content = response.choices[0].message.content
    location_data_dict = json.loads(content)
    location_data = Location(**location_data_dict)
    location_path.mkdir(parents=True, exist_ok=True)
    
    with open(wiki_path, 'w', encoding='utf-8') as f:
        f.write(location_data.model_dump_json(indent=2))
    
    print(f"Location data saved to {wiki_path}")
    return location_data



if __name__ == "__main__":
    create_location_wiki(location_name="caladyn", prompt="")
