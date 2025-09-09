"""Base provider class for LLM integrations."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage


class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, name: str, api_key: Optional[str] = None):
        self.name = name
        self.api_key = api_key
        self._client = None
    
    @abstractmethod
    async def generate(
        self, 
        messages: List[BaseMessage], 
        model: str,
        **kwargs
    ) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def stream(
        self, 
        messages: List[BaseMessage], 
        model: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream a response from the LLM."""
        pass
    
    @abstractmethod
    def supports_tools(self) -> bool:
        """Check if this provider supports tool calling."""
        pass
    
    @abstractmethod
    def supports_vision(self) -> bool:
        """Check if this provider supports vision capabilities."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider."""
        pass
    
    @abstractmethod
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        pass
    
    async def validate_api_key(self) -> bool:
        """Validate the API key for this provider."""
        try:
            # Try a simple test call
            test_messages = [{"role": "user", "content": "Hello"}]
            await self.generate(test_messages, self.get_available_models()[0])
            return True
        except Exception:
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "name": self.name,
            "supports_tools": self.supports_tools(),
            "supports_vision": self.supports_vision(),
            "available_models": self.get_available_models(),
            "api_key_configured": self.api_key is not None
        }


class ProviderRegistry:
    """Registry for managing LLM providers."""
    
    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
    
    def register_provider(self, provider: LLMProvider) -> None:
        """Register a provider in the registry."""
        self._providers[provider.name] = provider
    
    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get a provider by name."""
        return self._providers.get(name)
    
    def list_providers(self) -> List[str]:
        """List all registered provider names."""
        return list(self._providers.keys())
    
    def get_provider_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get provider information by name."""
        provider = self.get_provider(name)
        return provider.get_provider_info() if provider else None
    
    def get_all_provider_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information for all registered providers."""
        return {name: provider.get_provider_info() for name, provider in self._providers.items()}
    
    async def validate_all_providers(self) -> Dict[str, bool]:
        """Validate all registered providers."""
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.validate_api_key()
            except Exception:
                results[name] = False
        return results
