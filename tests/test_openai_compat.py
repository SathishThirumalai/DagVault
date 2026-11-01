import json
from collections.abc import Iterator

import httpx
import pytest

from app.llm.exceptions import LLMUnavailable
from app.llm.openai_compat import OpenAICompatProvider


def test_provider_streaming_success_with_usage():
    """Verify streaming SSE parsing, stop on [DONE], and usage token recording."""
    sse_lines = [
        'data: {"id":"chat1","choices":[{"delta":{"content":"Hello"}}]}\n\n',
        'data: {"id":"chat1","choices":[{"delta":{"content":" world!"}}]}\n\n',
        (
            'data: {"id":"chat1","choices":[],'
            '"usage":{"prompt_tokens":15,"completion_tokens":8,"total_tokens":23}}\n\n'
        ),
        "data: [DONE]\n\n",
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        data = json.loads(request.content)
        assert data["model"] == "test-model"
        assert data["stream"] is True
        assert data["stream_options"] == {"include_usage": True}
        return httpx.Response(
            status_code=200,
            headers={"content-type": "text/event-stream"},
            content="".join(sse_lines).encode("utf-8"),
        )

    transport = httpx.MockTransport(handler)
    provider = OpenAICompatProvider(
        api_key="mock-key",
        base_url="https://api.mock.com/v1",
        model="test-model",
        transport=transport,
    )

    chunks = list(provider.stream([{"role": "user", "content": "Hi"}]))
    assert chunks == ["Hello", " world!"]
    assert provider.last_input_tokens == 15
    assert provider.last_output_tokens == 8


def test_retry_on_retryable_status_codes():
    """Verify safe retries with full jitter backoff on 429 and 500 status codes."""
    attempts = 0
    backoffs_recorded = []

    def sleep_recorder(seconds: float) -> None:
        backoffs_recorded.append(seconds)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(status_code=429)
        if attempts == 2:
            return httpx.Response(status_code=500)
        return httpx.Response(
            status_code=200,
            headers={"content-type": "text/event-stream"},
            content=b'data: {"choices":[{"delta":{"content":"OK"}}]}\n\ndata: [DONE]\n\n',
        )

    transport = httpx.MockTransport(handler)
    provider = OpenAICompatProvider(
        api_key="mock-key",
        transport=transport,
        sleep_fn=sleep_recorder,
        max_retries=3,
        backoff_base=0.5,
        backoff_cap=8.0,
    )

    chunks = list(provider.stream([{"role": "user", "content": "Hi"}]))
    assert chunks == ["OK"]
    assert attempts == 3  # 2 failed attempts + 1 success
    assert len(backoffs_recorded) == 2


def test_no_retry_on_non_retryable_status_codes():
    """Verify non-retryable 400/401/403/404 errors fail immediately with no retry."""
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(status_code=401, json={"error": "Unauthorized"})

    transport = httpx.MockTransport(handler)
    provider = OpenAICompatProvider(
        api_key="invalid-key",
        transport=transport,
        max_retries=3,
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        list(provider.stream([{"role": "user", "content": "Hi"}]))

    assert exc_info.value.response.status_code == 401
    assert attempts == 1  # Exactly 1 attempt, zero retries


def test_retries_exhausted_raises_llm_unavailable():
    """Verify retries are exhausted after max_retries and raise LLMUnavailable."""
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(status_code=503)

    transport = httpx.MockTransport(handler)
    provider = OpenAICompatProvider(
        api_key="mock-key",
        transport=transport,
        sleep_fn=lambda _: None,
        max_retries=3,
    )

    with pytest.raises(LLMUnavailable, match="LLM unavailable with status 503"):
        list(provider.stream([{"role": "user", "content": "Hi"}]))

    assert attempts == 4  # Initial attempt + 3 retries


def test_no_retry_after_streaming_starts():
    """Verify NEVER retrying if failure occurs after partial output has already been streamed."""
    attempts = 0

    class BrokenStream(Iterator[bytes]):
        def __init__(self):
            self.yielded = False

        def __iter__(self):
            return self

        def __next__(self):
            if not self.yielded:
                self.yielded = True
                return b'data: {"choices":[{"delta":{"content":"First chunk"}}]}\n\n'
            raise httpx.NetworkError("Connection lost mid-stream")

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            status_code=200,
            headers={"content-type": "text/event-stream"},
            content=BrokenStream(),
        )

    transport = httpx.MockTransport(handler)
    provider = OpenAICompatProvider(
        api_key="mock-key",
        transport=transport,
        sleep_fn=lambda _: None,
        max_retries=3,
    )

    stream_gen = provider.stream([{"role": "user", "content": "Hi"}])
    # First chunk yields successfully
    first_chunk = next(stream_gen)
    assert first_chunk == "First chunk"

    # Mid-stream error must raise LLMUnavailable without triggering a retry
    with pytest.raises(LLMUnavailable, match="Stream interrupted after partial output"):
        next(stream_gen)

    assert attempts == 1  # No second attempt allowed
