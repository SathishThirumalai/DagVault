from collections.abc import Iterator

from app.cost import record_cost
from app.main import app, get_llm_provider


class MockChatProvider:
    def __init__(self):
        self.model = "mock-chat-model"
        self.last_input_tokens = 50
        self.last_output_tokens = 25
        self.last_model = "mock-chat-model"

    def stream(self, messages: list[dict[str, str]]) -> Iterator[str]:
        yield "Airflow "
        yield "DAGs are "
        yield "workflows."


def test_chat_endpoint_streams_sse_and_records_cost(client, test_cost_log):
    """Verify /chat returns SSE streaming response and logs cost upon completion."""
    app.dependency_overrides[get_llm_provider] = lambda: MockChatProvider()

    response = client.post("/chat", json={"message": "What is an Airflow DAG?"})
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    content = response.text
    assert "data: Airflow \n\n" in content
    assert "data: DAGs are \n\n" in content
    assert "data: workflows.\n\n" in content
    assert "data: [DONE]\n\n" in content

    # Verify cost log entry created
    with open(test_cost_log, encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 1
    assert "mock-chat-model" in lines[0]


def test_usage_endpoint_returns_grouped_daily_usage(client, test_cost_log):
    """Verify GET /usage groups calls and tokens per UTC day."""
    # Seed usage log with two distinct UTC days
    record_cost(
        model="mock-chat-model",
        input_tokens=100,
        output_tokens=50,
        price_input_per_million=1.0,
        price_output_per_million=2.0,
        provider="openai_compat",
        log_path=test_cost_log,
        timestamp="2026-11-01T12:00:00Z",
    )
    record_cost(
        model="mock-chat-model",
        input_tokens=200,
        output_tokens=100,
        price_input_per_million=1.0,
        price_output_per_million=2.0,
        provider="openai_compat",
        log_path=test_cost_log,
        timestamp="2026-11-02T15:00:00Z",
    )

    response = client.get("/usage")
    assert response.status_code == 200
    data = response.json()

    assert data["total_requests"] == 2
    assert data["total_input_tokens"] == 300
    assert data["total_output_tokens"] == 150
    assert data["total_tokens"] == 450

    daily = data["daily"]
    assert "2026-11-01" in daily
    assert daily["2026-11-01"]["requests"] == 1
    assert daily["2026-11-01"]["input_tokens"] == 100

    assert "2026-11-02" in daily
    assert daily["2026-11-02"]["requests"] == 1
    assert daily["2026-11-02"]["input_tokens"] == 200
