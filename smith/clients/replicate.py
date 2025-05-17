
import os
import httpx
import replicate


_DEFAULT_TIMEOUT = httpx.Timeout(1200.0) 

_replicate_client = replicate.Client(
    api_token=os.getenv("REPLICATE_API_TOKEN"),
    timeout=_DEFAULT_TIMEOUT,
)


class Replicate:
     
     @staticmethod
     def run_replicate(model: str, input: dict):
          return _replicate_client.run(
               model,
               input=input
          )