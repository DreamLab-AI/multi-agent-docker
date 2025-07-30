"""OpenAI API interface for image generation."""

import base64
import aiohttp
import json
from typing import Optional

class OpenAIInterface:
    """Interface for OpenAI API."""

    def __init__(self, api_key: str, org_id: Optional[str] = None, api_url: str = "https://api.openai.com/v1/images/generations"):
        """
        Initializes the OpenAIInterface.
        Args:
            api_key: The OpenAI API key.
            org_id: The OpenAI organization ID.
            api_url: The URL for the image generation endpoint.
        """
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if org_id:
            self.headers["OpenAI-Organization"] = org_id

    async def generate_image(
        self,
        prompt: str,
        model: str = "gpt-image-1",
        size: str = "1024x1024",
        quality: str = "auto",
        n: int = 1,
    ) -> Optional[bytes]:
        """
        Generates an image using the OpenAI API.
        Args:
            prompt: The text prompt for the image generation.
            model: The model to use for generation.
            size: The size of the generated image.
            quality: The quality of the image.
            n: The number of images to generate.
        Returns:
            The image data in bytes, or None if an error occurred.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality,
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.api_url, json=payload, headers=self.headers, timeout=120) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"HTTP error occurred: {response.status} - {error_text}")
                        return None

                    response_json = await response.json()
                    print(f"OpenAI API Response: {json.dumps(response_json, indent=2)}")

                    # Check for b64_json first
                    if "b64_json" in response_json["data"][0]:
                        image_data = base64.b64decode(response_json["data"][0]["b64_json"])
                        return image_data

                    # Fallback to URL
                    image_url = response_json["data"][0]["url"]
                    async with session.get(image_url) as image_response:
                        if image_response.status != 200:
                            error_text = await image_response.text()
                            print(f"Failed to download image: {image_response.status} - {error_text}")
                            return None
                        image_data = await image_response.read()
                        return image_data

            except Exception as e:
                print(f"An error occurred: {e}")
                return None