"""Anthropic provider implementation for LLM integrations."""

import os
from typing import AsyncIterator, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from .optimized_provider import OptimizedLLMProvider


class AnthropicProvider(OptimizedLLMProvider):
    """Anthropic provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("anthropic", api_key or os.getenv("ANTHROPIC_API_KEY"))
        self._client = None
    
    async def _create_client(self) -> ChatAnthropic:
        """Create Anthropic client."""
        return ChatAnthropic(
            api_key=self.api_key,
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=8192
        )
    
    
    def supports_tools(self) -> bool:
        """Check if Anthropic supports tool calling."""
        return True
    
    def supports_vision(self) -> bool:
        """Check if Anthropic supports vision capabilities."""
        return True
    
    def get_available_models(self) -> List[str]:
        """Get list of available Anthropic models."""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific Anthropic model."""
        model_info = {
            "claude-3-5-sonnet-20241022": {
                "name": "Claude 3.5 Sonnet",
                "description": "Most advanced Claude model with excellent reasoning and vision",
                "max_tokens": 200000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.015
            },
            "claude-3-5-haiku-20241022": {
                "name": "Claude 3.5 Haiku",
                "description": "Fast and efficient Claude model",
                "max_tokens": 200000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.001
            },
            "claude-3-opus-20240229": {
                "name": "Claude 3 Opus",
                "description": "Most powerful Claude 3 model",
                "max_tokens": 200000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.075
            },
            "claude-3-sonnet-20240229": {
                "name": "Claude 3 Sonnet",
                "description": "Balanced Claude 3 model",
                "max_tokens": 200000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.015
            },
            "claude-3-haiku-20240307": {
                "name": "Claude 3 Haiku",
                "description": "Fast Claude 3 model",
                "max_tokens": 200000,
                "supports_vision": True,
                "supports_tools": True,
                "cost_per_1k_tokens": 0.001
            }
        }
        
        return model_info.get(model, {
            "name": model,
            "description": "Unknown Anthropic model",
            "max_tokens": 100000,
            "supports_vision": False,
            "supports_tools": False,
            "cost_per_1k_tokens": 0.01
        })
    
    async def validate_api_key(self) -> bool:
        """Validate the Anthropic API key."""
        try:
            if not self.api_key:
                return False
            
            # Try a simple test call
            test_messages = [HumanMessage(content="Hello")]
            await self.generate(test_messages, model="claude-3-haiku-20240307")
            return True
        except Exception:
            return False
