"""Startup script for the agentic chat server."""

import uvicorn
from main import app

if __name__ == "__main__":
    print("🚀 Starting Agentic Chat Server...")
    print("=" * 50)
    print("📋 Server Information:")
    print("   - Framework: FastAPI with LangGraph")
    print("   - Architecture: Agentic (Optimized)")
    print("   - Version: 4.1.0")
    print("   - Host: 0.0.0.0")
    print("   - Port: 8000")
    print("=" * 50)
    print("🔗 Available Endpoints:")
    print("   - Root: http://localhost:8000/")
    print("   - Health: http://localhost:8000/health")
    print("   - Models: http://localhost:8000/models")
    print("   - Agents: http://localhost:8000/agents")
    print("   - Providers: http://localhost:8000/providers")
    print("   - Performance: http://localhost:8000/performance")
    print("   - Chat: http://localhost:8000/chat")
    print("   - File Upload: http://localhost:8000/file/upload")
    print("   - API Docs: http://localhost:8000/docs")
    print("=" * 50)
    print("🤖 Available Agents:")
    print("   - ChatAgent: Main conversation orchestrator (with parallel processing)")
    print("   - FileAgent: Document and file processing")
    print("   - SearchAgent: Web search and information retrieval")
    print("   - ImageAgent: Image generation and processing")
    print("=" * 50)
    print("🔧 Available Providers (Optimized):")
    print("   - OpenAI: GPT-4o, GPT-4o-mini, GPT-4-turbo (with caching & pooling)")
    print("   - Anthropic: Claude 3.5 Sonnet, Claude 3.5 Haiku (with caching & pooling)")
    print("   - Google: Gemini 1.5 Pro, Gemini 1.5 Flash (with caching & pooling)")
    print("   - Mistral: Mistral Large, Mistral Small (with caching & pooling)")
    print("=" * 50)
    print("🌐 Starting server...")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
