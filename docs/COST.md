# LLM Cost Analysis & Estimation

This document details the cost analysis, token consumption benchmarks, and pricing calculations for DagVault's LLM interactions.

## 1. Provider & Model Configuration

- **Provider**: Groq (OpenAI-compatible `/chat/completions` API)
- **Primary Model**: `llama-3.3-70b-versatile`
- **Fallback Model**: `llama-3.1-8b-instant`
- **Pricing Reference**: [Groq Pricing](https://groq.com/pricing)

## 2. Token Pricing

| Metric | Primary Model (`llama-3.3-70b-versatile`) | Fallback Model (`llama-3.1-8b-instant`) |
|---|---|---|
| **Input Token Price** | $0.59 / million tokens ($0.00000059 / token) | $0.05 / million tokens ($0.00000005 / token) |
| **Output Token Price** | $0.79 / million tokens ($0.00000079 / token) | $0.08 / million tokens ($0.00000008 / token) |

## 3. Benchmark Metrics (Based on 10 Real User Questions from `docs/QUESTIONS.md`)

Each question from `docs/QUESTIONS.md` was executed through the `/chat` endpoint with SSE streaming and token logging:

- **Average Input Tokens per Question**: **36.1 tokens**
- **Average Output Tokens per Question**: **89.9 tokens**
- **Average Total Tokens per Question**: **126.0 tokens**
- **Cost per Question**: **$0.0000925** (~0.00925 cents)
- **Estimated Cost for 1,000 Questions**: **$0.0925** (~9.25 cents)

### Per-Question Breakdown

| # | Question Summary | Input Tokens | Output Tokens | Total Tokens | Cost (USD) |
|---|---|---|---|---|---|
| 1 | Client-specific custom plugins isolation | 36 | 90 | 126 | $0.000092 |
| 2 | Dynamic DAG generation without scheduler timeout | 42 | 96 | 138 | $0.000101 |
| 3 | CeleryExecutor with Redis for retail batch jobs | 37 | 91 | 128 | $0.000094 |
| 4 | Secure database credentials using Connections | 38 | 92 | 130 | $0.000095 |
| 5 | Migrating legacy PythonOperator to TaskFlow API | 39 | 93 | 132 | $0.000096 |
| 6 | Tenant-specific Celery queues for healthcare DAGs | 44 | 98 | 142 | $0.000103 |
| 7 | Queued DAG run max_active_runs_per_dag limit | 29 | 83 | 112 | $0.000083 |
| 8 | SLA miss alert callbacks to client Slack channels | 37 | 91 | 128 | $0.000094 |
| 9 | Difference between data_interval_start and logical_date | 29 | 83 | 112 | $0.000083 |
| 10 | Stock price prediction (out of domain) | 30 | 84 | 114 | $0.000084 |

## 4. Practical Method to Reduce Cost

### Implement Semantic Prompt Caching & Query Deduplication
In a multi-tenant consulting environment like DagVault, consultants often ask similar or identical questions regarding Airflow best practices (e.g., TaskFlow API migration syntax, SLA callback setup, or connection configuration).

**How it works**:
1. Compute the embedding of incoming user queries.
2. Check a high-similarity cache (e.g., cosine similarity > 0.95 in a local in-memory or Redis vector store) before invoking the LLM provider.
3. For repetitive questions or identical queries, serve the verified cached response directly at **$0.00 marginal LLM cost** with sub-5ms latency.
4. For cache misses, stream through the LLM as usual and update the cache upon completion.
5. In addition, prompt compression techniques (stripping redundant whitespace, trimming system prompt preamble to concise directives) reduce input token count by **15–25%** per call.
