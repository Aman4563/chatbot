"""State schemas for the agentic chat system."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FileData(BaseModel):
    """File data structure."""
    filename: str = Field(..., description="Name of the file")
    mime_type: str = Field(..., description="MIME type of the file")
    data: str = Field(..., description="Base64 encoded file data")
    url: Optional[str] = Field(default=None, description="URL of the file if available")
    size: Optional[int] = Field(default=None, description="Size of the file in bytes")


class MessageData(BaseModel):
    """Message data structure."""
    text: str = Field(..., description="Text content of the message")
    files: List[FileData] = Field(default=[], description="Files attached to the message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class AgentState(BaseModel):
    """Base agent state structure."""
    messages: List[Dict[str, Any]] = Field(default=[], description="List of messages")
    user_input: str = Field(..., description="User input text")
    current_agent: str = Field(..., description="Current agent name")
    session_id: str = Field(..., description="Session identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class ChatState(AgentState):
    """Chat agent state structure."""
    selected_provider: Optional[str] = Field(default=None, description="Selected LLM provider")
    selected_model: str = Field(default="gemini-2.0-flash", description="Selected model")
    system_prompt: Optional[str] = Field(default=None, description="System prompt")
    active_tools: List[str] = Field(default=[], description="List of active tools")
    tool_results: Dict[str, Any] = Field(default={}, description="Results from tool execution")
    tool_errors: Dict[str, str] = Field(default={}, description="Errors from tool execution")
    attachments: List[Dict[str, Any]] = Field(default=[], description="File attachments")
    processed_files: Dict[str, str] = Field(default={}, description="Processed file content")
    search_queries: List[str] = Field(default=[], description="Search queries")
    search_results: List[Dict[str, Any]] = Field(default=[], description="Search results")
    image_requests: List[Dict[str, Any]] = Field(default=[], description="Image generation requests")
    generated_images: List[Dict[str, Any]] = Field(default=[], description="Generated images")
    response_mode: str = Field(default="stream", description="Response mode")
    final_response: Optional[str] = Field(default=None, description="Final response text")
    streaming_chunks: List[str] = Field(default=[], description="Streaming response chunks")


class FileState(AgentState):
    """File agent state structure."""
    attachments: List[Dict[str, Any]] = Field(default=[], description="File attachments")
    processed_files: Dict[str, str] = Field(default={}, description="Processed file content")
    file_analysis_results: Dict[str, Any] = Field(default={}, description="File analysis results")
    processing_stage: str = Field(default="initialized", description="Current processing stage")
    extraction_results: Dict[str, Any] = Field(default={}, description="Content extraction results")
    analysis_results: Dict[str, Any] = Field(default={}, description="Content analysis results")
    final_response: Optional[str] = Field(default=None, description="Final response text")
    summary: Optional[str] = Field(default=None, description="Summary of processed files")


class SearchState(AgentState):
    """Search agent state structure."""
    search_queries: List[str] = Field(default=[], description="Search queries")
    search_results: List[Dict[str, Any]] = Field(default=[], description="Search results")
    search_provider: str = Field(default="auto", description="Search provider")
    max_results: int = Field(default=10, description="Maximum number of results")
    query_analysis: Dict[str, Any] = Field(default={}, description="Query analysis results")
    result_filtering: Dict[str, Any] = Field(default={}, description="Result filtering results")
    result_synthesis: Dict[str, Any] = Field(default={}, description="Result synthesis results")
    final_response: Optional[str] = Field(default=None, description="Final response text")
    citations: List[Dict[str, str]] = Field(default=[], description="Citations from search results")


class ImageState(AgentState):
    """Image agent state structure."""
    image_requests: List[Dict[str, Any]] = Field(default=[], description="Image generation requests")
    generated_images: List[Dict[str, Any]] = Field(default=[], description="Generated images")
    image_provider: str = Field(default="openai", description="Image generation provider")
    image_model: str = Field(default="dall-e-3", description="Image generation model")
    prompt_analysis: Dict[str, Any] = Field(default={}, description="Prompt analysis results")
    generation_params: Dict[str, Any] = Field(default={}, description="Generation parameters")
    post_processing: Dict[str, Any] = Field(default={}, description="Post-processing results")
    final_response: Optional[str] = Field(default=None, description="Final response text")
    image_urls: List[str] = Field(default=[], description="URLs of generated images")
