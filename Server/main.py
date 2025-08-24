# main.py

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List
import json
import base64
from schemas import ChatRequest, ChatResponse, FileData, FileUploadResponse, ModelInfo,  SearchResponse, ImageGenRequest, ImageGenResponse
from model import my_genai_chat_function_stream, MODEL_CONFIG, web_search_tool, image_gen_tool

app = FastAPI(title="AI Chat API with Document Analysis", version="3.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat_endpoint(payload: ChatRequest):
    """
    Enhanced streaming chat endpoint with LangChain multi-model support
    """
    try:
        print(f"Received chat request:")
        print(f" - Message: {payload.message.text[:100] if payload.message.text else 'No text'}...")
        print(f" - Files: {len(payload.message.files)}")
        print(f" - History length: {len(payload.history)}")
        print(f" - Model: {payload.model_name}")
        
        # Validate model
        if payload.model_name not in MODEL_CONFIG:
            raise HTTPException(status_code=400, detail=f"Unsupported model: {payload.model_name}")
        
        # Log file types for debugging
        for file_data in payload.message.files:
            print(f" - File: {file_data.filename} ({file_data.mime_type})")
        
        def generate_response():
            try:
                for chunk in my_genai_chat_function_stream(payload):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                print(f"Error in stream generation: {e}")
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
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/file/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Enhanced file upload with comprehensive validation and document support
    """
    try:
        # Validate file size (max 50MB for documents, 10MB for images)
        contents = await file.read()
        max_size = 50 * 1024 * 1024 if not file.content_type.startswith('image/') else 10 * 1024 * 1024
        
        if len(contents) > max_size:
            max_mb = 50 if not file.content_type.startswith('image/') else 10
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {max_mb}MB.")
        
        # Comprehensive file type validation
        allowed_types = [
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
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")
        
        # Validate file content for security
        filename_lower = file.filename.lower() if file.filename else ""
        if any(ext in filename_lower for ext in ['.exe', '.bat', '.cmd', '.scr', '.vbs']):
            raise HTTPException(status_code=400, detail="Executable files are not allowed")
        
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

@app.get("/models", response_model=List[ModelInfo])
async def get_available_models():
    """
    Return detailed information about available models across different providers
    """
    models = []
    
    for model_name, config in MODEL_CONFIG.items():
        models.append(ModelInfo(
            name=model_name,
            display_name=model_name.replace("-", " ").title(),
            description=f"{config['provider'].title()} model with advanced capabilities",
            supports_vision=config["supports_vision"],
            supports_files=config["supports_files"],
            provider=config["provider"]
        ))
    
    return models

# Add this debug endpoint to your main.py for testing image generation
@app.get("/debug/image-test")
async def debug_image_test():
    """
    Debug endpoint to test image generation without frontend
    """
    try:
        test_prompt = "A beautiful sunset over mountains"
        url = image_gen_tool(test_prompt)
        
        return {
            "success": True,
            "prompt": test_prompt,
            "url": url,
            "url_type": type(url).__name__,
            "url_length": len(url),
            "is_data_url": url.startswith("data:") if isinstance(url, str) else False,
            "url_preview": url[:100] if isinstance(url, str) else str(url)[:100]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }





@app.get("/tools/search", response_model=SearchResponse)
async def search_tool_endpoint(
    q: str = Query(..., description="Search query"),
    num_results: int = Query(5, gt=0, le=20)
):
    """
    Tool: Web search (top N URLs).
    """
    try:
        results = web_search_tool(q, num_results)
        return SearchResponse(query=q, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/image", response_model=ImageGenResponse)
async def image_tool_endpoint(body: ImageGenRequest):
    """
    Tool: Image generation via Gemini or DALL·E fallback.
    """
    try:
        url = image_gen_tool(body.prompt)
        return ImageGenResponse(prompt=body.prompt, url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=dict)
async def health_check():
    """
    Enhanced health check with LangChain multi-model support
    """
    try:
        available_models = len(MODEL_CONFIG)
        providers = list(set([config["provider"] for config in MODEL_CONFIG.values()]))
        
        return {
            "status": "healthy",
            "message": "Multi-Model Chat API with LangChain is running",
            "models_available": available_models,
            "providers": providers,
            "features": [
                "streaming",
                "vision",
                "pdf_analysis",
                "word_documents",
                "csv_analysis",
                "json_processing",
                "context_awareness",
                "multi_modal",
                "multi_provider"
            ],
            "supported_formats": [
                "PDF", "DOCX", "CSV", "JSON", "TXT",
                "Images (JPEG, PNG, GIF, WebP)",
                "Markdown", "XML"
            ]
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Multi-Model AI Chat API with LangChain",
        "version": "3.0.0",
        "documentation": "/docs",
        "features": [
            "Multi-provider LLM support",
            "Streaming responses",
            "Document analysis",
            "Vision capabilities",
            "File processing"
        ]
    }
