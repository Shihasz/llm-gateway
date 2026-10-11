from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "llm-gateway"
    environment: str = "local"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+psycopg2://gateway:gateway@localhost:5432/gateway"
    otlp_endpoint: str = "http://localhost:4318"

    class Config:
        env_file = ".env"


settings = Settings()
