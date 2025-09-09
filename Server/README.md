# AI Chatbot Backend

A sophisticated AI chatbot backend built with FastAPI, featuring agentic architecture with LangGraph, multi-provider LLM support, and comprehensive web search capabilities.

## 🏗️ Architecture

This backend implements an agentic architecture with specialized agents for different tasks:

- **ChatAgent**: Main conversation orchestrator
- **SearchAgent**: Web search and information retrieval
- **FileAgent**: Document processing and analysis
- **ImageAgent**: Image generation and analysis

## 📁 Project Structure

```
Server/
├── agents/                 # Agent implementations
│   ├── base.py            # Base agent class
│   ├── chat_agent.py      # Main conversation agent
│   ├── search_agent.py    # Web search agent
│   ├── file_agent.py      # File processing agent
│   └── image_agent.py     # Image generation agent
├── assets/                # Static assets (images, etc.)
├── config/                # Configuration files
├── data/                  # Data storage
│   ├── conversations/     # Conversation history
│   └── daily_usage.json   # Usage statistics
├── docs/                  # Documentation
├── examples/              # Example scripts
├── graphs/                # LangGraph state definitions
├── logs/                  # Log files
├── providers/             # LLM provider implementations
├── schemas/               # Pydantic models
├── services/              # Business logic services
├── tools/                 # Agent tools and utilities
├── utils/                 # Utility functions
├── main.py               # FastAPI application
└── start_server.py       # Server startup script
```

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   # Required for LLM providers
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   export GOOGLE_API_KEY="your-google-key"
   export MISTRAL_API_KEY="your-mistral-key"
   
   # Optional for web search
   export GOOGLE_SEARCH_API_KEY="your-google-search-key"
   export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"
   ```

3. **Start the Server**:
   ```bash
   python start_server.py
   ```

4. **Access the API**:
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 🔧 Features

### Core Capabilities
- **Multi-Provider LLM Support**: OpenAI, Anthropic, Google, Mistral
- **Web Search Integration**: DuckDuckGo, Google Custom Search
- **Document Processing**: PDF, DOCX, TXT file analysis
- **Image Generation**: DALL-E integration
- **Real-time Streaming**: SSE support for live responses

### Advanced Features
- **Agent Collaboration**: Multi-agent workflows
- **Context Management**: Conversation history and context
- **Legal Compliance**: Robots.txt checking, content limits
- **Performance Optimization**: Caching, rate limiting
- **Error Handling**: Graceful fallbacks and retries

## 📚 Documentation

- [Architecture Overview](docs/architecture_diagrams.md)
- [Agent Communication](docs/AGENT_COMMUNICATION_README.md)
- [Conversation Context](docs/CONVERSATION_CONTEXT_IMPLEMENTATION.md)
- [Performance Optimization](docs/PERFORMANCE_OPTIMIZATION_README.md)
- [Legal Compliance](docs/LEGAL_COMPLIANCE_GUIDE.md)

## 🛠️ Development

### Running Examples
```bash
# Enhanced web search example
python examples/enhanced_search_example.py
```

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .
```

## 📊 API Endpoints

### Core Endpoints
- `POST /chat` - Main chat endpoint
- `GET /health` - Health check
- `GET /providers` - Available LLM providers

### Conversation Management
- `GET /conversations` - List conversations
- `GET /conversations/{id}` - Get conversation
- `PUT /conversations/{id}/title` - Update title
- `DELETE /conversations/{id}` - Delete conversation

### File Operations
- `POST /upload` - Upload files
- `GET /files/{id}` - Get file info

## 🔒 Security & Compliance

- **API Key Management**: Secure environment variable handling
- **Content Limits**: Fair use compliance for web scraping
- **Robots.txt Compliance**: Respects website crawling policies
- **Rate Limiting**: Prevents API abuse
- **Input Validation**: Comprehensive request validation

## 📈 Monitoring

- **Health Checks**: Built-in health monitoring
- **Usage Statistics**: Daily usage tracking
- **Error Logging**: Comprehensive error tracking
- **Performance Metrics**: Response time monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
