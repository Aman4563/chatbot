"""Response schemas for the agentic chat system."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """Chat response with optional error information."""
    response: str = Field(..., description="The generated response")
    error: Optional[str] = Field(default=None, description="Error message if any")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    conversation_id: Optional[str] = Field(default=None, description="Conversation identifier")


class AgentResponse(BaseModel):
    """Response from specific agent."""
    agent_name: str = Field(..., description="Name of the agent that processed the request")
    response: str = Field(..., description="The generated response")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    error: Optional[str] = Field(default=None, description="Error message if any")


class FileUploadResponse(BaseModel):
    """File upload response with metadata."""
    filename: str = Field(..., description="Name of the uploaded file")
    url: str = Field(..., description="URL or data URI of the uploaded file")
    mime_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="Size of the file in bytes")
    processed: bool = Field(default=False, description="Whether the file was processed")


class ModelInfo(BaseModel):
    """Model information and capabilities."""
    name: str = Field(..., description="Model name")
    display_name: str = Field(..., description="Human-readable model name")
    description: str = Field(..., description="Model description")
    supports_vision: bool = Field(..., description="Whether the model supports vision")
    supports_files: bool = Field(..., description="Whether the model supports file processing")
    provider: str = Field(..., description="Provider of the model")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens supported")
    cost_per_token: Optional[float] = Field(default=None, description="Cost per 1k tokens")


class AgentInfo(BaseModel):
    """Agent information and capabilities."""
    name: str = Field(..., description="Agent name")
    display_name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="Agent description")
    capabilities: List[str] = Field(..., description="List of agent capabilities")
    tools: List[str] = Field(..., description="List of tools available to the agent")
    status: str = Field(..., description="Current status of the agent")


class SearchResponse(BaseModel):
    """Web search results."""
    query: str = Field(..., description="Search query")
    results: List[str] = Field(..., description="List of search result URLs")


class ImageGenRequest(BaseModel):
    """Image generation request."""
    prompt: str = Field(..., description="Text prompt for image generation")


class ImageGenResponse(BaseModel):
    """Image generation response."""
    prompt: str = Field(..., description="Original prompt")
    url: str = Field(..., description="URL of the generated image")
