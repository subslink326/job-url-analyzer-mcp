"""Application configuration."""

from functools import lru_cache
from typing import List

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Server configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # Database configuration
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/job_analyzer.db",
        description="Database URL"
    )
    
    # CORS configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    # Crawler configuration
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, description="Max concurrent HTTP requests")
    REQUEST_TIMEOUT: int = Field(default=30, description="HTTP request timeout in seconds")
    CRAWL_DELAY: float = Field(default=1.0, description="Delay between requests in seconds")
    RESPECT_ROBOTS_TXT: bool = Field(default=True, description="Respect robots.txt")
    
    # Enrichment provider configuration
    ENABLE_CRUNCHBASE: bool = Field(default=False, description="Enable Crunchbase enrichment")
    CRUNCHBASE_API_KEY: str = Field(default="", description="Crunchbase API key")
    
    ENABLE_LINKEDIN: bool = Field(default=False, description="Enable LinkedIn enrichment")
    LINKEDIN_API_KEY: str = Field(default="", description="LinkedIn API key")
    
    # Data retention
    DATA_RETENTION_DAYS: int = Field(default=90, description="Data retention period in days")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()