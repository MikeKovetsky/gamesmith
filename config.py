from dataclasses import dataclass
from dotenv import load_dotenv
import os


load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))

@dataclass
class Config:
    style: str = "Photorealistic Hand-painted PBR, high fantasy"
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    wiki_cdn_url: str = "https://raw.githubusercontent.com/MikeKovetsky/gamesmith/refs/heads/main/wiki"
    wiki_path: str = os.path.join(current_dir, "wiki")
    unreal_engine_version: str = "5.5"


config = Config()