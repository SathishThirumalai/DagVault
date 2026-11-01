import pytest

from app.schemas import ChatMessage, ChatRequest, DailyUsage, UsageResponse


def test_chat_request_and_message_schemas():
    """Verify ChatMessage and ChatRequest validation and normalization."""
    # ChatMessage validation
    msg = ChatMessage(role="user", content="Hello world")
    assert msg.role == "user"
    assert msg.content == "Hello world"

    # ChatRequest from string message
    req_single = ChatRequest(message="What is Airflow?")
    messages = req_single.get_messages()
    assert len(messages) == 1
    assert messages[0] == {"role": "user", "content": "What is Airflow?"}

    # ChatRequest from message list
    req_multi = ChatRequest(
        messages=[
            ChatMessage(role="system", content="You are an Airflow expert"),
            ChatMessage(role="user", content="Explain DAGs"),
        ]
    )
    assert len(req_multi.get_messages()) == 2
    assert req_multi.get_messages()[0]["role"] == "system"

    # ChatRequest validation error when both empty
    with pytest.raises(ValueError, match="Either 'message' or 'messages' must be provided"):
        ChatRequest()

    # DailyUsage & UsageResponse validation
    daily = DailyUsage(requests=2, input_tokens=100, output_tokens=50, total_tokens=150, total_cost=0.001)
    resp = UsageResponse(
        daily={"2026-11-01": daily},
        total_requests=2,
        total_input_tokens=100,
        total_output_tokens=50,
        total_tokens=150,
        total_cost=0.001,
    )
    assert resp.total_requests == 2
    assert resp.daily["2026-11-01"].total_tokens == 150
