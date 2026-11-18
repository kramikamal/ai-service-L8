"""Configuration and requests shared by the two OpenAI-backed routes."""

import os

import requests
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()


def enabled(name):
    return os.getenv(name, "").lower() == "true"


def model_settings(image=False):
    if enabled("USE_AZURE_OPENAI"):
        prefix = "AZURE_OPENAI_DALLE" if image else "AZURE_OPENAI_GPT"
        endpoint = os.getenv(f"{prefix}_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT", "")
        base = endpoint.rstrip("/")
        if base and not base.endswith("/openai/v1"):
            base += "/openai/v1"
        return base, os.getenv(f"{prefix}_DEPLOYMENT_NAME")

    if image:
        model = os.getenv("OPENAI_IMAGE_MODEL") or os.getenv("OPENAI_DALLE_MODEL_NAME", "gpt-image-2.6-flare")
    else:
        model = os.getenv("OPENAI_GPT_MODEL_NAME", "gpt-4o-mini")
    return os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"), model


def configured(image=False):
    base, model = model_settings(image)
    key = os.getenv("OPENAI_DALLE_API_KEY" if image else "OPENAI_GPT_API_KEY")
    identity = enabled("USE_AZURE_OPENAI") and enabled("USE_AZURE_AD")
    return bool(base and model and (key or identity))


def post_json(url, payload, headers=None):
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=(5, 150))
    except requests.Timeout as exc:
        raise HTTPException(504, "The AI provider timed out.") from exc
    except requests.RequestException as exc:
        raise HTTPException(502, "Could not connect to the AI provider.") from exc

    if not response.ok:
        messages = {
            400: "The AI provider rejected the request. Check the inputs and model settings.",
            401: "The AI provider rejected the credential.",
            403: "The credential does not have access to this model.",
            404: "The configured AI model or deployment was not found.",
            429: "The AI provider rate limit or quota was reached.",
        }
        raise HTTPException(response.status_code, messages.get(response.status_code, "The AI provider failed the request."))
    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(502, "The AI provider returned invalid JSON.") from exc


def generate(path, payload, *, image=False):
    if not configured(image):
        raise HTTPException(503, "Configure the AI endpoint, model, and credential for this feature.")
    base, model = model_settings(image)
    key = os.getenv("OPENAI_DALLE_API_KEY" if image else "OPENAI_GPT_API_KEY")
    if enabled("USE_AZURE_OPENAI") and enabled("USE_AZURE_AD"):
        from azure.identity import DefaultAzureCredential

        with DefaultAzureCredential() as credential:
            token = credential.get_token("https://cognitiveservices.azure.com/.default").token
        headers = {"Authorization": f"Bearer {token}"}
    elif enabled("USE_AZURE_OPENAI"):
        headers = {"api-key": key}
    else:
        headers = {"Authorization": f"Bearer {key}"}
        if os.getenv("OPENAI_ORG_ID"):
            headers["OpenAI-Organization"] = os.environ["OPENAI_ORG_ID"]
    return post_json(f"{base}/{path}", {"model": model, **payload}, headers)
