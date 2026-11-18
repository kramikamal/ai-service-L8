import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from routers.LLM import enabled, generate, post_json

description = APIRouter(prefix="/generate", tags=["generate"])
prompt_template = (Path(__file__).resolve().parents[1] / "skills/ProductSkill/Description/skprompt.txt").read_text()


class DescriptionRequest(BaseModel):
    name: str
    tags: list[str]


@description.post("/description")
def post_description(product: DescriptionRequest):
    tags = ", ".join(product.tags)
    if enabled("USE_LOCAL_LLM"):
        endpoint = os.getenv("AI_ENDPOINT") or os.getenv("AZURE_OPENAI_GPT_ENDPOINT")
        if not endpoint or enabled("USE_AZURE_OPENAI"):
            raise HTTPException(503, "Check the local LLM endpoint and provider settings.")
        prompt = f"Describe this pet store product using joyful, playful, and enticing language.\nProduct name: {product.name}\ntags: {tags}\ndescription:\""
        result = post_json(endpoint, {"prompt": prompt, "temperature": 0.5, "top_p": 0.0})
        text = result.get("Result") if isinstance(result, dict) else None
        if isinstance(text, str):
            text = text.rsplit("description:", 1)[-1].strip().strip('"')
    else:
        prompt = prompt_template.replace("{{$name}}", product.name).replace("{{$tags}}", tags)
        result = generate("chat/completions", {"messages": [{"role": "user", "content": prompt}]})
        try:
            text = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            text = None
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(502, "The AI provider returned an empty product description.")
    return {"description": text.strip()}
