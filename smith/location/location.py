import json

from smith.clients.openai import OpenAI
from config import config
from smith.location.assets import create_location_assets
from smith.location.map import create_location_map



def create_location(node_name: str, custom_prompt: str = ""):
    # create_location_map(node_name, custom_prompt)
    create_location_assets(node_name)
    


if __name__ == "__main__":
    create_location("caladyn/aroth-kai")


