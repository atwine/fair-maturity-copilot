from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All environment-driven config in one place. Nothing below should ever
    be hardcoded elsewhere — that's what keeps the LLM provider swap (Ollama
    dev <-> vLLM pilot) a config change, not a code change."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "llama3.1:8b"
    llm_api_key: str = "ollama"

    frontend_origin: str = "http://localhost:3000"


settings = Settings()
