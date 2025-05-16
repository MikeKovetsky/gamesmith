from openai import BaseModel
from smith.models.game_object import GameObject


class Scene(BaseModel):
    name: str
    description: str
    location: str
    objects: list[GameObject]
