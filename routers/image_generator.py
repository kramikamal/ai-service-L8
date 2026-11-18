import base64
import binascii
from io import BytesIO

from fastapi import APIRouter, HTTPException
from PIL import Image
from pydantic import BaseModel

from routers.LLM import generate

image = APIRouter(prefix="/generate", tags=["generate"])


class ImageRequest(BaseModel):
    name: str
    description: str | list[str]


def thumbnail(encoded):
    # The product service accepts 256 KiB per product, including base64 and text.
    with Image.open(BytesIO(base64.b64decode(encoded, validate=True))) as source:
        source.thumbnail((384, 384))
        photo = source.convert("RGB")
    while True:
        output = BytesIO()
        photo.save(output, format="JPEG", quality=75)
        if output.tell() <= 96 * 1024:
            return "data:image/jpeg;base64," + base64.b64encode(output.getvalue()).decode("ascii")
        photo.thumbnail((max(1, photo.width // 2), max(1, photo.height // 2)))


@image.post("/image")
def post_image(product: ImageRequest):
    prompt = (
        f"Photograph the pet supply product {product.name} in its packaging against a plain "
        f"background for an online store. Product description: {product.description}"
    )
    result = generate("images/generations", {"prompt": prompt, "n": 1, "quality": "low"}, image=True)
    try:
        item = result["data"][0]
        if item.get("b64_json"):
            return {"image": thumbnail(item["b64_json"])}
        if isinstance(item.get("url"), str) and item["url"].startswith("https://"):
            return {"image": item["url"]}
    except (KeyError, IndexError, AttributeError, TypeError, binascii.Error, OSError, ValueError, Image.DecompressionBombError):
        pass
    raise HTTPException(502, "The AI provider did not return a readable image.")
