"""
Configuration management using Pydantic for type safety
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # API Keys
    openai_api_key: str
    anthropic_api_key: str

    # Email Services
    resend_api_key: Optional[str] = None
    sendgrid_api_key: Optional[str] = None

    # Data Sources
    apollo_api_key: Optional[str] = None
    hunter_api_key: Optional[str] = None

    # Social Media
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None

    # Payment
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    # Database
    database_url: str = "sqlite:///data/leads.db"

    # Monitoring
    sentry_dsn: Optional[str] = None
    log_level: str = "INFO"

    # Business Config
    company_name: str = "AI Services Agency"
    company_email: str = "hello@aiservices.com"
    company_website: str = "https://aiservices.com"

    # Pricing (in EUR)
    linkedin_package_price: int = 1200
    seo_content_price: int = 800
    email_sequence_price: int = 600
    twitter_management_price: int = 1500

    # Outreach Config
    daily_email_limit: int = 50
    min_personalization_score: int = 70
    followup_delay_days: int = 3

    # Quality Control
    content_quality_threshold: float = 0.85

    class Config:
        env_file = "config/.env"
        env_file_encoding = "utf-8"


# Singleton instance
settings = Settings()
