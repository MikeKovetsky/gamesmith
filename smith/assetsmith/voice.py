from pydantic import BaseModel
from smith.clients.replicate import Replicate


class VoiceConfig(BaseModel):
     text: str
     emotion: str
     voice_id: str


def create_voice(voice_config: VoiceConfig) -> str:
     output = Replicate.run_replicate(
          "minimax/speech-02-hd",
          input={
               "text": voice_config.text,
               "pitch": 0,
               "speed": 1,
               "volume": 1,
               "bitrate": 128000,
               "channel": "mono",
               "emotion": voice_config.emotion,
               "voice_id": voice_config.voice_id,
               "sample_rate": 32000,
               "language_boost": "English",
               "english_normalization": True
          }
          )
     return output