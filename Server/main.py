# main.py

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List
import json
import base64

from schemas import (
    ChatRequest, ChatResponse, FileData, FileUploadResponse, 
    ModelInfo, SearchResponse, ImageGenRequest, ImageGenResponse
)
from model import my_genai_chat_function_stream, MODEL_CONFIG, web_search_tool, image_gen_tool

# FastAPI app configuration
app = FastAPI(title="AI Chat API with Document Analysis", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
MAX_FILE_SIZE_MB = {"image": 10, "document": 50}
ALLOWED_MIME_TYPES = {
    # Images
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp', 'image/tiff',
    # Text files
    'text/plain', 'text/csv', 'text/markdown', 'text/xml',
    # Data files
    'application/json', 'application/xml',
    # Documents
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    # Programming files
    'text/x-python', 'application/javascript', 'text/html', 'text/css'
}
FORBIDDEN_EXTENSIONS = {'.exe', '.bat', '.cmd', '.scr', '.vbs'}

@app.post("/chat")
async def chat_endpoint(payload: ChatRequest):
    """
    Enhanced streaming chat endpoint with LangChain multi-model support
    """
    try:
        _log_chat_request(payload)
        _validate_model(payload.model_name)
        
        return StreamingResponse(
            _generate_streaming_response(payload),
            media_type="text/plain",
            headers=_get_streaming_headers()
        )
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _log_chat_request(payload: ChatRequest) -> None:
    """Log incoming chat request details."""
    print(f"Received chat request:")
    print(f" - Message: {payload.message.text[:100] if payload.message.text else 'No text'}...")
    print(f" - Files: {len(payload.message.files)}")
    print(f" - History length: {len(payload.history)}")
    print(f" - Model: {payload.model_name}")
    
    for file_data in payload.message.files:
        print(f" - File: {file_data.filename} ({file_data.mime_type})")


def _validate_model(model_name: str) -> None:
    """Validate that the model is supported."""
    if model_name not in MODEL_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {model_name}")


def _generate_streaming_response(payload: ChatRequest):
    """Generate streaming response with error handling."""
    try:
        for chunk in my_genai_chat_function_stream(payload):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as e:
        print(f"Error in stream generation: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


def _get_streaming_headers() -> dict:
    """Get headers for streaming response."""
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
    }

@app.post("/file/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Enhanced file upload with comprehensive validation and document support
    """
    try:
        contents = await file.read()
        _validate_file_upload(file, contents)
        
        base64_encoded = base64.b64encode(contents).decode('utf-8')
        print(f"File uploaded successfully: {file.filename} ({file.content_type}, {len(contents)} bytes)")
        
        return FileUploadResponse(
            filename=file.filename,
            url=f"data:{file.content_type};base64,{base64_encoded}",
            mime_type=file.content_type,
            size=len(contents)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


def _validate_file_upload(file: UploadFile, contents: bytes) -> None:
    """Validate uploaded file size, type, and security."""
    # Validate file size
    file_type = "image" if file.content_type.startswith('image/') else "document"
    max_size = MAX_FILE_SIZE_MB[file_type] * 1024 * 1024
    
    if len(contents) > max_size:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB[file_type]}MB."
        )
    
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")
    
    # Security validation
    filename_lower = (file.filename or "").lower()
    if any(ext in filename_lower for ext in FORBIDDEN_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Executable files are not allowed")

@app.get("/models", response_model=List[ModelInfo])
async def get_available_models():
    """
    Return detailed information about available models across different providers
    """
    return [
        ModelInfo(
            name=model_name,
            display_name=model_name.replace("-", " ").title(),
            description=f"{config['provider'].title()} model with advanced capabilities",
            supports_vision=config["supports_vision"],
            supports_files=config["supports_files"],
            provider=config["provider"]
        )
        for model_name, config in MODEL_CONFIG.items()
    ]


@app.get("/tools/search", response_model=SearchResponse)
async def search_tool_endpoint(
    q: str = Query(..., description="Search query"),
    num_results: int = Query(5, gt=0, le=20)
):
    """Web search tool endpoint."""
    try:
        results = web_search_tool(q, num_results)
        return SearchResponse(query=q, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/image", response_model=ImageGenResponse)
async def image_tool_endpoint(body: ImageGenRequest):
    """Image generation tool endpoint."""
    try:
        url = image_gen_tool(body.prompt)
        return ImageGenResponse(prompt=body.prompt, url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint with system information."""
    try:
        return {
            "status": "healthy",
            "message": "Multi-Model Chat API with LangChain is running",
            "models_available": len(MODEL_CONFIG),
            "providers": list(set(config["provider"] for config in MODEL_CONFIG.values())),
            "features": [
                "streaming", "vision", "pdf_analysis", "word_documents",
                "csv_analysis", "json_processing", "context_awareness",
                "multi_modal", "multi_provider"
            ],
            "supported_formats": [
                "PDF", "DOCX", "CSV", "JSON", "TXT",
                "Images (JPEG, PNG, GIF, WebP)", "Markdown", "XML"
            ]
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Multi-Model AI Chat API with LangChain",
        "version": "3.0.0",
        "documentation": "/docs",
        "features": [
            "Multi-provider LLM support", "Streaming responses",
            "Document analysis", "Vision capabilities", "File processing"
        ]
    }
