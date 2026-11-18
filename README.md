# AI service

Store Admin calls this FastAPI service through the product service. It generates descriptions with Chat Completions and product photos with the Images API. A generated photo is returned as a compact JPEG data URL so the product and its image fit in the catalog's 256 KiB request limit.

## Run locally

Run these commands from the repository root using Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp routers/.env.example .env
```

Edit the private `.env` file for your provider, then start the service.

```bash
uvicorn main:app --host 127.0.0.1 --port 5001
```

| Setting | Direct OpenAI | Azure OpenAI |
| --- | --- | --- |
| `USE_AZURE_OPENAI` | `False` | `True` |
| Text model | `OPENAI_GPT_MODEL_NAME` | `AZURE_OPENAI_GPT_DEPLOYMENT_NAME` |
| Image model | `OPENAI_IMAGE_MODEL` | `AZURE_OPENAI_DALLE_DEPLOYMENT_NAME` |
| Endpoint | Defaults to `https://api.openai.com/v1`. Override with `OPENAI_BASE_URL` for a compatible gateway. | Set `AZURE_OPENAI_GPT_ENDPOINT` and `AZURE_OPENAI_DALLE_ENDPOINT` to the respective resource endpoints. |
| Credentials | `OPENAI_GPT_API_KEY` and `OPENAI_DALLE_API_KEY` | Use the resource keys in those same fields, or set `USE_AZURE_AD=True` with an authorized Azure identity. |

The lab manifest selects the models for the Brightspace path. The existing image credential and Azure deployment field names are also used for GPT Image models. The service accepts the older direct model variable `OPENAI_DALLE_MODEL_NAME` if `OPENAI_IMAGE_MODEL` is unset.

Use `GET /health` to see which features are configured. Exercise the two generation routes with the [sample requests](./test-ai-service.http). A generation request checks model access. Run the image-response regression tests locally with `python -m unittest test_image_generator`.
