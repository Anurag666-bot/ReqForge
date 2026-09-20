"""
Configuration management for ReqForge.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings


class ScopeConfig(BaseSettings):
    """Scope validation configuration."""

    allowed_domains: List[str] = Field(default_factory=list)
    blocked_domains: List[str] = Field(default_factory=list)
    allow_subdomains: bool = True

    model_config = ConfigDict(env_prefix="REQFORGE_SCOPE_", extra="ignore")


class HTTPClientConfig(BaseSettings):
    """HTTP client configuration."""

    timeout: int = Field(default=30, description="Request timeout in seconds")
    retries: int = Field(default=3, description="Number of retry attempts")
    concurrency: int = Field(default=20, description="Maximum concurrent requests")
    backoff_factor: float = Field(default=0.5, description="Backoff factor for retries")
    user_agent: str = Field(default="ReqForge/0.1.0", description="User agent string")
    follow_redirects: bool = Field(default=True, description="Whether to follow redirects")
    max_redirects: int = Field(default=5, description="Maximum redirects to follow")
    verify_ssl: bool = Field(default=True, description="Whether to verify SSL certificates")
    proxy: Optional[str] = Field(default=None, description="HTTP proxy URL (e.g., http://127.0.0.1:8080)")

    model_config = ConfigDict(env_prefix="REQFORGE_HTTP_", extra="ignore")


class StorageConfig(BaseSettings):
    """Storage configuration."""

    database_url: str = Field(default="sqlite:///./reqforge.db", description="Database URL")
    echo: bool = Field(default=False, description="Echo SQL statements")

    model_config = ConfigDict(env_prefix="REQFORGE_STORAGE_", extra="ignore")


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    file: Optional[str] = Field(default=None, description="Log file path")

    model_config = ConfigDict(env_prefix="REQFORGE_LOG_", extra="ignore")


class ReqForgeConfig(BaseSettings):
    """Main ReqForge configuration."""

    scope: ScopeConfig = Field(default_factory=ScopeConfig)
    http: HTTPClientConfig = Field(default_factory=HTTPClientConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global config instance
config = ReqForgeConfig()


def load_config() -> ReqForgeConfig:
    """Load configuration from environment and .env file."""
    return ReqForgeConfig()


def get_config() -> ReqForgeConfig:
    """Get the global configuration instance."""
    return config