from collections.abc import Iterator
from typing import Annotated, Any

import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse

from app.config import Settings, get_settings
from app.cost import get_usage_summary, record_cost
from app.llm import FallbackProvider, LLMUnavailable, OpenAICompatProvider
from app.schemas import ChatRequest, UsageResponse

app = FastAPI(title="DagVault GenAI API", version="0.1.0")

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_llm_provider(settings: SettingsDep) -> Any:
    primary = OpenAICompatProvider(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )
    if settings.llm_fallback_model:
        fallback = OpenAICompatProvider(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_fallback_model,
        )
        return FallbackProvider(primary=primary, fallback=fallback)
    return primary


ProviderDep = Annotated[Any, Depends(get_llm_provider)]


@app.get("/health")
def health(settings: SettingsDep) -> dict:
    """Liveness: the process is up. Must be fast and must not call the LLM or the DB."""
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


@app.post("/chat")
def chat(
    request: ChatRequest,
    settings: SettingsDep,
    provider: ProviderDep,
) -> StreamingResponse:
    """Stream LLM assistant response using SSE and record cost & token usage."""
    messages = request.get_messages()
    stream_gen = provider.stream(messages)

    try:
        first_chunk = next(stream_gen)
    except StopIteration:
        first_chunk = None
    except LLMUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service temporarily unavailable: {exc}",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"LLM provider error: {exc}",
        ) from exc

    def event_stream() -> Iterator[str]:
        try:
            if first_chunk is not None:
                yield f"data: {first_chunk}\n\n"
            for chunk in stream_gen:
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        finally:
            input_tokens = getattr(provider, "last_input_tokens", 0)
            output_tokens = getattr(provider, "last_output_tokens", 0)
            model = getattr(provider, "last_model", getattr(provider, "model", settings.llm_model))
            record_cost(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                price_input_per_million=settings.price_input_per_million,
                price_output_per_million=settings.price_output_per_million,
                provider=settings.llm_provider,
                log_path=settings.cost_log_path,
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/usage", response_model=UsageResponse)
def usage(settings: SettingsDep) -> UsageResponse:
    """Read logs/cost.jsonl and provide grouped usage and cost information per UTC day."""
    summary_data = get_usage_summary(log_path=settings.cost_log_path)
    return UsageResponse(**summary_data)
