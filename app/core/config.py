from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "llm-gateway"
    environment: str = "local"

    class Config:
        env_file = ".env"


settings = Settings()
