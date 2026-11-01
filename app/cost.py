import json
import os
from datetime import UTC, datetime
from typing import Any


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    price_input_per_million: float,
    price_output_per_million: float,
) -> dict[str, float]:
    """Calculate token costs based on price per million tokens."""
    input_cost = (input_tokens / 1_000_000.0) * price_input_per_million
    output_cost = (output_tokens / 1_000_000.0) * price_output_per_million
    total_cost = input_cost + output_cost
    return {
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total_cost, 6),
    }


def record_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    price_input_per_million: float = 0.0,
    price_output_per_million: float = 0.0,
    provider: str = "openai_compat",
    log_path: str = "logs/cost.jsonl",
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Record LLM call metrics and cost into logs/cost.jsonl."""
    if timestamp is None:
        timestamp = datetime.now(UTC).isoformat()

    costs = calculate_cost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        price_input_per_million=price_input_per_million,
        price_output_per_million=price_output_per_million,
    )

    entry = {
        "timestamp": timestamp,
        "model": model,
        "provider": provider,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost": costs["input_cost"],
        "output_cost": costs["output_cost"],
        "total_cost": costs["total_cost"],
    }

    dir_path = os.path.dirname(os.path.abspath(log_path))
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def get_usage_summary(log_path: str = "logs/cost.jsonl") -> dict[str, Any]:
    """Read cost.jsonl and aggregate usage and costs grouped by UTC day."""
    summary: dict[str, Any] = {
        "daily": {},
        "total_requests": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
    }

    if not os.path.exists(log_path):
        return summary

    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = item.get("timestamp", "")
            # Extract UTC date (YYYY-MM-DD)
            day = ts[:10] if len(ts) >= 10 else "unknown"

            in_tok = int(item.get("input_tokens", 0))
            out_tok = int(item.get("output_tokens", 0))
            tot_tok = in_tok + out_tok
            cost = float(item.get("total_cost", 0.0))

            if day not in summary["daily"]:
                summary["daily"][day] = {
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                }

            day_data = summary["daily"][day]
            day_data["requests"] += 1
            day_data["input_tokens"] += in_tok
            day_data["output_tokens"] += out_tok
            day_data["total_tokens"] += tot_tok
            day_data["total_cost"] = round(day_data["total_cost"] + cost, 6)

            summary["total_requests"] += 1
            summary["total_input_tokens"] += in_tok
            summary["total_output_tokens"] += out_tok
            summary["total_tokens"] += tot_tok
            summary["total_cost"] = round(summary["total_cost"] + cost, 6)

    return summary
