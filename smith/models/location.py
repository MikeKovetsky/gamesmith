from typing import List
from pydantic import BaseModel

from smith.models.game_object import GameObject

class Location(BaseModel):
    name: str
    description: str
    style: str