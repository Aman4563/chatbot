"""OpenAI provider implementation for LLM integrations."""

import os
from typing import AsyncIterator, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from .optimized_provider import OptimizedLLMProvider


class OpenAIProvider(OptimizedLLMProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("openai", api_key or os.getenv("OPENAI_API_KEY"))
        self._client = None
    
    async def _create_client(self) -> ChatOpenAI:
        """Create OpenAI client."""
        return ChatOpenAI(
            api_key=self.api_key,
            model="gpt-4o",
            temperature=0.7,
            max_tokens=8192,
            streaming=True
        )
    
    
    def supports_tools(self) -> bool:
        """Check if OpenAI supports tool calling."""
        return True
    
    def supports_vision(self) -> bool:
        """Check if OpenAI supports vision capabilities."""
        return True
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ]
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific OpenAI model."""
        model_info = {
            "gpt-4o": {
                "name": "GPT-4o",
                "description": "Most advanced GPT-4 model with vision capabilities",
                "max_tokens": 128000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.03
            },
            "gpt-4o-mini": {
                "name": "GPT-4o Mini",
                "description": "Faster and more cost-effective GPT-4 model",
                "max_tokens": 128000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.015
            },
            "gpt-4-turbo": {
                "name": "GPT-4 Turbo",
                "description": "High-performance GPT-4 model",
                "max_tokens": 128000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.01
            },
            "gpt-4": {
                "name": "GPT-4",
                "description": "Standard GPT-4 model",
                "max_tokens": 8192,
                "supports_vision": False,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.03
            },
            "gpt-3.5-turbo": {
                "name": "GPT-3.5 Turbo",
                "description": "Fast and efficient GPT-3.5 model",
                "max_tokens": 16384,
                "supports_vision": False,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.002
            }
        }
        
        return model_info.get(model, {
            "name": model,
            "description": "Unknown OpenAI model",
            "max_tokens": 4096,
            "supports_vision": False,
            "supports_tools": False,
            "cost_per_1k_tokens": 0.01
        })
    
    async def validate_api_key(self) -> bool:
        """Validate the OpenAI API key."""
        try:
            if not self.api_key:
                return False
            
            # Try a simple test call
            test_messages = [HumanMessage(content="Hello")]
            await self.generate(test_messages, model="gpt-3.5-turbo")
            return True
        except Exception:
            return False
