class LLMUnavailable(Exception):
    """Raised when the primary LLM provider fails after exhausted retries or network errors."""

    pass
