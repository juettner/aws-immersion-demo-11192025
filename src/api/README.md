# Concert AI Chatbot API

REST API for the Concert AI Chatbot service, providing HTTP endpoints for chatbot interactions, conversation management, and session handling.

## Features

- **Chat Endpoints**: Send messages and receive AI-powered responses
- **Session Management**: Create, retrieve, and delete conversation sessions
- **Conversation History**: Access and manage conversation history
- **Streaming Support**: Real-time streaming responses (Server-Sent Events)
- **Health Monitoring**: Health check and statistics endpoints
- **CORS Support**: Configured for cross-origin requests
- **Auto-generated Documentation**: Interactive API docs with Swagger UI

## Quick Start

### Installation

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Running the API Server

**Option 1: Using the run script (recommended)**
```bash
python src/api/run_api.py
```

**Option 2: Using uvicorn directly**
```bash
uvicorn src.api.chatbot_api:app --host 0.0.0.0 --port 8000 --reload
```

**Option 3: Running the module directly**
```bash
python -m src.api.chatbot_api
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, access the interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Core Endpoints

#### `GET /`
Root endpoint with API information.

#### `GET /health`
Health check endpoint returning service status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-10T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "chatbot": "healthy",
    "memory": "healthy",
    "nl_to_sql": "healthy",
    "data_analysis": "healthy",
    "redshift": "unavailable"
  }
}
```

### Chat Endpoints

#### `POST /chat`
Send a message to the chatbot and receive a response.

**Request:**
```json
{
  "message": "What are the most popular venues?",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id",
  "stream": false
}
```

**Response:**
```json
{
  "message": "Based on our data, the top venues are...",
  "session_id": "abc123",
  "intent": "venue_search",
  "confidence": 0.95,
  "data": {...},
  "suggestions": ["Show me concerts", "Ticket predictions"],
  "timestamp": "2024-11-10T12:00:00Z"
}
```

#### `POST /chat/stream`
Send a message with streaming response (Server-Sent Events).

**Request:** Same as `/chat`

**Response:** Stream of events with incremental content

### Session Management

#### `POST /sessions`
Create a new conversation session.

**Request:**
```json
{
  "user_id": "optional-user-id"
}
```

**Response:**
```json
{
  "session_id": "abc123",
  "user_id": "user123",
  "created_at": "2024-11-10T12:00:00Z",
  "message_count": 0
}
```

#### `GET /sessions/{session_id}`
Get session information.

**Response:**
```json
{
  "session_id": "abc123",
  "user_id": "user123",
  "created_at": "2024-11-10T12:00:00Z",
  "message_count": 5
}
```

#### `DELETE /sessions/{session_id}`
Delete a conversation session.

**Response:** 204 No Content

### Conversation History

#### `GET /history/{session_id}`
Get conversation history for a session.

**Query Parameters:**
- `limit` (optional): Maximum number of messages to return

**Response:**
```json
{
  "session_id": "abc123",
  "messages": [
    {
      "message_id": "msg1",
      "role": "user",
      "content": "Hello",
      "timestamp": "2024-11-10T12:00:00Z",
      "metadata": {}
    },
    {
      "message_id": "msg2",
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": "2024-11-10T12:00:01Z",
      "metadata": {}
    }
  ],
  "total_messages": 2
}
```

#### `DELETE /history/{session_id}`
Clear conversation history for a session.

**Response:** 204 No Content

### Session Context

#### `GET /sessions/{session_id}/context`
Get session context information.

**Response:**
```json
{
  "session_id": "abc123",
  "context": {
    "last_venue": "Madison Square Garden",
    "preferred_genre": "Rock"
  },
  "current_intent": "venue_search",
  "updated_at": "2024-11-10T12:00:00Z"
}
```

#### `PUT /sessions/{session_id}/context`
Update session context.

**Request:**
```json
{
  "preferred_genre": "Pop",
  "location": "New York"
}
```

**Response:**
```json
{
  "message": "Context updated successfully"
}
```

### Statistics

#### `GET /stats`
Get chatbot service statistics.

**Response:**
```json
{
  "total_sessions": 10,
  "total_messages": 50,
  "average_messages_per_session": 5.0,
  "intent_distribution": {
    "venue_search": 5,
    "artist_lookup": 3,
    "concert_recommendation": 2
  },
  "memory_service": {
    "conversations_table": "concert-chatbot-conversations",
    "preferences_table": "concert-chatbot-preferences",
    "dynamodb_available": true,
    "total_messages": 50,
    "total_users_with_preferences": 5
  }
}
```

## Usage Examples

### Python Client

```python
import requests

# Create a session
response = requests.post("http://localhost:8000/sessions")
session_id = response.json()["session_id"]

# Send a message
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "What are the most popular venues?",
        "session_id": session_id
    }
)
print(response.json()["message"])

# Get conversation history
response = requests.get(f"http://localhost:8000/history/{session_id}")
print(response.json())
```

### JavaScript/TypeScript Client

```typescript
// Create a session
const sessionResponse = await fetch('http://localhost:8000/sessions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({})
});
const { session_id } = await sessionResponse.json();

// Send a message
const chatResponse = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'What are the most popular venues?',
    session_id
  })
});
const data = await chatResponse.json();
console.log(data.message);
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/health

# Create session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo_user"}'

# Send message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the most popular venues?",
    "session_id": "your-session-id"
  }'

# Get conversation history
curl http://localhost:8000/history/your-session-id
```

## Testing

Run the validation script to test all endpoints:

```bash
python validate_chatbot_api.py
```

Run the example usage script:

```bash
# Start the API server first
python src/api/run_api.py

# In another terminal, run the example
python src/api/example_api_usage.py
```

## Configuration

The API uses settings from `src/config/settings.py`, which loads from environment variables:

```bash
# AWS Configuration
export AWS_REGION=us-east-1
export AWS_REDSHIFT_CLUSTER_ID=concert-warehouse

# API Configuration
export API_SPOTIFY_CLIENT_ID=your_client_id
export API_SPOTIFY_CLIENT_SECRET=your_client_secret
export API_TICKETMASTER_API_KEY=your_api_key

# DynamoDB Tables
export AWS_DYNAMODB_CONVERSATIONS_TABLE=concert-chatbot-conversations
export AWS_DYNAMODB_PREFERENCES_TABLE=concert-chatbot-preferences
```

## CORS Configuration

The API is configured to allow all origins by default for development. For production, update the CORS settings in `chatbot_api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "timestamp": "2024-11-10T12:00:00Z"
}
```

Common HTTP status codes:
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `204 No Content`: Successful deletion
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Development

### Project Structure

```
src/api/
├── __init__.py
├── chatbot_api.py          # Main FastAPI application
├── run_api.py              # Startup script
├── example_api_usage.py    # Usage examples
└── README.md               # This file
```

### Adding New Endpoints

1. Define request/response models using Pydantic
2. Add endpoint function with appropriate decorators
3. Update documentation
4. Add tests to validation script

## Deployment

### Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
EXPOSE 8000

CMD ["uvicorn", "src.api.chatbot_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t concert-chatbot-api .
docker run -p 8000:8000 concert-chatbot-api
```

### AWS Lambda

The API can be deployed to AWS Lambda using Mangum:

```bash
pip install mangum
```

Create a Lambda handler:

```python
from mangum import Mangum
from src.api.chatbot_api import app

handler = Mangum(app)
```

## License

Part of the Concert Data Platform - AWS Data Readiness & AI Demo
