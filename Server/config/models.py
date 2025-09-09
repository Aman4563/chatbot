"""Model configurations for LLM providers."""

import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Environment keys
ENV_KEYS = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
    "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY"),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    "HUGGINGFACE_API_KEY": os.getenv("HUGGINGFACE_API_KEY"),
}

# Model configurations
MODEL_CONFIG: Dict[str, Dict[str, Any]] = {
    "mistral-large": {
        "provider": "mistral",
        "class": "ChatMistralAI",
        "model": "mistral-large-latest",
        "supports_vision": False,
        "supports_files": True,
        "supports_tools": True,
        "max_tokens": 8192,
        "temperature": 0.7,
        "api_key": ENV_KEYS["MISTRAL_API_KEY"],
        "cost_per_1k_tokens": 0.002,
    },
    "mistral-small": {
        "provider": "mistral",
        "class": "ChatMistralAI",
        "model": "mistral-small-latest",
        "supports_vision": False,
        "supports_files": True,
        "supports_tools": True,
        "max_tokens": 8192,
        "temperature": 0.7,
        "api_key": ENV_KEYS["MISTRAL_API_KEY"],
        "cost_per_1k_tokens": 0.001,
    },
    "gpt-4o": {
        "provider": "openai",
        "class": "ChatOpenAI",
        "model": "gpt-4o",
        "supports_vision": True,
        "supports_files": True,
        "supports_tools": True,
        "max_tokens": 8192,
        "temperature": 0.7,
        "api_key": ENV_KEYS["OPENAI_API_KEY"],
        "cost_per_1k_tokens": 0.03,
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "class": "ChatOpenAI",
        "model": "gpt-4o-mini",
        "supports_vision": True,
        "supports_files": True,
        "supports_tools": True,
        "max_tokens": 8192,
        "temperature": 0.7,
        "api_key": ENV_KEYS["OPENAI_API_KEY"],
        "cost_per_1k_tokens": 0.015,
    },
    "claude-3-5-sonnet": {
        "provider": "anthropic",
        "class": "ChatAnthropic",
        "model": "claude-3-5-sonnet-20241022",
        "supports_vision": True,
        "supports_files": True,
        "supports_tools": True,
        "max_tokens": 8192,
        "temperature": 0.7,
        "api_key": ENV_KEYS["ANTHROPIC_API_KEY"],
        "cost_per_1k_tokens": 0.015,
    },
    "gemini-1.5-pro": {
        "provider": "google",
        "class": "ChatGoogleGenerativeAI",
        "model": "gemini-1.5-pro",
        "supports_vision": True,
        "supports_files": True,
        "supports_tools": True,
        "max_tokens": 8192,
        "temperature": 0.7,
        "api_key": ENV_KEYS["GOOGLE_API_KEY"],
        "cost_per_1k_tokens": 0.001,
    },
    "gemini-1.5-flash": {
        "provider": "google",
        "class": "ChatGoogleGenerativeAI",
        "model": "gemini-1.5-flash",
        "supports_vision": True,
        "supports_files": True,
        "supports_tools": True,
        "max_tokens": 8192,
        "temperature": 0.7,
        "api_key": ENV_KEYS["GOOGLE_API_KEY"],
        "cost_per_1k_tokens": 0.0005,
    },
    "gemini-2.0-flash": {
        "provider": "google",
        "class": "ChatGoogleGenerativeAI",
        "model": "gemini-2.0-flash",
        "supports_vision": True,
        "supports_files": True,
        "supports_tools": True,
        "max_tokens": 8192,
        "temperature": 0.7,
        "api_key": ENV_KEYS["GOOGLE_API_KEY"],
        "cost_per_1k_tokens": 0.0005,
    },
    "gemini-2.5-flash": {
        "provider": "google",
        "class": "ChatGoogleGenerativeAI",
        "model": "gemini-2.5-flash",
        "supports_vision": True,
        "supports_files": True,
        "supports_tools": True,
        "max_tokens": 8192,
        "temperature": 0.7,
        "api_key": ENV_KEYS["GOOGLE_API_KEY"],
        "cost_per_1k_tokens": 0.0005,
    },
    "gemini-2.5-pro": {
        "provider": "google",
        "class": "ChatGoogleGenerativeAI",
        "model": "gemini-2.5-pro",
        "supports_vision": True,
        "supports_files": True,
        "supports_tools": True,
        "max_tokens": 8192,
        "temperature": 0.7,
        "api_key": ENV_KEYS["GOOGLE_API_KEY"],
        "cost_per_1k_tokens": 0.001,
    },
    "gemini-2.0-flash-exp": {
        "provider": "google",
        "class": "ChatGoogleGenerativeAI",
        "model": "gemini-2.0-flash-exp",
        "supports_vision": True,
        "supports_files": True,
        "supports_tools": True,
        "max_tokens": 8192,
        "temperature": 0.7,
        "api_key": ENV_KEYS["GOOGLE_API_KEY"],
        "cost_per_1k_tokens": 0.0005,
    },
}

# Provider configurations
PROVIDER_CONFIG: Dict[str, Dict[str, Any]] = {
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "supports_streaming": True,
        "supports_tools": True,
        "supports_vision": True,
        "rate_limit": 1000,  # requests per minute
    },
    "anthropic": {
        "name": "Anthropic",
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-3-5-sonnet-20241022",
        "supports_streaming": True,
        "supports_tools": True,
        "supports_vision": True,
        "rate_limit": 1000,
    },
    "google": {
        "name": "Google",
        "base_url": "https://generativelanguage.googleapis.com",
        "default_model": "gemini-1.5-pro",
        "supports_streaming": True,
        "supports_tools": True,
        "supports_vision": True,
        "rate_limit": 1000,
    },
    "mistral": {
        "name": "Mistral",
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "mistral-large-latest",
        "supports_streaming": True,
        "supports_tools": True,
        "supports_vision": False,
        "rate_limit": 1000,
    },
}

# Tool configurations
TOOL_CONFIG: Dict[str, Dict[str, Any]] = {
    "web_search": {
        "name": "Web Search",
        "description": "Search the web for current information",
        "provider": "google",
        "enabled": True,
        "max_results": 10,
        "rate_limit": 100,  # requests per minute
    },
    "image_generation": {
        "name": "Image Generation",
        "description": "Generate images from text prompts",
        "provider": "openai",
        "enabled": True,
        "max_images": 4,
        "rate_limit": 50,  # requests per minute
    },
    "document_processing": {
        "name": "Document Processing",
        "description": "Process and analyze documents",
        "provider": "local",
        "enabled": True,
        "max_file_size": 50 * 1024 * 1024,  # 50MB
        "supported_formats": [
            "pdf", "docx", "txt", "csv", "json", "xml", "md"
        ],
    },
    "code_analysis": {
        "name": "Code Analysis",
        "description": "Analyze and explain code",
        "provider": "local",
        "enabled": True,
        "supported_languages": [
            "python", "javascript", "typescript", "java", "cpp", "go", "rust"
        ],
    },
}


def get_model_config(model_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific model."""
    return MODEL_CONFIG.get(model_name)


def get_provider_config(provider_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific provider."""
    return PROVIDER_CONFIG.get(provider_name)


def get_tool_config(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific tool."""
    return TOOL_CONFIG.get(tool_name)


def get_available_models() -> List[str]:
    """Get list of all available model names."""
    return list(MODEL_CONFIG.keys())


def get_available_providers() -> List[str]:
    """Get list of all available provider names."""
    return list(PROVIDER_CONFIG.keys())


def get_available_tools() -> List[str]:
    """Get list of all available tool names."""
    return list(TOOL_CONFIG.keys())


def get_models_by_provider(provider: str) -> List[str]:
    """Get list of models for a specific provider."""
    return [
        model_name for model_name, config in MODEL_CONFIG.items()
        if config["provider"] == provider
    ]


def get_models_with_capability(capability: str) -> List[str]:
    """Get list of models that support a specific capability."""
    capability_map = {
        "vision": "supports_vision",
        "files": "supports_files",
        "tools": "supports_tools",
    }
    
    if capability not in capability_map:
        return []
    
    return [
        model_name for model_name, config in MODEL_CONFIG.items()
        if config.get(capability_map[capability], False)
    ]


def validate_model_config(model_name: str) -> bool:
    """Validate that a model configuration is complete."""
    config = get_model_config(model_name)
    if not config:
        return False
    
    required_fields = [
        "provider", "class", "model", "supports_vision", 
        "supports_files", "supports_tools", "api_key"
    ]
    
    return all(field in config for field in required_fields)


def get_default_model() -> str:
    """Get the default model name."""
    return "mistral-large"


def get_fallback_models() -> List[str]:
    """Get list of fallback models in order of preference."""
    return [
        "mistral-large",
        "gpt-4o-mini",
        "gemini-1.5-flash",
        "claude-3-5-sonnet"
    ]
