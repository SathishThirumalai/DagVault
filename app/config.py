from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "examate-rag"
    environment: str = "local"  # local | ci | production
    llm_provider: str = "openai_compat"
    llm_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    price_input_per_million: float = 0.0
    price_output_per_million: float = 0.0
    llm_fallback_model: str = ""
    cost_log_path: str = "logs/cost.jsonl"


@lru_cache
def get_settings() -> Settings:
    return Settings()
