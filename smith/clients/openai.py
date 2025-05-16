import json
import openai
from pydantic import BaseModel


class OpenAI(BaseModel):
     
    @staticmethod
    def complete(
        system_prompt: str, user_prompt: str, image_urls: list[str]
    ) -> dict:
        client = openai.OpenAI()
        image_messages = []
        for art_url in image_urls:
            image_messages.append({"type": "image_url", "image_url": {"url": art_url}})

        user_content = [{"type": "text", "text": user_prompt}] + image_messages

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=messages,
            temperature=0.7,
        )
        content = response.choices[0].message.content
        data_dict = json.loads(content)
        return data_dict
