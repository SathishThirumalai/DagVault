import json
import random
import time
from collections.abc import Callable, Iterator
from typing import Any

import httpx

from app.llm.exceptions import LLMUnavailable
from app.token_utils import estimate_messages_tokens, estimate_tokens

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 404}


class OpenAICompatProvider:
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.groq.com/openai/v1",
        model: str = "llama-3.3-70b-versatile",
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        backoff_cap: float = 8.0,
        transport: httpx.BaseTransport | None = None,
        http_client: httpx.Client | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self.transport = transport
        self.http_client = http_client
        self.sleep_fn = sleep_fn

        self.last_input_tokens: int = 0
        self.last_output_tokens: int = 0

    def calculate_backoff(self, attempt: int) -> float:
        """Full-jitter exponential backoff: random.uniform(0, min(cap, base * (2 ** attempt)))."""
        exponential = self.backoff_base * (2**attempt)
        max_sleep = min(self.backoff_cap, exponential)
        return random.uniform(0, max_sleep)

    def _get_client(self) -> httpx.Client:
        if self.http_client is not None:
            return self.http_client
        return httpx.Client(transport=self.transport, timeout=self.timeout)

    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]:
        """Stream chat completions from OpenAI-compatible API with safe retries and usage tracking."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
            **kwargs,
        }

        self.last_input_tokens = 0
        self.last_output_tokens = 0
        accumulated_text: list[str] = []
        has_streamed = False
        attempt = 0

        owns_client = self.http_client is None
        client = self._get_client()

        try:
            while attempt <= self.max_retries:
                try:
                    request = client.build_request("POST", url, headers=headers, json=payload)
                    response = client.send(request, stream=True)
                except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as net_err:
                    if has_streamed:
                        # NEVER retry after text has already been sent to the client
                        raise LLMUnavailable(f"Network error after streaming started: {net_err}") from net_err
                    if attempt < self.max_retries:
                        backoff = self.calculate_backoff(attempt)
                        self.sleep_fn(backoff)
                        attempt += 1
                        continue
                    raise LLMUnavailable(
                        f"LLM unavailable after {attempt} retries due to network error: {net_err}"
                    ) from net_err

                # Check HTTP status codes before streaming response lines
                if response.status_code != 200:
                    status = response.status_code
                    response.close()

                    if status in NON_RETRYABLE_STATUS_CODES:
                        # Do NOT retry: 400, 401, 403, 404
                        response.raise_for_status()

                    if status in RETRYABLE_STATUS_CODES:
                        if attempt < self.max_retries:
                            backoff = self.calculate_backoff(attempt)
                            self.sleep_fn(backoff)
                            attempt += 1
                            continue
                        raise LLMUnavailable(f"LLM unavailable with status {status} after {attempt} retries.")

                    # Any other unexpected HTTP status
                    response.raise_for_status()

                # Status is 200 OK: stream SSE lines
                try:
                    for line in response.iter_lines():
                        line = line.strip()
                        if not line or line.startswith(":"):
                            continue

                        if line.startswith("data:"):
                            raw_data = line[5:].strip()
                            if raw_data == "[DONE]":
                                break

                            try:
                                data = json.loads(raw_data)
                            except json.JSONDecodeError:
                                continue

                            # Extract usage if returned in chunk
                            usage = data.get("usage")
                            if usage:
                                p_tokens = usage.get("prompt_tokens")
                                c_tokens = usage.get("completion_tokens")
                                if p_tokens is not None:
                                    self.last_input_tokens = p_tokens
                                if c_tokens is not None:
                                    self.last_output_tokens = c_tokens

                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    has_streamed = True
                                    accumulated_text.append(content)
                                    yield content
                    # Successfully completed stream
                    break

                except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as stream_err:
                    if has_streamed:
                        # NEVER retry after partial output has already been streamed
                        raise LLMUnavailable(
                            f"Stream interrupted after partial output: {stream_err}"
                        ) from stream_err
                    if attempt < self.max_retries:
                        backoff = self.calculate_backoff(attempt)
                        self.sleep_fn(backoff)
                        attempt += 1
                        continue
                    raise LLMUnavailable(
                        f"Stream failed before any content after {attempt} retries: {stream_err}"
                    ) from stream_err
                finally:
                    response.close()

            # If usage was not provided by provider, estimate tokens
            if self.last_input_tokens == 0:
                self.last_input_tokens = estimate_messages_tokens(messages)
            if self.last_output_tokens == 0 and accumulated_text:
                self.last_output_tokens = estimate_tokens("".join(accumulated_text))

        finally:
            if owns_client:
                client.close()
