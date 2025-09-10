import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str
    FINANCIAL_MODELING_PREP_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()