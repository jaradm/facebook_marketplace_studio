import os
from pathlib import Path

from config import AI_MODEL
from models import ProductListing

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


class AIDescriptionService:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.client = OpenAI(api_key=self.api_key) if self.api_key and OpenAI is not None else None

    def available(self) -> bool:
        return self.client is not None

    def generate_description(self, product: ProductListing) -> str:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY is not set, or the openai package is not installed.")
        if not product.image_paths:
            raise RuntimeError("No image found for this product.")

        first_image = Path(product.image_paths[0])
        prompt = (
            "You are writing a Facebook Marketplace product listing. "
            "Analyze the product photo and draft a concise, appealing description. "
            "Do not invent specs you cannot see. "
            "Keep it honest and suitable for a local Marketplace post. "
            "Do not say pickup only. State that delivery is included. "
            "Do not mention payment amounts in the paragraph because those will be added separately below the description. "
            "Return only the description text.\n\n"
            f"Title: {product.title}\n"
            f"Item Number: {product.item_number}\n"
            f"Existing Description: {product.description}\n"
        )

        response = self.client.responses.create(
            model=AI_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/{first_image.suffix.lstrip('.').lower()};base64,{self._to_base64(first_image)}",
                        },
                    ],
                }
            ],
        )
        text = getattr(response, "output_text", "")
        if not text:
            raise RuntimeError("The AI service returned an empty description.")
        return text.strip()

    @staticmethod
    def _to_base64(path: Path) -> str:
        import base64
        return base64.b64encode(path.read_bytes()).decode("utf-8")
