from pathlib import Path

from app.cost import calculate_cost, get_usage_summary, record_cost


def test_cost_calculation():
    """Verify input, output, and total cost calculations per million tokens."""
    # Zero pricing
    free_costs = calculate_cost(
        input_tokens=1000,
        output_tokens=500,
        price_input_per_million=0.0,
        price_output_per_million=0.0,
    )
    assert free_costs["input_cost"] == 0.0
    assert free_costs["output_cost"] == 0.0
    assert free_costs["total_cost"] == 0.0

    # Paid model pricing: e.g. Llama 3.3 70B ($0.59 / $0.79 per MTok)
    paid_costs = calculate_cost(
        input_tokens=100_000,
        output_tokens=50_000,
        price_input_per_million=0.59,
        price_output_per_million=0.79,
    )
    # 100,000 / 1,000,000 * 0.59 = 0.059
    # 50,000 / 1,000,000 * 0.79 = 0.0395
    # total = 0.0985
    assert paid_costs["input_cost"] == 0.059
    assert paid_costs["output_cost"] == 0.0395
    assert paid_costs["total_cost"] == 0.0985


def test_record_cost_and_usage_summary(tmp_path: Path):
    """Verify JSONL cost record writing, directory creation, and UTC day aggregation."""
    log_file = tmp_path / "sub_dir" / "cost.jsonl"
    log_path_str = str(log_file)

    # Empty summary when file doesn't exist
    empty_summary = get_usage_summary(log_path=log_path_str)
    assert empty_summary["total_requests"] == 0
    assert empty_summary["daily"] == {}

    # Record two calls on Day 1
    record_cost(
        model="llama-3.3-70b-versatile",
        input_tokens=1000,
        output_tokens=200,
        price_input_per_million=1.0,
        price_output_per_million=2.0,
        provider="openai_compat",
        log_path=log_path_str,
        timestamp="2026-11-01T10:00:00Z",
    )
    record_cost(
        model="llama-3.3-70b-versatile",
        input_tokens=500,
        output_tokens=100,
        price_input_per_million=1.0,
        price_output_per_million=2.0,
        provider="openai_compat",
        log_path=log_path_str,
        timestamp="2026-11-01T14:30:00Z",
    )

    # Record one call on Day 2
    record_cost(
        model="llama-3.3-70b-versatile",
        input_tokens=2000,
        output_tokens=400,
        price_input_per_million=1.0,
        price_output_per_million=2.0,
        provider="openai_compat",
        log_path=log_path_str,
        timestamp="2026-11-02T08:00:00Z",
    )

    # File should exist now
    assert log_file.exists()

    summary = get_usage_summary(log_path=log_path_str)
    assert summary["total_requests"] == 3
    assert summary["total_input_tokens"] == 3500
    assert summary["total_output_tokens"] == 700
    assert summary["total_tokens"] == 4200

    # Grouped by day
    assert "2026-11-01" in summary["daily"]
    day1 = summary["daily"]["2026-11-01"]
    assert day1["requests"] == 2
    assert day1["input_tokens"] == 1500
    assert day1["output_tokens"] == 300
    assert day1["total_tokens"] == 1800

    assert "2026-11-02" in summary["daily"]
    day2 = summary["daily"]["2026-11-02"]
    assert day2["requests"] == 1
    assert day2["input_tokens"] == 2000
    assert day2["output_tokens"] == 400
    assert day2["total_tokens"] == 2400
