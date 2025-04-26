import secrets
from typing import Any, Dict, Optional

# For Pydantic v2.x
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "E-commerce API"
    
    # SECURITY
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # DATABASE
    DATABASE_URL: Optional[str] = None
    
    # REDIS
    REDIS_URL: str = "redis://redis:6379/0"
    
    # STRIPE
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # EMAIL
    EMAIL_ENABLED: bool = False
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 1025  # Default for MailHog
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: str = "noreply@example.com"
    
    # CORS
    CORS_ORIGINS: Optional[str] = None
    
    # ENVIRONMENT
    ENVIRONMENT: str = "development"
    
    # LOGGING
    LOG_LEVEL: str = "INFO"
    
    # RATE LIMITING
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_LOGIN: str = "10/minute"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
