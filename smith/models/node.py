from pydantic import BaseModel
from smith.models.asset import Asset


class Node(BaseModel):
    name: str
    description: str
    style: str
    assets: list[Asset] = []
