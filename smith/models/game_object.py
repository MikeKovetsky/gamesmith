from enum import Enum
from typing import Optional

from pydantic import BaseModel


class GameObjectType(str, Enum):
    Object = "object"
    Texture = "texture"
    Audio = "audio"


object_types = [GameObjectType.Object.value, GameObjectType.Texture.value, GameObjectType.Audio.value]


class GameObject(BaseModel):
    name: str
    description: str
    type: GameObjectType
    prompt: str
    quantity: Optional[int] = None
    placement_notes: Optional[str] = None