def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a string using ~4 chars per token rule of thumb."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def estimate_messages_tokens(messages: list[dict[str, str]]) -> int:
    """Estimate token count for a list of chat messages including per-message framing overhead."""
    total = 3  # Conversation start overhead
    for msg in messages:
        content = msg.get("content", "")
        role = msg.get("role", "")
        total += 4 + estimate_tokens(content) + estimate_tokens(role)
    return total
