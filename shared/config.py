from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/queue.db"
    OLLAMA_HOST: str = "http://ollama:11434"
    POLL_INTERVAL: float = 1.0
    GPU_POLL_INTERVAL: float = 2.0

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
