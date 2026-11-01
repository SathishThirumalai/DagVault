from pydantic import BaseModel, model_validator


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatRequest(BaseModel):
    message: str | None = None
    messages: list[ChatMessage] | None = None

    @model_validator(mode="after")
    def validate_content(self) -> "ChatRequest":
        if not self.message and not self.messages:
            raise ValueError("Either 'message' or 'messages' must be provided.")
        return self

    def get_messages(self) -> list[dict[str, str]]:
        if self.messages:
            return [{"role": m.role, "content": m.content} for m in self.messages]
        if self.message:
            return [{"role": "user", "content": self.message}]
        return []


class DailyUsage(BaseModel):
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


class UsageResponse(BaseModel):
    daily: dict[str, DailyUsage]
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
