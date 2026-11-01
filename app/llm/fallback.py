from collections.abc import Iterator
from typing import Any

from app.llm.exceptions import LLMUnavailable


class FallbackProvider:
    """Wraps a primary and fallback LLM provider.

    Switches to fallback ONLY if primary raises LLMUnavailable before any text has streamed.
    """

    def __init__(self, primary: Any, fallback: Any):
        self.primary = primary
        self.fallback = fallback
        self.last_input_tokens: int = 0
        self.last_output_tokens: int = 0
        self.last_model: str = getattr(primary, "model", "")
        self.used_fallback: bool = False

    @property
    def model(self) -> str:
        if self.used_fallback:
            return getattr(self.fallback, "model", "")
        return getattr(self.primary, "model", "")

    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]:
        self.used_fallback = False
        has_streamed = False

        try:
            for chunk in self.primary.stream(messages, **kwargs):
                has_streamed = True
                yield chunk
            self.last_input_tokens = self.primary.last_input_tokens
            self.last_output_tokens = self.primary.last_output_tokens
            self.last_model = getattr(self.primary, "model", "")
        except LLMUnavailable as exc:
            if has_streamed:
                # Do NOT fallback after partial output has already been streamed
                raise exc

            # Primary unavailable before any text streamed: switch to fallback
            self.used_fallback = True
            for chunk in self.fallback.stream(messages, **kwargs):
                yield chunk
            self.last_input_tokens = self.fallback.last_input_tokens
            self.last_output_tokens = self.fallback.last_output_tokens
            self.last_model = getattr(self.fallback, "model", "")
