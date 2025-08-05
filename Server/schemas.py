# schemas.py

from typing import List, Optional, Union
from pydantic import BaseModel, Field

class FileData(BaseModel):
    data: str  # Base64-encoded content
    mime_type: str  # e.g. 'image/png', 'text/plain'
    filename: str  # Required filename
    url: Optional[str] = None  # Optional URL for preview

class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str  # Text content
    files: List[FileData] = []  # Attached files

class LastUserMessage(BaseModel):
    text: str
    files: List[FileData] = []

class ChatRequest(BaseModel):
    message: LastUserMessage
    history: List[Message] = []  # Full conversation history
    system_prompt: Optional[str] = "You are a helpful AI assistant with vision and document analysis capabilities."
    model_name: Optional[str] = Field(
        "mistral-large",
        title="Model name",
        description="Name of the model to use for this chat session"
    )

class ChatResponse(BaseModel):
    response: str
    error: Optional[str] = None

class FileUploadResponse(BaseModel):
    filename: str
    url: str
    mime_type: str
    size: int

class ModelInfo(BaseModel):
    name: str
    display_name: str
    description: str
    supports_vision: bool
    supports_files: bool
    provider: str  # New field to indicate the provider (e.g., "mistral", "openai", "anthropic")


class SearchResponse(BaseModel):
    query: str
    results: List[str]

class ImageGenRequest(BaseModel):
    prompt: str

class ImageGenResponse(BaseModel):
    prompt: str
    url: str

