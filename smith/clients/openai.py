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
        if content is None:
            raise ValueError(f"No content returned from OpenAI. Message: {response.choices[0].message}")
        data_dict = json.loads(content)
        return data_dict

    @staticmethod
    def create_image(prompt: str, size: str = "1024x1024", model: str = "gpt-image-1") -> str:
        """Generate an image from a text prompt using the newest GPT image model.

        Parameters
        ----------
        prompt : str
            The textual description of the desired image.
        size : str, optional
            Resolution requested (e.g. "1024x1024"). Defaults to 1024×1024.
        model : str, optional
            Which image-generation model to use. Defaults to ``gpt-image-1`` as per
            https://platform.openai.com/docs/guides/image-generation?image-generation-model=gpt-image-1

        Returns
        -------
        str
            A direct URL to the generated image.
        """
        client = openai.OpenAI()
        response = client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            size=size,
            response_format="b64_json",
        )
        return response.data[0].b64_json
