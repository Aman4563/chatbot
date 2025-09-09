"""LLM provider tools for agent capabilities."""

from typing import Dict, Any, List, Optional, AsyncIterator, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from .base import BaseTool
from providers.base import LLMProvider
from providers.openai_provider import OpenAIProvider
from providers.anthropic_provider import AnthropicProvider
from providers.google_provider import GoogleProvider
from providers.mistral_provider import MistralProvider


class LLMProviderTool(BaseTool):
    """Tool for LLM provider interactions."""
    
    def __init__(self, providers=None):
        super().__init__("llm_provider", "Generate responses using LLM providers")
        if providers:
            self.providers = providers
        else:
            # Fallback to creating providers without API keys
            self.providers = {
                "openai": OpenAIProvider(),
                "anthropic": AnthropicProvider(),
                "google": GoogleProvider(),
                "mistral": MistralProvider()
            }
        self.category = "llm"
    
    async def execute(
        self,
        messages: List[Dict[str, Any]],
        provider: str = "openai",
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 8192,
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncIterator[str]]:
        """Execute LLM generation."""
        if not await self.validate_input(messages=messages, provider=provider, model=model):
            raise ValueError("Invalid input parameters")
        
        provider_instance = self.providers.get(provider)
        if not provider_instance:
            raise ValueError(f"Unknown provider: {provider}")
        
        # Convert messages to LangChain format
        langchain_messages = self._convert_messages(messages)
        
        if stream:
            return await provider_instance.stream(
                langchain_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        else:
            return await provider_instance.generate(
                langchain_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
    
    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[BaseMessage]:
        """Convert message dictionaries to LangChain messages."""
        langchain_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
        
        return langchain_messages
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "messages": {
                    "type": "array",
                    "description": "List of messages for the conversation",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                            "content": {"type": "string"}
                        },
                        "required": ["role", "content"]
                    }
                },
                "provider": {
                    "type": "string",
                    "enum": ["openai", "anthropic", "google", "mistral"],
                    "description": "LLM provider to use",
                    "default": "openai"
                },
                "model": {
                    "type": "string",
                    "description": "Model name to use",
                    "default": "gpt-4o"
                },
                "temperature": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 2,
                    "description": "Sampling temperature",
                    "default": 0.7
                },
                "max_tokens": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 32768,
                    "description": "Maximum tokens to generate",
                    "default": 8192
                },
                "stream": {
                    "type": "boolean",
                    "description": "Whether to stream the response",
                    "default": False
                }
            },
            "required": ["messages", "provider", "model"]
        }
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.providers.keys())
    
    def get_available_models(self, provider: str) -> List[str]:
        """Get list of available models for a provider."""
        provider_instance = self.providers.get(provider)
        if provider_instance:
            return provider_instance.get_available_models()
        return []
    
    def get_provider_info(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get provider information."""
        provider_instance = self.providers.get(provider)
        if provider_instance:
            return provider_instance.get_provider_info()
        return None


class ConversationTool(BaseTool):
    """Tool for managing conversation context."""
    
    def __init__(self):
        super().__init__("conversation", "Manage conversation context and history")
        self.category = "conversation"
    
    async def execute(
        self,
        action: str,
        conversation_id: str,
        message: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute conversation management action."""
        if not await self.validate_input(action=action, conversation_id=conversation_id):
            raise ValueError("Invalid input parameters")
        
        if action == "add_message":
            return await self._add_message(conversation_id, message)
        elif action == "get_history":
            return await self._get_history(conversation_id)
        elif action == "clear_history":
            return await self._clear_history(conversation_id)
        elif action == "get_context":
            return await self._get_context(conversation_id)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _add_message(self, conversation_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Add a message to conversation history."""
        # This would integrate with a conversation store
        return {"status": "success", "message": "Message added"}
    
    async def _get_history(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation history."""
        # This would retrieve from a conversation store
        return {"status": "success", "history": []}
    
    async def _clear_history(self, conversation_id: str) -> Dict[str, Any]:
        """Clear conversation history."""
        # This would clear the conversation store
        return {"status": "success", "message": "History cleared"}
    
    async def _get_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation context."""
        # This would retrieve context from a conversation store
        return {"status": "success", "context": {}}
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add_message", "get_history", "clear_history", "get_context"],
                    "description": "Action to perform"
                },
                "conversation_id": {
                    "type": "string",
                    "description": "Conversation identifier"
                },
                "message": {
                    "type": "object",
                    "description": "Message to add (required for add_message action)",
                    "properties": {
                        "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                        "content": {"type": "string"},
                        "timestamp": {"type": "string"}
                    }
                }
            },
            "required": ["action", "conversation_id"]
        }


class ResponseSynthesisTool(BaseTool):
    """Tool for synthesizing responses from multiple sources with real-time data integration."""
    
    def __init__(self):
        super().__init__("response_synthesis", "Synthesize responses from multiple sources with real-time data")
        self.category = "synthesis"
        self.llm_provider = None  # Will be set by the agent
    
    def set_llm_provider(self, llm_provider):
        """Set the LLM provider for synthesis."""
        self.llm_provider = llm_provider
    
    async def execute(
        self,
        sources: List[Dict[str, Any]],
        synthesis_type: str = "combine",
        user_query: str = "",
        **kwargs
    ) -> str:
        """Execute response synthesis with real-time data integration."""
        if not await self.validate_input(sources=sources, synthesis_type=synthesis_type):
            raise ValueError("Invalid input parameters")
        
        if synthesis_type == "combine":
            return await self._combine_sources(sources)
        elif synthesis_type == "summarize":
            return await self._summarize_sources(sources, user_query)
        elif synthesis_type == "extract_key_points":
            return await self._extract_key_points(sources, user_query)
        elif synthesis_type == "real_time_response":
            return await self._generate_real_time_response(sources, user_query)
        else:
            raise ValueError(f"Unknown synthesis type: {synthesis_type}")
    
    async def _combine_sources(self, sources: List[Dict[str, Any]]) -> str:
        """Combine multiple sources into a single response."""
        combined = []
        for source in sources:
            content = source.get("content", "")
            if content:
                combined.append(content)
        return "\n\n".join(combined)
    
    async def _summarize_sources(self, sources: List[Dict[str, Any]], user_query: str = "") -> str:
        """Summarize multiple sources using LLM."""
        if not self.llm_provider or not sources:
            return "No sources available for summarization"
        
        # Prepare context from sources
        source_text = ""
        for i, source in enumerate(sources, 1):
            title = source.get("title", f"Source {i}")
            snippet = source.get("snippet", source.get("content", ""))
            url = source.get("url", "")
            
            source_text += f"Source {i}: {title}\n"
            source_text += f"Content: {snippet}\n"
            if url:
                source_text += f"URL: {url}\n"
            source_text += "\n"
        
        # Create synthesis prompt
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that synthesizes information from multiple sources to answer user questions. Always prioritize real-time, current information from the sources provided. If the sources contain current data, use that instead of your training data."
            },
            {
                "role": "user", 
                "content": f"User Question: {user_query}\n\nSources:\n{source_text}\n\nPlease provide a comprehensive answer based on the sources above. If the sources contain current/real-time information, use that data. Include relevant details and cite sources when appropriate."
            }
        ]
        
        try:
            response = await self.llm_provider.execute(
                messages=messages,
                provider="google",  # Use Gemini as per workspace rules
                model="gemini-2.0-flash",
                temperature=0.3,
                max_tokens=2048
            )
            return response
        except Exception as e:
            return f"Error synthesizing sources: {str(e)}"
    
    async def _extract_key_points(self, sources: List[Dict[str, Any]], user_query: str = "") -> str:
        """Extract key points from multiple sources using LLM."""
        if not self.llm_provider or not sources:
            return "No sources available for key point extraction"
        
        # Prepare context from sources
        source_text = ""
        for i, source in enumerate(sources, 1):
            title = source.get("title", f"Source {i}")
            snippet = source.get("snippet", source.get("content", ""))
            source_text += f"Source {i}: {title}\n{snippet}\n\n"
        
        # Create extraction prompt
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that extracts key points from sources to answer user questions. Focus on the most relevant and current information."
            },
            {
                "role": "user",
                "content": f"User Question: {user_query}\n\nSources:\n{source_text}\n\nExtract the key points that directly answer the user's question. Prioritize current/real-time information."
            }
        ]
        
        try:
            response = await self.llm_provider.execute(
                messages=messages,
                provider="google",
                model="gemini-2.0-flash", 
                temperature=0.3,
                max_tokens=1024
            )
            return response
        except Exception as e:
            return f"Error extracting key points: {str(e)}"
    
    async def _generate_real_time_response(self, sources: List[Dict[str, Any]], user_query: str = "") -> str:
        """Generate response prioritizing real-time data from sources."""
        if not sources:
            return "I don't have access to real-time information to answer your question. Please check reliable sources for current data."
        
        # Check if we have search results
        search_results = []
        for source in sources:
            if source.get("type") == "search_result" or "url" in source:
                search_results.append(source)
        
        if not search_results:
            return "I don't have current information to answer your question accurately."
        
        # Try to use LLM to generate response based on search results
        try:
            return await self._summarize_sources(search_results, user_query)
        except Exception as e:
            # If LLM synthesis fails, create a response from search results directly
            return self._create_fallback_response_from_sources(search_results, user_query)
    
    def _create_fallback_response_from_sources(self, sources: List[Dict[str, Any]], user_query: str = "") -> str:
        """Create a response directly from search results when LLM synthesis fails."""
        if not sources:
            return "I don't have current information to answer your question."
        
        # Extract the most relevant information from search results
        response_parts = []
        
        # Add a header based on the query type
        query_lower = user_query.lower()
        if "date" in query_lower and "time" in query_lower:
            response_parts.append("Based on current information:")
        elif "stock" in query_lower or "price" in query_lower:
            response_parts.append("Current stock information:")
        elif "when will" in query_lower or "release" in query_lower:
            response_parts.append("Release information:")
        else:
            response_parts.append("Based on current search results:")
        
        # Add the most relevant result
        if sources:
            best_result = sources[0]  # Take the first (most relevant) result
            title = best_result.get("title", "")
            snippet = best_result.get("snippet", "")
            url = best_result.get("url", "")
            
            if snippet:
                response_parts.append(f"\n{snippet}")
            
            if url and not url.startswith("https://example"):
                response_parts.append(f"\nSource: {url}")
        
        # Add additional relevant results if available
        if len(sources) > 1:
            response_parts.append("\n\nAdditional information:")
            for i, source in enumerate(sources[1:3], 1):  # Show up to 2 additional sources
                title = source.get("title", "")
                snippet = source.get("snippet", "")
                if snippet:
                    response_parts.append(f"\n• {snippet[:100]}...")
        
        return "".join(response_parts)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "sources": {
                    "type": "array",
                    "description": "List of sources to synthesize",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "title": {"type": "string"},
                            "snippet": {"type": "string"},
                            "url": {"type": "string"},
                            "source_type": {"type": "string"},
                            "metadata": {"type": "object"}
                        },
                        "required": ["content"]
                    }
                },
                "synthesis_type": {
                    "type": "string",
                    "enum": ["combine", "summarize", "extract_key_points", "real_time_response"],
                    "description": "Type of synthesis to perform",
                    "default": "combine"
                },
                "user_query": {
                    "type": "string",
                    "description": "The user's original query for context",
                    "default": ""
                }
            },
            "required": ["sources"]
        }
