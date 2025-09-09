"""Request schemas for the agentic chat system."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .state import FileData


class ChatRequest(BaseModel):
    """Complete chat request with message, history, and configuration."""
    message: Dict[str, Any] = Field(..., description="Message content with text and files")
    history: List[Dict[str, Any]] = Field(default=[], description="Conversation history")
    system_prompt: Optional[str] = Field(default=None, description="System prompt for the conversation")
    provider: Optional[str] = Field(default=None, description="LLM provider to use (openai, anthropic, google, mistral)")
    model_name: Optional[str] = Field(default="mistral-large-latest", description="Model to use")
    stream: bool = Field(default=True, description="Whether to stream the response")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    conversation_id: Optional[str] = Field(default=None, description="Conversation identifier")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Browser metadata for enhanced responses")


class AgentRequest(BaseModel):
    """Request for specific agent processing."""
    agent_name: str = Field(..., description="Name of the agent to use")
    message: str = Field(..., description="Message to process")
    files: List[FileData] = Field(default=[], description="Files to process")
    parameters: Dict[str, Any] = Field(default={}, description="Additional parameters")
    stream: bool = Field(default=True, description="Whether to stream the response")
    session_id: Optional[str] = Field(default=None, description="Session identifier")


class FileUploadRequest(BaseModel):
    """File upload request."""
    filename: str = Field(..., description="Name of the file")
    mime_type: str = Field(..., description="MIME type of the file")
    data: str = Field(..., description="Base64 encoded file data")
    size: int = Field(..., description="Size of the file in bytes")
