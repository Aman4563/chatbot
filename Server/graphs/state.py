"""LangGraph state definitions for agentic chat system."""

from typing import TypedDict, List, Optional, Dict, Any, Union
from pydantic import BaseModel
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Main agent state for LangGraph workflows."""
    
    # Core conversation state
    messages: List[BaseMessage]
    user_input: str
    current_agent: str
    
    # Agent-specific state
    selected_provider: Optional[str]
    selected_model: str
    system_prompt: Optional[str]
    
    # Tool execution state
    active_tools: List[str]
    tool_results: Dict[str, Any]
    tool_errors: Dict[str, str]
    
    # File processing state
    attachments: List[Dict[str, Any]]
    processed_files: Dict[str, str]
    
    # Search state
    search_queries: List[str]
    search_results: List[Dict[str, Any]]
    
    # Image generation state
    image_requests: List[Dict[str, Any]]
    generated_images: List[Dict[str, Any]]
    
    # Response state
    response_mode: str  # "stream", "batch", "interactive"
    llm_response: Optional[str]
    synthesized_response: Optional[str]
    final_response: Optional[str]
    streaming_chunks: List[str]
    
    # Metadata
    session_id: str
    conversation_id: str
    metadata: Dict[str, Any]
    
    # User metadata fields for enhanced search
    ip_address: Optional[str]
    user_agent: Optional[str]
    client_hints: Optional[Dict[str, str]]
    timezone_input: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    address: Optional[str]


class ChatState(TypedDict):
    """State specific to chat agent."""
    
    # Inherit from AgentState
    messages: List[BaseMessage]
    user_input: str
    current_agent: str
    selected_provider: Optional[str]
    selected_model: str
    system_prompt: Optional[str]
    
    # Tool execution state
    active_tools: List[str]
    tool_results: Dict[str, Any]
    tool_errors: Dict[str, str]
    
    # File processing state
    attachments: List[Dict[str, Any]]
    processed_files: Dict[str, str]
    
    # Search state
    search_queries: List[str]
    search_results: List[Dict[str, Any]]
    
    # Image generation state
    image_requests: List[Dict[str, Any]]
    generated_images: List[Dict[str, Any]]
    
    # Chat-specific state with enhanced conversation management
    conversation_history: List[Dict[str, Any]]
    conversation_context: List[Dict[str, Any]]  # Optimized context for LLM
    context_window: int
    max_tokens: int
    temperature: float
    conversation_loaded: bool  # Flag to indicate if conversation was loaded
    
    # Response state
    response_mode: str
    llm_response: Optional[str]
    synthesized_response: Optional[str]
    final_response: Optional[str]
    streaming_chunks: List[str]
    
    # LLM Intent Analysis fields
    tool_plan: List[Dict[str, Any]]
    analysis_confidence: float
    analysis_reasoning: str
    
    # Metadata
    session_id: str
    conversation_id: str
    metadata: Dict[str, Any]
    
    # User metadata fields for enhanced search
    ip_address: Optional[str]
    user_agent: Optional[str]
    client_hints: Optional[Dict[str, str]]
    timezone_input: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    address: Optional[str]


class FileState(TypedDict):
    """State specific to file processing agent."""
    
    # Inherit from AgentState
    messages: List[BaseMessage]
    user_input: str
    current_agent: str
    
    # File-specific state
    attachments: List[Dict[str, Any]]
    processed_files: Dict[str, str]
    file_analysis_results: Dict[str, Any]
    
    # Processing state
    processing_stage: str  # "validate", "extract", "analyze", "summarize"
    extraction_results: Dict[str, str]
    analysis_results: Dict[str, Any]
    
    # Response state
    final_response: Optional[str]
    summary: Optional[str]
    
    # Metadata
    session_id: str
    conversation_id: str
    metadata: Dict[str, Any]


class SearchState(TypedDict):
    """State specific to search agent."""
    
    # Inherit from AgentState
    messages: List[BaseMessage]
    user_input: str
    current_agent: str
    
    # Search-specific state
    search_queries: List[str]
    search_results: List[Dict[str, Any]]
    search_provider: str
    max_results: int
    
    # Processing state
    query_analysis: Dict[str, Any]
    result_filtering: Dict[str, Any]
    result_synthesis: Dict[str, Any]
    
    # Response state
    final_response: Optional[str]
    citations: List[str]
    
    # Metadata
    session_id: str
    conversation_id: str
    metadata: Dict[str, Any]


class ImageState(TypedDict):
    """State specific to image generation agent."""
    
    # Inherit from AgentState
    messages: List[BaseMessage]
    user_input: str
    current_agent: str
    
    # Image-specific state
    image_requests: List[Dict[str, Any]]
    generated_images: List[Dict[str, Any]]
    image_provider: str
    image_model: str
    
    # Processing state
    prompt_analysis: Dict[str, Any]
    generation_params: Dict[str, Any]
    post_processing: Dict[str, Any]
    
    # Response state
    final_response: Optional[str]
    image_urls: List[str]
    
    # Metadata
    session_id: str
    conversation_id: str
    metadata: Dict[str, Any]


# Pydantic models for API schemas
class FileData(BaseModel):
    """File data with base64 content and metadata."""
    data: str
    mime_type: str
    filename: str
    url: Optional[str] = None
    size: Optional[int] = None


class Message(BaseModel):
    """Chat message with role, content, and optional files."""
    role: str  # 'user' or 'assistant'
    content: str
    files: Optional[List[FileData]] = None
    timestamp: Optional[str] = None


class LastUserMessage(BaseModel):
    """User's current message input."""
    text: str
    files: List[FileData] = []


class ChatRequest(BaseModel):
    """Complete chat request with message, history, and configuration."""
    message: LastUserMessage
    history: List[Message] = []
    system_prompt: Optional[str] = None
    model_name: Optional[str] = "mistral-large"
    stream: bool = True
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response with optional error information."""
    response: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None


class AgentRequest(BaseModel):
    """Request for specific agent processing."""
    agent_name: str
    message: str
    files: List[FileData] = []
    parameters: Dict[str, Any] = {}
    stream: bool = True
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    """Response from specific agent."""
    agent_name: str
    response: str
    metadata: Dict[str, Any] = {}
    session_id: Optional[str] = None
    error: Optional[str] = None


class FileUploadRequest(BaseModel):
    """File upload request."""
    filename: str
    mime_type: str
    data: str
    size: int


class FileUploadResponse(BaseModel):
    """File upload response with metadata."""
    filename: str
    url: str
    mime_type: str
    size: int
    processed: bool = False


class ModelInfo(BaseModel):
    """Model information and capabilities."""
    name: str
    display_name: str
    description: str
    supports_vision: bool
    supports_files: bool
    provider: str
    max_tokens: Optional[int] = None
    cost_per_token: Optional[float] = None


class AgentInfo(BaseModel):
    """Agent information and capabilities."""
    name: str
    display_name: str
    description: str
    capabilities: List[str]
    tools: List[str]
    status: str  # "active", "inactive", "maintenance"


class AgentStatus(BaseModel):
    """Agent status information."""
    agent_name: str
    status: str
    last_activity: Optional[str] = None
    active_sessions: int = 0
    error_count: int = 0
