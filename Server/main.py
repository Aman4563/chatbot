"""Optimized FastAPI application with performance enhancements."""

import uuid
import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import base64

# Import optimized components
from config.settings import settings, get_settings
from config.models import MODEL_CONFIG, get_available_models
from config.agents import AGENT_CONFIG, get_available_agents
from schemas.requests import ChatRequest, AgentRequest, FileUploadRequest
from schemas.responses import ChatResponse, AgentResponse, FileUploadResponse, ModelInfo, AgentInfo
from agents.chat_agent import ChatAgent
from agents.file_agent import FileAgent
from agents.search_agent import SearchAgent
from agents.image_agent import ImageAgent
from agents.metadata_agent import MetadataAgent
from agents.base import AgentRegistry
from providers.optimized_provider import OptimizedProviderRegistry
from providers.openai_provider import OpenAIProvider
from providers.anthropic_provider import AnthropicProvider
from providers.google_provider import GoogleProvider
from providers.mistral_provider import MistralProvider
from graphs.state import ChatState, FileState, SearchState, ImageState
from utils.performance_optimizer import (
    get_performance_tracker, get_response_cache, get_connection_pool,
    cleanup_resources, performance_monitor
)
from services.conversation_manager import conversation_manager

# Initialize FastAPI app
app = FastAPI(
    title="Optimized Agentic Chat API",
    version="4.1.0",
    description="High-Performance AI Chat API with Agentic Architecture powered by LangGraph"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize optimized agent and provider registries
agent_registry = AgentRegistry()
provider_registry = OptimizedProviderRegistry()

# Initialize optimized providers with API keys from settings
openai_provider = OpenAIProvider(api_key=settings.openai_api_key)
anthropic_provider = AnthropicProvider(api_key=settings.anthropic_api_key)
google_provider = GoogleProvider(api_key=settings.google_api_key)
mistral_provider = MistralProvider(api_key=settings.mistral_api_key)

# Initialize optimized agents with providers
chat_agent = ChatAgent(providers={
    "openai": openai_provider,
    "anthropic": anthropic_provider,
    "google": google_provider,
    "mistral": mistral_provider
})
file_agent = FileAgent()
search_agent = SearchAgent()
image_agent = ImageAgent()
metadata_agent = MetadataAgent()

# Register agents
agent_registry.register_agent(chat_agent)
agent_registry.register_agent(file_agent)
agent_registry.register_agent(search_agent)
agent_registry.register_agent(image_agent)
agent_registry.register_agent(metadata_agent)

# Register providers (warmup will happen in startup event)
provider_registry.providers["openai"] = openai_provider
provider_registry.providers["anthropic"] = anthropic_provider
provider_registry.providers["google"] = google_provider
provider_registry.providers["mistral"] = mistral_provider


def _ensure_state_keys(state: Dict[str, Any]) -> None:
    """Ensure all required keys are present in the state dictionary."""
    required_keys = {
        "messages": [],
        "user_input": "",
        "current_agent": "",
        "selected_provider": None,
        "selected_model": "mistral-large-latest",
        "system_prompt": None,
        "active_tools": [],
        "tool_results": {},
        "tool_errors": {},
        "attachments": [],
        "processed_files": {},
        "search_queries": [],
        "search_results": [],
        "image_requests": [],
        "generated_images": [],
        "response_mode": "stream",
        "llm_response": None,
        "synthesized_response": None,
        "final_response": None,
        "streaming_chunks": [],
        "session_id": "",
        "conversation_id": "",
        "conversation_history": [],
        "conversation_context": [],
        "context_window": 4000,
        "max_tokens": 8192,
        "temperature": 0.7,
        "conversation_loaded": False,
        "metadata": {}
    }
    
    for key, default_value in required_keys.items():
        if key not in state:
            state[key] = default_value


async def load_conversation_context(conversation_id: str, session_id: str) -> Dict[str, Any]:
    """Load conversation context from the conversation manager."""
    try:
        # Get conversation context optimized for LLM
        conversation_context = await conversation_manager.get_conversation_context(
            conversation_id=conversation_id,
            max_tokens=4000,
            include_system=True
        )
        
        # Get full conversation history for reference
        conversation_history = await conversation_manager.get_conversation_history(
            conversation_id=conversation_id,
            include_system=True
        )
        
        return {
            "conversation_context": conversation_context,
            "conversation_history": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                for msg in conversation_history
            ],
            "conversation_loaded": True
        }
    
    except Exception as e:
        print(f"⚠️ Error loading conversation context: {e}")
        return {
            "conversation_context": [],
            "conversation_history": [],
            "conversation_loaded": False
        }


def convert_request_to_chat_state(request: ChatRequest) -> ChatState:
    """Convert ChatRequest to ChatState for LangGraph."""
    state = {
        "messages": [],
        "user_input": request.message.get("text", ""),
        "current_agent": "chat_agent",
        "selected_provider": request.provider,
        "selected_model": request.model_name or "mistral-large-latest",
        "system_prompt": request.system_prompt,
        "active_tools": [],
        "tool_results": {},
        "tool_errors": {},
        "attachments": [
            {
                "filename": file.get("filename", ""),
                "mime_type": file.get("mime_type", ""),
                "data": file.get("data", ""),
                "url": file.get("url", "")
            }
            for file in request.message.get("files", [])
        ],
        "processed_files": {},
        "search_queries": [],
        "search_results": [],
        "image_requests": [],
        "generated_images": [],
        "response_mode": "stream" if request.stream else "batch",
        "final_response": None,
        "streaming_chunks": [],
        "session_id": request.session_id or str(uuid.uuid4()),
        "conversation_id": request.conversation_id or str(uuid.uuid4()),
        "conversation_history": [],
        "conversation_context": [],
        "context_window": 4000,
        "max_tokens": 8192,
        "temperature": 0.7,
        "conversation_loaded": False,
        "metadata": {},
        # LLM Intent Analysis fields
        "tool_plan": [],
        "analysis_confidence": 0.0,
        "analysis_reasoning": "",
        # Metadata fields for enhanced search
        "ip_address": getattr(request, 'ip_address', None),
        "user_agent": getattr(request, 'user_agent', None),
        "client_hints": getattr(request, 'client_hints', None),
        "timezone_input": getattr(request, 'timezone_input', None),
        "latitude": getattr(request, 'latitude', None),
        "longitude": getattr(request, 'longitude', None),
        "address": getattr(request, 'address', None)
    }
    
    # Ensure all required keys are present
    _ensure_state_keys(state)
    return state


def convert_request_to_file_state(request: ChatRequest) -> FileState:
    """Convert ChatRequest to FileState for file processing."""
    state = {
        "messages": [],
        "user_input": request.message.get("text", ""),
        "current_agent": "file_agent",
        "attachments": [
            {
                "filename": file.get("filename", ""),
                "mime_type": file.get("mime_type", ""),
                "data": file.get("data", ""),
                "url": file.get("url", "")
            }
            for file in request.message.get("files", [])
        ],
        "processed_files": {},
        "file_analysis_results": {},
        "processing_stage": "initialized",
        "extraction_results": {},
        "analysis_results": {},
        "final_response": None,
        "summary": None,
        "session_id": request.session_id or str(uuid.uuid4()),
        "conversation_id": request.conversation_id or str(uuid.uuid4()),
        "metadata": {}
    }
    
    # Ensure all required keys are present
    _ensure_state_keys(state)
    return state


def convert_request_to_search_state(request: ChatRequest) -> SearchState:
    """Convert ChatRequest to SearchState for web search."""
    state = {
        "messages": [],
        "user_input": request.message.get("text", ""),
        "current_agent": "search_agent",
        "search_queries": [],
        "search_results": [],
        "search_provider": "auto",
        "max_results": 10,
        "query_analysis": {},
        "result_filtering": {},
        "result_synthesis": {},
        "final_response": None,
        "citations": [],
        "session_id": request.session_id or str(uuid.uuid4()),
        "conversation_id": request.conversation_id or str(uuid.uuid4()),
        "metadata": {}
    }
    
    # Ensure all required keys are present
    _ensure_state_keys(state)
    return state


def convert_request_to_image_state(request: ChatRequest) -> ImageState:
    """Convert ChatRequest to ImageState for image generation."""
    state = {
        "messages": [],
        "user_input": request.message.get("text", ""),
        "current_agent": "image_agent",
        "image_requests": [],
        "generated_images": [],
        "image_provider": "openai",
        "image_model": "dall-e-3",
        "prompt_analysis": {},
        "generation_params": {},
        "post_processing": {},
        "final_response": None,
        "image_urls": [],
        "session_id": request.session_id or str(uuid.uuid4()),
        "conversation_id": request.conversation_id or str(uuid.uuid4()),
        "metadata": {}
    }
    
    # Ensure all required keys are present
    _ensure_state_keys(state)
    return state


@app.on_event("startup")
async def startup_event():
    """Initialize performance optimizations on startup."""
    try:
        # Skip warmup to avoid API quota consumption
        # await provider_registry.warmup_all_providers()
        print("🚀 Optimized Chat API started (warmup disabled to preserve API quota)")
    except Exception as e:
        print(f"⚠️ Startup warning: {e}")
        print("🚀 Optimized Chat API started (some optimizations may be limited)")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    await cleanup_resources()
    await provider_registry.cleanup_all_providers()
    print("🛑 Optimized Chat API shutdown complete")


@app.post("/chat")
@performance_monitor("chat_endpoint")
async def chat_endpoint(request: ChatRequest, http_request: Request):
    """
    Optimized main chat endpoint using chatAgent with parallel processing
    """
    try:
        print(f"🚀 Received optimized chat request:")
        print(f" - Message: {request.message.get('text', '')[:100] if request.message.get('text') else 'No text'}...")
        print(f" - Files: {len(request.message.get('files', []))}")
        print(f" - Model: {request.model_name}")
        print(f" - Stream: {request.stream}")
        print(f" - Conversation ID: {request.conversation_id}")
        print(f" - Session ID: {request.session_id}")
        # Extract metadata from request headers
        client_ip = http_request.client.host if http_request.client else None
        # Check for X-Forwarded-For header (for testing with real IPs)
        if http_request.headers.get("x-forwarded-for"):
            client_ip = http_request.headers.get("x-forwarded-for").split(",")[0].strip()
        user_agent = http_request.headers.get("user-agent", "")
        client_hints = {
            "Sec-CH-UA": http_request.headers.get("sec-ch-ua", ""),
            "Sec-CH-UA-Mobile": http_request.headers.get("sec-ch-ua-mobile", ""),
            "Sec-CH-UA-Platform": http_request.headers.get("sec-ch-ua-platform", "")
        }
        
        print(f" - Client IP: {client_ip}")
        print(f" - User Agent: {user_agent[:100] if user_agent else 'None'}...")
        
        # Convert request to state
        state = convert_request_to_chat_state(request)
        
        # Add metadata from request headers
        if client_ip:
            state["ip_address"] = client_ip
        if user_agent:
            state["user_agent"] = user_agent
        if any(client_hints.values()):
            state["client_hints"] = client_hints
        
        # Add metadata from frontend if provided
        if request.metadata:
            print(f"📱 Frontend metadata received: {request.metadata}")
            if request.metadata.get("timezone"):
                state["timezone_input"] = request.metadata["timezone"]
            if request.metadata.get("location"):
                location = request.metadata["location"]
                if location.get("latitude") and location.get("longitude"):
                    state["latitude"] = location["latitude"]
                    state["longitude"] = location["longitude"]
            if request.metadata.get("language"):
                state["language"] = request.metadata["language"]
            if request.metadata.get("platform"):
                state["platform"] = request.metadata["platform"]
            if request.metadata.get("consent"):
                state["consent"] = request.metadata["consent"]
        
        # Load conversation context if conversation_id is provided
        if request.conversation_id:
            print(f"📚 Loading conversation context for: {request.conversation_id}")
            
            # Check if conversation exists, if not create it
            existing_conversation = await conversation_manager.get_conversation(request.conversation_id)
            if not existing_conversation:
                print(f"🆕 Creating new conversation: {request.conversation_id}")
                await conversation_manager.create_conversation_with_id(
                    conversation_id=request.conversation_id,
                    title="Chat Conversation",
                    session_id=request.session_id or state["session_id"],
                    metadata={"created_from_frontend": True}
                )
            
            context_data = await load_conversation_context(
                conversation_id=request.conversation_id,
                session_id=request.session_id or state["session_id"]
            )
            
            # Update state with conversation context
            state.update(context_data)
            print(f"✅ Loaded {len(state['conversation_context'])} context messages")
        
        # Add user message to conversation if conversation_id exists
        if request.conversation_id and request.message.get("text"):
            await conversation_manager.add_message(
                conversation_id=request.conversation_id,
                role="user",
                content=request.message.get("text", ""),
                metadata={
                    "files_count": len(request.message.get("files", [])),
                    "model": request.model_name,
                    "provider": request.provider
                },
                files=request.message.get("files", [])
            )
        
        if request.stream:
            # Streaming response with optimizations
            async def generate_response():
                try:
                    full_response = ""
                    async for chunk in chat_agent.stream(state):
                        if isinstance(chunk, str) and not chunk.startswith("🔍") and not chunk.startswith("🤝") and not chunk.startswith("👥") and not chunk.startswith("📄") and not chunk.startswith("🔍") and not chunk.startswith("🎨") and not chunk.startswith("🧠") and not chunk.startswith("🔄") and not chunk.startswith("✅"):
                            full_response += chunk
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    
                    # Add assistant response to conversation if conversation_id exists
                    if request.conversation_id and full_response.strip():
                        await conversation_manager.add_message(
                            conversation_id=request.conversation_id,
                            role="assistant",
                            content=full_response.strip(),
                            metadata=state.get("metadata", {})
                        )
                    
                    yield f"data: {json.dumps({'done': True})}\n\n"
                except Exception as e:
                    print(f"❌ Error in optimized stream generation: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                generate_response(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        else:
            # Non-streaming response with optimizations
            result = await chat_agent.process(state)
            
            # Add assistant response to conversation if conversation_id exists
            if request.conversation_id and result.get("final_response"):
                await conversation_manager.add_message(
                    conversation_id=request.conversation_id,
                    role="assistant",
                    content=result.get("final_response", ""),
                    metadata=result.get("metadata", {})
                )
            
            return ChatResponse(
                response=result.get("final_response", "No response generated"),
                metadata=result.get("metadata", {}),
                session_id=result.get("session_id"),
                conversation_id=result.get("conversation_id")
            )
    
    except Exception as e:
        print(f"❌ Error in optimized chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_name}")
@performance_monitor("agent_endpoint")
async def agent_endpoint(agent_name: str, request: AgentRequest):
    """
    Optimized direct agent access endpoint
    """
    try:
        # Get agent from registry
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        print(f"🚀 Processing optimized request with {agent_name}:")
        print(f" - Message: {request.message[:100]}...")
        print(f" - Files: {len(request.files)}")
        print(f" - Stream: {request.stream}")
        
        # Convert request to appropriate state based on agent
        if agent_name == "chat_agent":
            chat_request = ChatRequest(
                message={"text": request.message, "files": request.files},
                model_name=request.parameters.get("model", "mistral-large"),
                stream=request.stream,
                session_id=request.session_id
            )
            state = convert_request_to_chat_state(chat_request)
        elif agent_name == "file_agent":
            chat_request = ChatRequest(
                message={"text": request.message, "files": request.files},
                stream=request.stream,
                session_id=request.session_id
            )
            state = convert_request_to_file_state(chat_request)
        elif agent_name == "search_agent":
            chat_request = ChatRequest(
                message={"text": request.message, "files": request.files},
                stream=request.stream,
                session_id=request.session_id
            )
            state = convert_request_to_search_state(chat_request)
        elif agent_name == "image_agent":
            chat_request = ChatRequest(
                message={"text": request.message, "files": request.files},
                stream=request.stream,
                session_id=request.session_id
            )
            state = convert_request_to_image_state(chat_request)
        elif agent_name == "metadata_agent":
            # Create a simple state for metadata agent
            state = {
                "user_input": request.message,
                "session_id": request.session_id or str(uuid.uuid4()),
                "ip_address": getattr(request, 'ip_address', None),
                "user_agent": getattr(request, 'user_agent', None),
                "client_hints": getattr(request, 'client_hints', None),
                "timezone_input": getattr(request, 'timezone_input', None),
                "latitude": getattr(request, 'latitude', None),
                "longitude": getattr(request, 'longitude', None),
                "address": getattr(request, 'address', None),
                "metadata": {}
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported agent: {agent_name}")
        
        if request.stream:
            # Streaming response
            async def generate_response():
                try:
                    async for chunk in agent.stream(state):
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    yield f"data: {json.dumps({'done': True})}\n\n"
                except Exception as e:
                    print(f"❌ Error in agent stream: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                generate_response(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        else:
            # Non-streaming response
            result = await agent.process(state)
            return AgentResponse(
                agent_name=agent_name,
                response=result.get("final_response", "No response generated"),
                metadata=result.get("metadata", {}),
                session_id=result.get("session_id")
            )
    
    except Exception as e:
        print(f"❌ Error in optimized agent endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/file/upload", response_model=FileUploadResponse)
@performance_monitor("file_upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Optimized file upload with comprehensive validation
    """
    try:
        # Validate file size
        contents = await file.read()
        max_size = settings.max_file_size if not file.content_type.startswith('image/') else settings.max_image_size
        
        if len(contents) > max_size:
            max_mb = max_size // (1024 * 1024)
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {max_mb}MB.")
        
        # Validate file type
        if file.content_type not in settings.allowed_file_types:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")
        
        # Validate file content for security
        filename_lower = file.filename.lower() if file.filename else ""
        if any(ext in filename_lower for ext in ['.exe', '.bat', '.cmd', '.scr', '.vbs']):
            raise HTTPException(status_code=400, detail="Executable files are not allowed")
        
        base64_encoded = base64.b64encode(contents).decode('utf-8')
        
        print(f"✅ File uploaded successfully: {file.filename} ({file.content_type}, {len(contents)} bytes)")
        
        return FileUploadResponse(
            filename=file.filename,
            url=f"data:{file.content_type};base64,{base64_encoded}",
            mime_type=file.content_type,
            size=len(contents)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.get("/models", response_model=List[ModelInfo])
async def get_available_models_endpoint():
    """
    Return detailed information about available models
    """
    models = []
    
    for model_name, config in MODEL_CONFIG.items():
        models.append(ModelInfo(
            name=model_name,
            display_name=model_name.replace("-", " ").title(),
            description=f"{config['provider'].title()} model with advanced capabilities",
            supports_vision=config["supports_vision"],
            supports_files=config["supports_files"],
            provider=config["provider"],
            max_tokens=config.get("max_tokens"),
            cost_per_token=config.get("cost_per_1k_tokens")
        ))
    
    return models


@app.get("/agents", response_model=List[AgentInfo])
async def get_available_agents_endpoint():
    """
    Return detailed information about available agents
    """
    agents = []
    
    for agent_name, config in AGENT_CONFIG.items():
        agents.append(AgentInfo(
            name=agent_name,
            display_name=config["name"],
            description=config["description"],
            capabilities=config["capabilities"],
            tools=config["tools"],
            status="active" if config.get("enabled", True) else "inactive"
        ))
    
    return agents


@app.get("/providers")
async def get_available_providers():
    """
    Return information about available providers with performance metrics
    """
    return provider_registry.get_all_provider_info()


@app.get("/performance")
async def get_performance_metrics():
    """
    Get detailed performance metrics and statistics
    """
    performance_tracker = get_performance_tracker()
    response_cache = get_response_cache()
    
    return {
        "performance_tracker": {
            "total_operations": len(performance_tracker.metrics),
            "operation_stats": {
                operation: performance_tracker.get_operation_stats(operation)
                for operation in set(m.operation_name for m in performance_tracker.metrics)
            }
        },
        "response_cache": response_cache.get_stats(),
        "provider_performance": provider_registry.get_performance_summary(),
        "system_health": {
            "agents_active": len(agent_registry.get_all_agent_info()),
            "providers_active": len(provider_registry.get_all_providers()),
            "cache_hit_rate": response_cache.get_stats().get("hit_rate", 0)
        }
    }


@app.get("/health")
async def health_check():
    """
    Enhanced health check with performance metrics
    """
    try:
        # Check agent status
        agent_info = agent_registry.get_all_agent_info()
        active_agents = len([info for info in agent_info.values() if info.get("graph_built", False)])
        
        # Check provider status
        provider_info = provider_registry.get_all_provider_info()
        active_providers = len([info for info in provider_info.values() if info.get("api_key_configured", False)])
        
        # Get performance metrics
        performance_tracker = get_performance_tracker()
        response_cache = get_response_cache()
        
        return {
            "status": "healthy",
            "message": "Optimized Agentic Chat API with LangGraph is running",
            "version": "4.1.0",
            "optimization_features": [
                "parallel_processing",
                "response_caching",
                "connection_pooling",
                "performance_monitoring",
                "intelligent_batching"
            ],
            "agents": {
                "total": len(agent_info),
                "active": active_agents,
                "list": list(agent_info.keys())
            },
            "providers": {
                "total": len(provider_info),
                "active": active_providers,
                "list": list(provider_info.keys())
            },
            "performance": {
                "total_operations": len(performance_tracker.metrics),
                "cache_hit_rate": response_cache.get_stats().get("hit_rate", 0),
                "cache_size": response_cache.get_stats().get("size", 0)
            },
            "models_available": len(MODEL_CONFIG),
            "features": [
                "agentic_architecture",
                "langgraph_workflows",
                "streaming_responses",
                "multi_modal_processing",
                "document_analysis",
                "web_search",
                "image_generation",
                "tool_orchestration",
                "multi_provider_support",
                "parallel_processing",
                "response_caching",
                "performance_monitoring"
            ],
            "supported_formats": [
                "PDF", "DOCX", "CSV", "JSON", "TXT",
                "Images (JPEG, PNG, GIF, WebP)",
                "Code files", "Markdown", "XML"
            ]
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/conversations")
async def create_conversation(
    title: str = "New Conversation",
    session_id: Optional[str] = None
):
    """Create a new conversation."""
    try:
        conversation = await conversation_manager.create_conversation(
            title=title,
            session_id=session_id
        )
        return {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at,
            "session_id": conversation.session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a conversation by ID."""
    try:
        conversation = await conversation_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "id": conversation.id,
            "title": conversation.title,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata,
                    "files": msg.files
                }
                for msg in conversation.messages
            ],
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "session_id": conversation.session_id,
            "metadata": conversation.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations")
async def get_session_conversations(session_id: str):
    """Get all conversations for a session."""
    try:
        conversations = await conversation_manager.get_session_conversations(session_id)
        return [
            {
                "id": conv.id,
                "title": conv.title,
                "message_count": len(conv.messages),
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "session_id": conv.session_id
            }
            for conv in conversations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/conversations/{conversation_id}/title")
async def update_conversation_title(conversation_id: str, title: str):
    """Update conversation title."""
    try:
        success = await conversation_manager.update_conversation_title(conversation_id, title)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Title updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    try:
        success = await conversation_manager.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/stats")
async def get_conversation_stats():
    """Get conversation manager statistics."""
    try:
        stats = conversation_manager.get_cache_stats()
        return {
            "cache_stats": stats,
            "storage_path": str(conversation_manager.storage_path),
            "max_memory_conversations": conversation_manager.max_memory_conversations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Optimized Agentic Chat API with LangGraph",
        "version": "4.1.0",
        "documentation": "/docs",
        "architecture": "agentic",
        "framework": "langgraph",
        "optimization_level": "high_performance",
        "features": [
            "Agent-based architecture",
            "LangGraph workflows",
            "Multi-provider LLM support",
            "Streaming responses",
            "Document analysis",
            "Web search",
            "Image generation",
            "Tool orchestration",
            "Parallel processing",
            "Response caching",
            "Performance monitoring",
            "Conversation context management"
        ],
        "endpoints": {
            "chat": "/chat",
            "agents": "/agents/{agent_name}",
            "models": "/models",
            "agents_list": "/agents",
            "providers": "/providers",
            "performance": "/performance",
            "health": "/health",
            "upload": "/file/upload",
            "conversations": "/conversations",
            "conversation": "/conversations/{conversation_id}",
            "conversation_stats": "/conversations/stats"
        }
    }


# Legacy endpoints for backward compatibility
@app.get("/tools/search")
async def search_tool_endpoint(
    q: str = Query(..., description="Search query"),
    num_results: int = Query(5, gt=0, le=20)
):
    """
    Legacy search endpoint - redirects to SearchAgent
    """
    try:
        # Create a simple request for SearchAgent
        request = AgentRequest(
            agent_name="search_agent",
            message=q,
            parameters={"num_results": num_results},
            stream=False
        )
        
        # Process with SearchAgent
        agent = agent_registry.get_agent("search_agent")
        if not agent:
            raise HTTPException(status_code=500, detail="SearchAgent not available")
        
        chat_request = ChatRequest(
            message={"text": q, "files": []},
            stream=False
        )
        state = convert_request_to_search_state(chat_request)
        result = await agent.process(state)
        
        # Extract search results
        search_results = result.get("search_results", [])
        urls = [result.get("url", "") for result in search_results]
        
        return {"query": q, "results": urls}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/image")
async def image_tool_endpoint(body: dict):
    """
    Legacy image generation endpoint - redirects to ImageAgent
    """
    try:
        prompt = body.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Create a simple request for ImageAgent
        request = AgentRequest(
            agent_name="image_agent",
            message=f"Generate image: {prompt}",
            stream=False
        )
        
        # Process with ImageAgent
        agent = agent_registry.get_agent("image_agent")
        if not agent:
            raise HTTPException(status_code=500, detail="ImageAgent not available")
        
        chat_request = ChatRequest(
            message={"text": f"Generate image: {prompt}", "files": []},
            stream=False
        )
        state = convert_request_to_image_state(chat_request)
        result = await agent.process(state)
        
        # Extract generated images
        generated_images = result.get("generated_images", [])
        if generated_images:
            image_url = generated_images[0].get("image_url", "")
            return {"prompt": prompt, "url": image_url}
        else:
            raise HTTPException(status_code=500, detail="No image generated")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
