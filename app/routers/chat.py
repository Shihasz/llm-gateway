from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.cache import get_cached_response, make_cache_key, set_cached_response
from app.core.registry import get_provider, list_providers

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatRequest(BaseModel):
    prompt: str
    provider: str = "mock"
    model: str = "mock-model"


class ChatResponse(BaseModel):
    text: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cached: bool


@router.get("/providers")
def get_providers():
    return {"providers": list_providers()}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        provider = get_provider(request.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    cache_key = make_cache_key(request.provider, request.model, request.prompt)
    cached = get_cached_response(cache_key)
    if cached is not None:
        return ChatResponse(**cached, cached=True)

    result = await provider.complete(request.prompt, request.model)
    response_data = {
        "text": result.text,
        "provider": result.provider,
        "model": result.model,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    }
    set_cached_response(cache_key, response_data)

    return ChatResponse(**response_data, cached=False)
