"""Google provider implementation for LLM integrations."""

import os
from typing import AsyncIterator, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from .optimized_provider import OptimizedLLMProvider


class GoogleProvider(OptimizedLLMProvider):
    """Google provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("google", api_key or os.getenv("GOOGLE_API_KEY"))
        self._client = None
    
    async def _create_client(self, model: str = "gemini-2.0-flash") -> ChatGoogleGenerativeAI:
        """Create Google client."""
        return ChatGoogleGenerativeAI(
            google_api_key=self.api_key,
            model=model,
            temperature=0.7,
            max_output_tokens=8192
        )
    
    async def _get_client(self, model: str = "gemini-2.0-flash"):
        """Get or create client with the specified model."""
        # For Google, we need to create a new client for each model
        return await self._create_client(model)
    
    
    def supports_tools(self) -> bool:
        """Check if Google supports tool calling."""
        return True
    
    def supports_vision(self) -> bool:
        """Check if Google supports vision capabilities."""
        return True
    
    def get_available_models(self) -> List[str]:
        """Get list of available Google models."""
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash-exp"
        ]
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific Google model."""
        model_info = {
            "gemini-1.5-pro": {
                "name": "Gemini 1.5 Pro",
                "description": "Advanced Gemini model with large context window",
                "max_tokens": 2000000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.001
            },
            "gemini-1.5-flash": {
                "name": "Gemini 1.5 Flash",
                "description": "Fast and efficient Gemini model",
                "max_tokens": 1000000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.0005
            },
            "gemini-2.0-flash": {
                "name": "Gemini 2.0 Flash",
                "description": "Latest fast Gemini model",
                "max_tokens": 1000000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.0005
            },
            "gemini-2.5-flash": {
                "name": "Gemini 2.5 Flash",
                "description": "Enhanced fast Gemini model",
                "max_tokens": 1000000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.0005
            },
            "gemini-2.5-pro": {
                "name": "Gemini 2.5 Pro",
                "description": "Most advanced Gemini model",
                "max_tokens": 2000000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.001
            },
            "gemini-2.0-flash-exp": {
                "name": "Gemini 2.0 Flash Experimental",
                "description": "Experimental Gemini 2.0 Flash model",
                "max_tokens": 1000000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.0005
            }
        }
        
        return model_info.get(model, {
            "name": model,
            "description": "Unknown Google model",
            "max_tokens": 1000000,
            "supports_vision": False,
            "supports_tools": False,
            "cost_per_1k_tokens": 0.001
        })
    
    async def validate_api_key(self) -> bool:
        """Validate the Google API key."""
        try:
            if not self.api_key:
                return False
            
            # Skip actual API call to preserve quota - just check if key exists
            return bool(self.api_key and len(self.api_key) > 10)
        except Exception:
            return False
