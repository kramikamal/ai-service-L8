from fastapi import FastAPI
from routers.description_generator import description
from routers.image_generator import image
from routers.LLM import configured, enabled
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(version=os.environ.get("APP_VERSION", "0.1.0"))
app.include_router(description)
app.include_router(image)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health", summary="check if server is healthy", operation_id="health")
async def get_health():
    """
    Returns status code 200
    """
    capabilities = []
    if enabled("USE_LOCAL_LLM") or configured():
        capabilities.append("description")
    if configured(image=True):
        capabilities.append("image")
    return {"status": "ok", "version": app.version, "capabilities": capabilities}
