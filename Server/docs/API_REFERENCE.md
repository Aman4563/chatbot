# API Reference

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the API does not require authentication. In production, implement proper authentication mechanisms.

## Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

### Chat
```http
POST /chat
```

**Request Body:**
```json
{
  "message": "Hello, how are you?",
  "conversation_id": "optional-conversation-id",
  "provider": "openai",
  "model": "gpt-4",
  "stream": false,
  "attachments": []
}
```

**Response:**
```json
{
  "response": "Hello! I'm doing well, thank you for asking.",
  "conversation_id": "generated-conversation-id",
  "provider_used": "openai",
  "model_used": "gpt-4",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Providers
```http
GET /providers
```

**Response:**
```json
{
  "providers": {
    "openai": {
      "name": "OpenAI",
      "models": ["gpt-4", "gpt-3.5-turbo"],
      "available": true
    },
    "anthropic": {
      "name": "Anthropic",
      "models": ["claude-3-5-sonnet", "claude-3-haiku"],
      "available": true
    }
  }
}
```

### Conversations

#### List Conversations
```http
GET /conversations
```

#### Get Conversation
```http
GET /conversations/{conversation_id}
```

#### Update Conversation Title
```http
PUT /conversations/{conversation_id}/title
```

**Request Body:**
```json
{
  "title": "New Conversation Title"
}
```

#### Delete Conversation
```http
DELETE /conversations/{conversation_id}
```

### File Upload
```http
POST /upload
```

**Request:** Multipart form data with file

**Response:**
```json
{
  "file_id": "generated-file-id",
  "filename": "document.pdf",
  "size": 1024,
  "mime_type": "application/pdf"
}
```

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "status_code": 400
}
```

## Rate Limiting

- Chat endpoint: 60 requests per minute per IP
- File upload: 10 requests per minute per IP
- Other endpoints: 100 requests per minute per IP

## WebSocket Support

For real-time streaming responses:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.send(JSON.stringify({
  message: "Hello",
  conversation_id: "optional-id"
}));
```
