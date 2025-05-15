from dataclasses import dataclass
from dotenv import load_dotenv
import os


load_dotenv()

@dataclass
class Config:
    style: str = "Photorealistic Hand-painted PBR, high fantasy"
    openai_api_key: str = os.getenv("OPENAI_API_KEY")


config = Config()