from typing import Optional


def build_prompt(character_path: str, existing_metadata: Optional[dict], user_prompt: str) -> str:
    """Construct the user prompt that will be sent to OpenAI.

    Parameters
    ----------
    character_path
        Relative path of the character inside *wiki/characters*.
    existing_metadata
        Already existing *metadata.json* (if any) so we can instruct the model to
        preserve or update the information.
    user_prompt
        Any extra guidance coming from the caller.
    """
    sections: list[str] = []

    if existing_metadata:
        sections.append(
            "Update the list of replicas for the character "
            f"{character_path}. Existing replicas: {existing_metadata.get('replicas', [])}. "
            "Keep the existing replicas unless they are clearly wrong and add new ones as necessary."
        )
    else:
        sections.append(f"Create a list of replicas for the character {character_path}.")

    guidelines: list[str] = [
        "Answer with a *valid JSON object* with exactly the following keys *in the root*: \n"
        "  - lines: empty list\n"
        "  - sounds: empty list.\n"
        "  - voice_id: always the string \"1\" (hard-coded for now).\n"
        "  - items_to_drop: an empty array.\n",
        "Do NOT include any additional keys or comments outside the JSON object.",
    ]

    sections.append("Guidelines:\n" + "\n".join(f"- {g}" for g in guidelines))

    if user_prompt:
        sections.append(f"Important additional user instructions: {user_prompt}")

    return "\n\n".join(sections)
