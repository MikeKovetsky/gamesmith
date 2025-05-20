
import httpx
import replicate as r
from config import config


_DEFAULT_TIMEOUT = httpx.Timeout(1200.0) 

_replicate_client = r.Client(
    api_token=config.replicate_api_key,
    timeout=_DEFAULT_TIMEOUT,
)


class Replicate:
     
     @staticmethod
     def run_replicate(model: str, input: dict):
          return _replicate_client.run(
               model,
               input=input
          )