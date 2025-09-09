"""Settings and environment configuration for the agentic chat system."""

import os
from typing import Dict, Any, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = {"extra": "ignore"}
    
    # Application settings
    app_name: str = "Agentic Chat API"
    app_version: str = "4.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # API settings
    api_prefix: str = "/api/v1"
    max_request_size: int = Field(default=100 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 100MB
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")  # 5 minutes
    
    # LLM Provider settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    mistral_api_key: Optional[str] = Field(default=None, env="MISTRAL_API_KEY")
    huggingface_api_key: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    
    # Web Search API settings
    google_search_api_key: Optional[str] = Field(default=None, env="GOOGLE_SEARCH_API_KEY")
    google_search_engine_id: Optional[str] = Field(default=None, env="GOOGLE_SEARCH_ENGINE_ID")
    bing_search_api_key: Optional[str] = Field(default=None, env="BING_SEARCH_API_KEY")
    brave_search_api_key: Optional[str] = Field(default=None, env="BRAVE_SEARCH_API_KEY")
    
    # Default model settings
    default_model: str = Field(default="mistral-large", env="DEFAULT_MODEL")
    default_temperature: float = Field(default=0.7, env="DEFAULT_TEMPERATURE")
    default_max_tokens: int = Field(default=8192, env="DEFAULT_MAX_TOKENS")
    
    # Agent settings
    max_concurrent_agents: int = Field(default=10, env="MAX_CONCURRENT_AGENTS")
    agent_timeout: int = Field(default=60, env="AGENT_TIMEOUT")  # seconds
    enable_agent_collaboration: bool = Field(default=True, env="ENABLE_AGENT_COLLABORATION")
    
    # Tool settings
    enable_web_search: bool = Field(default=True, env="ENABLE_WEB_SEARCH")
    enable_image_generation: bool = Field(default=True, env="ENABLE_IMAGE_GENERATION")
    enable_document_processing: bool = Field(default=True, env="ENABLE_DOCUMENT_PROCESSING")
    enable_code_analysis: bool = Field(default=True, env="ENABLE_CODE_ANALYSIS")
    
    # Web search settings
    web_search_provider: str = Field(default="auto", env="WEB_SEARCH_PROVIDER")
    max_search_results: int = Field(default=10, env="MAX_SEARCH_RESULTS")
    search_timeout: int = Field(default=10, env="SEARCH_TIMEOUT")  # seconds
    
    # Image generation settings
    image_generation_provider: str = Field(default="openai", env="IMAGE_GENERATION_PROVIDER")
    max_images_per_request: int = Field(default=4, env="MAX_IMAGES_PER_REQUEST")
    image_generation_timeout: int = Field(default=30, env="IMAGE_GENERATION_TIMEOUT")  # seconds
    
    # File processing settings
    max_file_size: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    max_image_size: int = Field(default=10 * 1024 * 1024, env="MAX_IMAGE_SIZE")  # 10MB
    allowed_file_types: List[str] = Field(
        default=[
            "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp", "image/bmp", "image/tiff",
            "text/plain", "text/csv", "text/markdown", "text/xml",
            "application/json", "application/xml",
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/x-python", "application/javascript", "text/html", "text/css"
        ],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Memory and caching settings
    enable_memory: bool = Field(default=True, env="ENABLE_MEMORY")
    memory_backend: str = Field(default="sqlite", env="MEMORY_BACKEND")  # sqlite, redis, postgresql
    memory_ttl: int = Field(default=3600, env="MEMORY_TTL")  # 1 hour
    max_memory_size: int = Field(default=1000, env="MAX_MEMORY_SIZE")  # number of conversations
    
    # Redis settings (if using Redis for memory)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Database settings (if using database for memory)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    database_port: int = Field(default=5432, env="DATABASE_PORT")
    database_name: str = Field(default="agentic_chat", env="DATABASE_NAME")
    database_user: str = Field(default="postgres", env="DATABASE_USER")
    database_password: Optional[str] = Field(default=None, env="DATABASE_PASSWORD")
    
    # Security settings
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # Monitoring and logging
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    enable_health_checks: bool = Field(default=True, env="ENABLE_HEALTH_CHECKS")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")  # seconds
    
    # Development settings
    enable_hot_reload: bool = Field(default=False, env="ENABLE_HOT_RELOAD")
    enable_debug_toolbar: bool = Field(default=False, env="ENABLE_DEBUG_TOOLBAR")
    enable_api_docs: bool = Field(default=True, env="ENABLE_API_DOCS")
    


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def update_settings(**kwargs) -> None:
    """Update settings with new values."""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a specific provider."""
    key_map = {
        "openai": settings.openai_api_key,
        "anthropic": settings.anthropic_api_key,
        "google": settings.google_api_key,
        "mistral": settings.mistral_api_key,
        "huggingface": settings.huggingface_api_key,
    }
    return key_map.get(provider)


def is_provider_enabled(provider: str) -> bool:
    """Check if a provider is enabled (has API key)."""
    return get_api_key(provider) is not None


def get_enabled_providers() -> List[str]:
    """Get list of enabled providers."""
    return [
        provider for provider in ["openai", "anthropic", "google", "mistral", "huggingface"]
        if is_provider_enabled(provider)
    ]


def validate_settings() -> Dict[str, Any]:
    """Validate settings and return validation results."""
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "enabled_providers": get_enabled_providers(),
        "enabled_tools": [],
        "enabled_agents": []
    }
    
    # Check required settings
    if not settings.secret_key or settings.secret_key == "your-secret-key-here":
        validation_results["warnings"].append("Secret key is not set or using default value")
    
    # Check API keys
    if not get_enabled_providers():
        validation_results["errors"].append("No LLM providers are enabled (missing API keys)")
        validation_results["valid"] = False
    
    # Check tool settings
    if settings.enable_web_search:
        validation_results["enabled_tools"].append("web_search")
    
    if settings.enable_image_generation:
        validation_results["enabled_tools"].append("image_generation")
    
    if settings.enable_document_processing:
        validation_results["enabled_tools"].append("document_processing")
    
    if settings.enable_code_analysis:
        validation_results["enabled_tools"].append("code_analysis")
    
    # Check memory settings
    if settings.enable_memory and settings.memory_backend == "redis":
        if not settings.redis_url and not settings.redis_host:
            validation_results["warnings"].append("Redis memory backend enabled but Redis not configured")
    
    return validation_results


def get_environment_info() -> Dict[str, Any]:
    """Get environment information for debugging."""
    return {
        "python_version": os.sys.version,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug_mode": settings.debug,
        "log_level": settings.log_level,
        "enabled_providers": get_enabled_providers(),
        "memory_backend": settings.memory_backend,
        "database_configured": bool(settings.database_url),
        "redis_configured": bool(settings.redis_url or settings.redis_host),
    }
