# Agentic Chat API with LangGraph

A modern, agentic AI chat API built with FastAPI and LangGraph, featuring specialized agents for different tasks and multi-provider LLM support.

## 🏗️ Architecture

This system uses an **agentic architecture** where specialized agents handle different aspects of conversation and processing:

- **ChatAgent**: Main conversation orchestrator
- **FileAgent**: Document and file processing specialist
- **SearchAgent**: Web search and information retrieval specialist
- **ImageAgent**: Image generation and processing specialist

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file with your API keys:

```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
MISTRAL_API_KEY=your_mistral_key
```

### 3. Run the Server

```bash
python start_server.py
```

Or directly with uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test the Server

```bash
python test_server.py
```

## 📡 API Endpoints

### Core Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check with system status
- `GET /models` - List available models
- `GET /agents` - List available agents
- `GET /providers` - List available providers

### Chat Endpoints

- `POST /chat` - Main chat endpoint with agentic processing
- `POST /agents/{agent_name}` - Direct agent access
- `POST /file/upload` - File upload endpoint

### Legacy Endpoints (for backward compatibility)

- `GET /tools/search` - Web search tool
- `POST /tools/image` - Image generation tool

## 🤖 Agents

### ChatAgent
- **Purpose**: Main conversation orchestrator
- **Capabilities**: 
  - Routes requests to appropriate agents
  - Coordinates multi-agent workflows
  - Synthesizes responses from multiple sources
  - Handles streaming responses

### FileAgent
- **Purpose**: Document and file processing specialist
- **Capabilities**:
  - Processes PDF, DOCX, CSV, JSON files
  - Analyzes code files
  - Extracts and summarizes content
  - Handles image analysis

### SearchAgent
- **Purpose**: Web search and information retrieval specialist
- **Capabilities**:
  - Performs web searches
  - Analyzes search results
  - Fetches and processes web content
  - Generates citations and summaries

### ImageAgent
- **Purpose**: Image generation and processing specialist
- **Capabilities**:
  - Generates images from text prompts
  - Processes and analyzes images
  - Optimizes prompts for better results
  - Handles multiple image formats

## 🔧 Providers

### OpenAI
- **Models**: GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo
- **Features**: Vision, tools, streaming
- **Best for**: General conversation, complex reasoning

### Anthropic
- **Models**: Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus
- **Features**: Vision, tools, large context
- **Best for**: Analysis, writing, coding

### Google
- **Models**: Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini 2.0 Flash
- **Features**: Vision, tools, massive context
- **Best for**: Research, analysis, multimodal tasks

### Mistral
- **Models**: Mistral Large, Mistral Small, Mistral Nemo
- **Features**: Tools, efficient processing
- **Best for**: Fast responses, cost-effective processing

## 🛠️ Tools

The system includes a comprehensive set of tools:

### LLM Tools
- `LLMProviderTool`: Interface with LLM providers
- `ConversationTool`: Manage conversation history
- `ResponseSynthesisTool`: Combine multiple responses

### File Tools
- `DocumentProcessorTool`: Process various document types
- `ImageAnalysisTool`: Analyze images and extract information
- `CodeAnalysisTool`: Analyze code files

### Web Tools
- `WebSearchTool`: Perform web searches
- `URLFetcherTool`: Fetch content from URLs
- `SearchResultAnalyzerTool`: Analyze search results

### Image Tools
- `ImageGenerationTool`: Generate images from prompts
- `ImageProcessingTool`: Process and manipulate images
- `ImageAnalysisTool`: Analyze image content

## 📊 State Management

The system uses LangGraph for state management with specialized state types:

- `ChatState`: Main conversation state
- `FileState`: File processing state
- `SearchState`: Web search state
- `ImageState`: Image generation state

## 🔄 Workflow

1. **Request Reception**: FastAPI receives the request
2. **Agent Selection**: ChatAgent determines which agents to use
3. **Tool Execution**: Agents execute appropriate tools
4. **State Management**: LangGraph manages state transitions
5. **Response Synthesis**: Final response is synthesized
6. **Streaming**: Response is streamed back to client

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_server.py
```

This tests:
- All imports and dependencies
- Server endpoints
- Agent initialization
- Provider initialization
- Basic functionality

## 📝 Configuration

Configuration is managed through:

- `config/settings.py`: Environment settings
- `config/models.py`: Model configurations
- `config/agents.py`: Agent configurations

## 🚀 Deployment

The server is ready for production deployment with:

- FastAPI for high-performance API
- Uvicorn ASGI server
- Comprehensive error handling
- Health checks and monitoring
- CORS support for frontend integration

## 🔒 Security

- Input validation and sanitization
- File type and size restrictions
- API key management
- Error handling without information leakage

## 📈 Performance

- Async/await throughout
- Streaming responses
- Efficient state management
- Provider failover and retry logic
- Caching and optimization

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass

## 📄 License

This project is part of the chatbot system and follows the same licensing terms.
