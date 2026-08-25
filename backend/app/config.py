from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All environment-driven config in one place. Nothing below should ever
    be hardcoded elsewhere — that's what keeps the LLM provider swap (vLLM
    <-> local Ollama fallback) a config change, not a code change."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Defaults to a local SQLite file so anything that doesn't actually touch
    # the DB (e.g. scripts/run_demo_assessment.py) can still import settings
    # without requiring a Postgres/Neon URL to be configured first. Real
    # environments set DATABASE_URL in .env.
    database_url: str = "sqlite:///./dev.db"

    # vLLM (dedicated A100 infra) is the default, not local Ollama — it's
    # both the actual production target and faster in practice than Ollama
    # on this hardware. Override in .env to fall back to Ollama offline.
    llm_base_url: str = "http://10.35.50.41:8000/v1"
    llm_model: str = "ibnzterrell/Meta-Llama-3.3-70B-Instruct-AWQ-INT4"
    llm_api_key: str = "not-needed"

    frontend_origin: str = "http://localhost:3000"


settings = Settings()
