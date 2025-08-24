"""Pydantic schemas for API request/response models."""

from typing import List, Optional
from pydantic import BaseModel, Field


class FileData(BaseModel):
    """File data with base64 content and metadata."""
    data: str
    mime_type: str
    filename: str
    url: Optional[str] = None


class Message(BaseModel):
    """Chat message with role, content, and optional files."""
    role: str  # 'user' or 'assistant'
    content: str
    files: List[FileData] = []


class LastUserMessage(BaseModel):
    """User's current message input."""
    text: str
    files: List[FileData] = []


class ChatRequest(BaseModel):
    """Complete chat request with message, history, and configuration."""
    message: LastUserMessage
    history: List[Message] = []
    system_prompt: Optional[str] = (
        "You are a helpful AI assistant with vision and document analysis capabilities."
    )
    model_name: Optional[str] = Field(
        default="mistral-large",
        title="Model name",
        description="Name of the model to use for this chat session"
    )


class ChatResponse(BaseModel):
    """Chat response with optional error information."""
    response: str
    error: Optional[str] = None


class FileUploadResponse(BaseModel):
    """File upload response with metadata."""
    filename: str
    url: str
    mime_type: str
    size: int


class ModelInfo(BaseModel):
    """Model information and capabilities."""
    name: str
    display_name: str
    description: str
    supports_vision: bool
    supports_files: bool
    provider: str


class SearchResponse(BaseModel):
    """Web search results."""
    query: str
    results: List[str]


class ImageGenRequest(BaseModel):
    """Image generation request."""
    prompt: str


class ImageGenResponse(BaseModel):
    """Image generation response."""
    prompt: str
    url: str

