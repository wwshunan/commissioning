from pydantic import BaseSettings

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"

settings = Settings()