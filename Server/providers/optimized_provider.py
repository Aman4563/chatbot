"""Optimized provider base class with performance enhancements."""

import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncIterator, Union
from abc import ABC, abstractmethod
from langchain_core.messages import BaseMessage
from utils.performance_optimizer import (
    performance_monitor, cached_response, retry_with_backoff,
    get_connection_pool, get_response_cache
)
from utils.rate_limiter import api_rate_limiter


class OptimizedLLMProvider(ABC):
    """Optimized base class for LLM providers with performance enhancements."""
    
    def __init__(self, name: str, api_key: Optional[str] = None):
        self.name = name
        self.api_key = api_key
        self._client = None
        self._client_lock = asyncio.Lock()
        self.connection_pool = get_connection_pool()
        self.cache = get_response_cache()
        self._request_count = 0
        self._total_latency = 0.0
    
    @abstractmethod
    async def _create_client(self):
        """Create the LLM client."""
        pass
    
    async def _get_client(self):
        """Get or create client with connection pooling."""
        if self._client is None:
            async with self._client_lock:
                if self._client is None:  # Double-check locking
                    self._client = await self._create_client()
        return self._client
    
    @cached_response("llm_generation", ttl_seconds=1800)  # Cache for 30 minutes
    @performance_monitor("llm_generation")
    @retry_with_backoff(max_attempts=2, base_delay=2.0)  # Reduced retries to prevent quota exhaustion
    async def generate(
        self, 
        messages: List[BaseMessage], 
        model: str,
        **kwargs
    ) -> str:
        """Generate a response from the LLM with optimizations."""
        start_time = time.time()
        
        # Check rate limit
        if not api_rate_limiter.is_allowed(f"{self.name}_{model}"):
            remaining = api_rate_limiter.get_remaining_requests(f"{self.name}_{model}")
            reset_time = api_rate_limiter.get_reset_time(f"{self.name}_{model}")
            raise Exception(f"Rate limit exceeded for {self.name}. Remaining requests: {remaining}. Reset time: {reset_time}")
        
        try:
            # For providers that need model-specific clients, pass the model
            if hasattr(self, '_get_client') and 'model' in self._get_client.__code__.co_varnames:
                client = await self._get_client(model)
            else:
                client = await self._get_client()
                # Update client parameters if needed
                await self._update_client_params(client, model, **kwargs)
            
            # Generate response
            response = await client.ainvoke(messages)
            
            # Update performance metrics
            self._request_count += 1
            self._total_latency += time.time() - start_time
            
            return response.content
        
        except Exception as e:
            # Update error metrics
            self._request_count += 1
            self._total_latency += time.time() - start_time
            raise Exception(f"{self.name} generation error: {str(e)}")
    
    @performance_monitor("llm_streaming")
    async def stream(
        self, 
        messages: List[BaseMessage], 
        model: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream a response from the LLM with optimizations."""
        start_time = time.time()
        
        # Check rate limit
        if not api_rate_limiter.is_allowed(f"{self.name}_{model}"):
            remaining = api_rate_limiter.get_remaining_requests(f"{self.name}_{model}")
            reset_time = api_rate_limiter.get_reset_time(f"{self.name}_{model}")
            raise Exception(f"Rate limit exceeded for {self.name}. Remaining requests: {remaining}. Reset time: {reset_time}")
        
        try:
            # For providers that need model-specific clients, pass the model
            if hasattr(self, '_get_client') and 'model' in self._get_client.__code__.co_varnames:
                client = await self._get_client(model)
            else:
                client = await self._get_client()
                # Update client parameters if needed
                await self._update_client_params(client, model, **kwargs)
            
            # Stream response
            async for chunk in client.astream(messages):
                yield chunk.content
            
            # Update performance metrics
            self._request_count += 1
            self._total_latency += time.time() - start_time
        
        except Exception as e:
            # Update error metrics
            self._request_count += 1
            self._total_latency += time.time() - start_time
            raise Exception(f"{self.name} streaming error: {str(e)}")
    
    async def _update_client_params(self, client, model: str, **kwargs):
        """Update client parameters efficiently."""
        if hasattr(client, 'model') and client.model != model:
            client.model = model
        
        # Update other parameters only if they've changed
        for param, value in kwargs.items():
            if hasattr(client, param) and getattr(client, param) != value:
                setattr(client, param, value)
    
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
            # Skip actual API call to preserve quota - just check if key exists
            return bool(self.api_key and len(self.api_key) > 10)
        except Exception:
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information with performance metrics."""
        avg_latency = self._total_latency / max(self._request_count, 1)
        
        return {
            "name": self.name,
            "api_key_configured": bool(self.api_key),
            "request_count": self._request_count,
            "average_latency": avg_latency,
            "total_latency": self._total_latency,
            "supports_tools": self.supports_tools(),
            "supports_vision": self.supports_vision(),
            "available_models": self.get_available_models()
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get detailed performance statistics."""
        return {
            "provider": self.name,
            "total_requests": self._request_count,
            "total_latency": self._total_latency,
            "average_latency": self._total_latency / max(self._request_count, 1),
            "requests_per_second": self._request_count / max(self._total_latency, 0.001),
            "cache_stats": self.cache.get_stats()
        }
    
    async def warmup(self):
        """Warm up the provider by pre-creating connections."""
        try:
            # Only create client, don't make test API calls to preserve quota
            if hasattr(self, '_get_client') and 'model' in self._get_client.__code__.co_varnames:
                await self._get_client(self.get_available_models()[0])
            else:
                await self._get_client()
            # Skip test API call to avoid quota consumption
            # test_messages = [{"role": "user", "content": "test"}]
            # await self.generate(test_messages, self.get_available_models()[0])
        except Exception:
            pass  # Warmup failures shouldn't break the system
    
    async def cleanup(self):
        """Clean up provider resources."""
        if self._client and hasattr(self._client, 'close'):
            try:
                await self._client.close()
            except Exception:
                pass
        self._client = None


class OptimizedProviderRegistry:
    """Registry for optimized providers with performance tracking."""
    
    def __init__(self):
        self.providers: Dict[str, OptimizedLLMProvider] = {}
        self._registry_lock = asyncio.Lock()
    
    async def register_provider(self, provider: OptimizedLLMProvider):
        """Register a provider with warmup."""
        async with self._registry_lock:
            self.providers[provider.name] = provider
            # Warm up the provider
            await provider.warmup()
    
    def get_provider(self, name: str) -> Optional[OptimizedLLMProvider]:
        """Get a provider by name."""
        return self.providers.get(name)
    
    def get_all_providers(self) -> Dict[str, OptimizedLLMProvider]:
        """Get all registered providers."""
        return self.providers.copy()
    
    def get_all_provider_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all providers."""
        return {
            name: provider.get_provider_info()
            for name, provider in self.providers.items()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all providers."""
        total_requests = 0
        total_latency = 0.0
        provider_stats = {}
        
        for name, provider in self.providers.items():
            stats = provider.get_performance_stats()
            provider_stats[name] = stats
            total_requests += stats["total_requests"]
            total_latency += stats["total_latency"]
        
        return {
            "total_providers": len(self.providers),
            "total_requests": total_requests,
            "total_latency": total_latency,
            "average_latency": total_latency / max(total_requests, 1),
            "provider_stats": provider_stats
        }
    
    async def warmup_all_providers(self):
        """Warm up all registered providers."""
        warmup_tasks = []
        for provider in self.providers.values():
            if hasattr(provider, 'warmup') and callable(provider.warmup):
                warmup_tasks.append(provider.warmup())
        if warmup_tasks:
            await asyncio.gather(*warmup_tasks, return_exceptions=True)
    
    async def cleanup_all_providers(self):
        """Clean up all provider resources."""
        cleanup_tasks = []
        for provider in self.providers.values():
            if hasattr(provider, 'cleanup') and callable(provider.cleanup):
                cleanup_tasks.append(provider.cleanup())
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
