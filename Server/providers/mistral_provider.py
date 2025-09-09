"""Mistral provider implementation for LLM integrations."""

import os
from typing import AsyncIterator, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_mistralai import ChatMistralAI
from .optimized_provider import OptimizedLLMProvider


class MistralProvider(OptimizedLLMProvider):
    """Mistral provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("mistral", api_key or os.getenv("MISTRAL_API_KEY"))
        self._client = None
    
    async def _create_client(self) -> ChatMistralAI:
        """Create Mistral client."""
        return ChatMistralAI(
            api_key=self.api_key,
            model="mistral-large-latest",
            temperature=0.7,
            max_tokens=8192
        )
    
    
    def supports_tools(self) -> bool:
        """Check if Mistral supports tool calling."""
        return True
    
    def supports_vision(self) -> bool:
        """Check if Mistral supports vision capabilities."""
        return False  # Mistral models don't support vision yet
    
    def get_available_models(self) -> List[str]:
        """Get list of available Mistral models."""
        return [
            "mistral-large-latest",
            "mistral-small-latest",
            "mistral-nemo-latest",
            "mistral-7b-instruct",
            "mistral-8x7b-instruct"
        ]
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific Mistral model."""
        model_info = {
            "mistral-large-latest": {
                "name": "Mistral Large",
                "description": "Most advanced Mistral model with excellent reasoning",
                "max_tokens": 32768,
                "supports_vision": False,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.002
            },
            "mistral-small-latest": {
                "name": "Mistral Small",
                "description": "Efficient Mistral model for general tasks",
                "max_tokens": 32768,
                "supports_vision": False,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.001
            },
            "mistral-nemo-latest": {
                "name": "Mistral Nemo",
                "description": "Fast and lightweight Mistral model",
                "max_tokens": 32768,
                "supports_vision": False,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.0005
            },
            "mistral-7b-instruct": {
                "name": "Mistral 7B Instruct",
                "description": "7B parameter Mistral model",
                "max_tokens": 32768,
                "supports_vision": False,
                "supports_tools": False,
                "cost_per_1k_tokens": 0.0005
            },
            "mistral-8x7b-instruct": {
                "name": "Mistral 8x7B Instruct",
                "description": "Mixture of experts Mistral model",
                "max_tokens": 32768,
                "supports_vision": False,
                "supports_tools": False,
                "cost_per_1k_tokens": 0.0005
            }
        }
        
        return model_info.get(model, {
            "name": model,
            "description": "Unknown Mistral model",
            "max_tokens": 32768,
            "supports_vision": False,
            "supports_tools": False,
            "cost_per_1k_tokens": 0.001
        })
    
    async def validate_api_key(self) -> bool:
        """Validate the Mistral API key."""
        try:
            if not self.api_key:
                return False
            
            # Try a simple test call
            test_messages = [HumanMessage(content="Hello")]
            await self.generate(test_messages, model="mistral-small-latest")
            return True
        except Exception:
            return False
