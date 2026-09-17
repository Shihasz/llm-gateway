from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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


@router.get("/providers")
def get_providers():
    return {"providers": list_providers()}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        provider = get_provider(request.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    result = await provider.complete(request.prompt, request.model)
    return ChatResponse(
        text=result.text,
        provider=result.provider,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
