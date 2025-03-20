import secrets
from typing import Any, Dict, Optional

# For Pydantic v2.x
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "E-commerce API"
    
    # SECURITY
    SECRET_KEY: str  # This default should be removed
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # DATABASE
    DATABASE_URL: Optional[str] = None
    
    # REDIS
    REDIS_URL: str = "redis://redis:6379/0"
    
    # STRIPE
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
