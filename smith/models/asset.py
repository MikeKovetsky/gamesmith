from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AssetType(str, Enum):
    Object = "object"
    Texture = "texture"
    Audio = "audio"


asset_types = [AssetType.Object.value, AssetType.Texture.value, AssetType.Audio.value]


class Asset(BaseModel):
    name: str
    description: str
    type: AssetType
    prompt: str
    quantity: Optional[int] = None
    placement_notes: Optional[str] = None