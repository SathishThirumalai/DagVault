from collections.abc import Iterator

import httpx
import pytest

from app.llm.exceptions import LLMUnavailable
from app.llm.fallback import FallbackProvider


class FakeLLMProvider:
    def __init__(
        self,
        model: str = "fake-model",
        chunks: list[str] | None = None,
        fail_with: Exception | None = None,
        fail_after_chunk: bool = False,
    ):
        self.model = model
        self.chunks = chunks or ["Hello from fake"]
        self.fail_with = fail_with
        self.fail_after_chunk = fail_after_chunk
        self.last_input_tokens = 10
        self.last_output_tokens = 20
        self.called = False

    def stream(self, messages: list[dict[str, str]], **kwargs) -> Iterator[str]:
        self.called = True
        if self.fail_with and not self.fail_after_chunk:
            raise self.fail_with
        for chunk in self.chunks:
            yield chunk
            if self.fail_with and self.fail_after_chunk:
                raise self.fail_with


def test_fallback_provider_switches_when_primary_unavailable():
    """Verify fallback activates when primary raises LLMUnavailable before streaming."""
    primary = FakeLLMProvider(
        model="primary-70b",
        fail_with=LLMUnavailable("Primary provider down"),
    )
    fallback = FakeLLMProvider(
        model="fallback-8b",
        chunks=["Fallback answer"],
    )

    provider = FallbackProvider(primary=primary, fallback=fallback)
    chunks = list(provider.stream([{"role": "user", "content": "Hi"}]))

    assert primary.called is True
    assert fallback.called is True
    assert provider.used_fallback is True
    assert chunks == ["Fallback answer"]
    assert provider.model == "fallback-8b"


def test_fallback_provider_no_fallback_on_non_retryable_error():
    """Verify fallback does NOT activate on 400/401/403/404 HTTP errors."""
    req = httpx.Request("POST", "https://api.test.com")
    resp = httpx.Response(status_code=401, request=req)
    http_error = httpx.HTTPStatusError("Unauthorized", request=req, response=resp)

    primary = FakeLLMProvider(model="primary-70b", fail_with=http_error)
    fallback = FakeLLMProvider(model="fallback-8b")

    provider = FallbackProvider(primary=primary, fallback=fallback)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        list(provider.stream([{"role": "user", "content": "Hi"}]))

    assert exc_info.value.response.status_code == 401
    assert fallback.called is False
    assert provider.used_fallback is False


def test_fallback_provider_no_fallback_after_streaming_starts():
    """Verify fallback does NOT activate after partial output has already streamed."""
    primary = FakeLLMProvider(
        model="primary-70b",
        chunks=["First part"],
        fail_with=LLMUnavailable("Primary died midway"),
        fail_after_chunk=True,
    )
    fallback = FakeLLMProvider(model="fallback-8b", chunks=["Should not be seen"])

    provider = FallbackProvider(primary=primary, fallback=fallback)
    stream_gen = provider.stream([{"role": "user", "content": "Hi"}])

    first = next(stream_gen)
    assert first == "First part"

    with pytest.raises(LLMUnavailable, match="Primary died midway"):
        next(stream_gen)

    assert fallback.called is False
    assert provider.used_fallback is False
