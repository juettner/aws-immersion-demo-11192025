# API Gateway Reference

Quick reference for Concert AI Platform API Gateway endpoints.

## Base URL

```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}
```

Example:
```
https://abc123xyz.execute-api.us-east-1.amazonaws.com/development
```

## Authentication

### API Key (Optional)

Include API key in request header:

```
X-Api-Key: your-api-key-here
```

## Endpoints

### Chatbot Endpoints

#### POST /chat

Send a chat message and receive a response.

**Request:**
```json
{
  "message": "What are the top venues?",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id",
  "stream": false
}
```

**Response:**
```json
{
  "message": "Here are the top venues...",
  "session_id": "session-123",
  "intent": "venue_query",
  "confidence": 0.95,
  "data": {
    "venues": [...]
  },
  "suggestions": [
    "Tell me more about venue X",
    "Show me upcoming concerts"
  ],
  "timestamp": "2025-11-11T12:00:00Z"
}
```

**cURL Example:**
```bash
curl -X POST "${API_ENDPOINT}/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the top venues?",
    "session_id": "test-session"
  }'
```

---

#### GET /history/{session_id}

Retrieve conversation history for a session.

**Parameters:**
- `session_id` (path, required): Session identifier
- `limit` (query, optional): Maximum number of messages

**Response:**
```json
{
  "session_id": "session-123",
  "messages": [
    {
      "message_id": "msg-1",
      "role": "user",
      "content": "Hello",
      "timestamp": "2025-11-11T12:00:00Z",
      "metadata": {}
    },
    {
      "message_id": "msg-2",
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": "2025-11-11T12:00:01Z",
      "metadata": {}
    }
  ],
  "total_messages": 2
}
```

**cURL Example:**
```bash
curl -X GET "${API_ENDPOINT}/history/session-123?limit=10"
```

---

### Analytics Endpoints

#### GET /venues/popularity

Get venue popularity rankings.

**Query Parameters:**
- `top_n` (optional, default: 10): Number of venues to return
- `min_events` (optional, default: 5): Minimum events for ranking

**Response:**
```json
{
  "venues": [
    {
      "venue_id": "venue-1",
      "name": "Madison Square Garden",
      "popularity_score": 95.5,
      "total_events": 150,
      "avg_attendance": 18000,
      "city": "New York",
      "state": "NY"
    }
  ],
  "total_venues": 10,
  "timestamp": "2025-11-11T12:00:00Z"
}
```

**cURL Example:**
```bash
curl -X GET "${API_ENDPOINT}/venues/popularity?top_n=5"
```

---

#### POST /predictions/tickets

Predict ticket sales for a concert.

**Request:**
```json
{
  "artist_id": "artist-123",
  "venue_id": "venue-456",
  "event_date": "2025-12-31",
  "ticket_price": 75.00
}
```

**Response:**
```json
{
  "predicted_sales": 15000,
  "confidence": 0.85,
  "features_used": {
    "artist_id": "artist-123",
    "venue_id": "venue-456",
    "event_date": "2025-12-31",
    "ticket_price": 75.00
  },
  "timestamp": "2025-11-11T12:00:00Z"
}
```

**cURL Example:**
```bash
curl -X POST "${API_ENDPOINT}/predictions/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_id": "artist-123",
    "venue_id": "venue-456",
    "event_date": "2025-12-31"
  }'
```

---

#### GET /recommendations

Get concert recommendations.

**Query Parameters:**
- `user_id` (optional): User identifier for personalization
- `artist_preferences` (optional): Comma-separated genres
- `location` (optional): Preferred location
- `top_n` (optional, default: 10): Number of recommendations

**Response:**
```json
{
  "recommendations": [
    {
      "concert_id": "concert-789",
      "artist_name": "The Rolling Stones",
      "venue_name": "Madison Square Garden",
      "event_date": "2025-12-31",
      "score": 0.92,
      "reason": "Based on your listening history"
    }
  ],
  "total_recommendations": 10,
  "recommendation_type": "hybrid",
  "timestamp": "2025-11-11T12:00:00Z"
}
```

**cURL Example:**
```bash
curl -X GET "${API_ENDPOINT}/recommendations?user_id=user-123&top_n=5"
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "timestamp": "2025-11-11T12:00:00Z"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid API key |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## Rate Limits

- **Rate Limit**: 500 requests per second
- **Burst Limit**: 1000 requests
- **Daily Quota**: 100,000 requests

When rate limit is exceeded, you'll receive a `429 Too Many Requests` response with a `Retry-After` header.

---

## CORS

All endpoints support CORS with the following configuration:

- **Allowed Origins**: `*` (configure for production)
- **Allowed Methods**: `GET, POST, PUT, DELETE, OPTIONS`
- **Allowed Headers**: `Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token`

---

## Request/Response Headers

### Common Request Headers

```
Content-Type: application/json
X-Api-Key: your-api-key (optional)
Authorization: Bearer token (if using auth)
```

### Common Response Headers

```
Content-Type: application/json
Access-Control-Allow-Origin: *
X-Amzn-RequestId: request-id
X-Amzn-Trace-Id: trace-id
```

---

## Testing with Postman

### Import Collection

1. Create a new collection in Postman
2. Set base URL as environment variable: `{{API_ENDPOINT}}`
3. Add requests for each endpoint
4. Set headers: `Content-Type: application/json`

### Example Environment

```json
{
  "API_ENDPOINT": "https://abc123xyz.execute-api.us-east-1.amazonaws.com/development",
  "API_KEY": "your-api-key-here",
  "SESSION_ID": "test-session-123"
}
```

---

## Testing with Python

```python
import requests

API_ENDPOINT = "https://abc123xyz.execute-api.us-east-1.amazonaws.com/development"

# Chat endpoint
response = requests.post(
    f"{API_ENDPOINT}/chat",
    json={
        "message": "What are the top venues?",
        "session_id": "test-session"
    }
)
print(response.json())

# Venue popularity
response = requests.get(
    f"{API_ENDPOINT}/venues/popularity",
    params={"top_n": 5}
)
print(response.json())

# Ticket prediction
response = requests.post(
    f"{API_ENDPOINT}/predictions/tickets",
    json={
        "artist_id": "artist-123",
        "venue_id": "venue-456",
        "event_date": "2025-12-31"
    }
)
print(response.json())

# Recommendations
response = requests.get(
    f"{API_ENDPOINT}/recommendations",
    params={"user_id": "user-123", "top_n": 5}
)
print(response.json())
```

---

## Testing with JavaScript/TypeScript

```typescript
const API_ENDPOINT = "https://abc123xyz.execute-api.us-east-1.amazonaws.com/development";

// Chat endpoint
const chatResponse = await fetch(`${API_ENDPOINT}/chat`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: "What are the top venues?",
    session_id: "test-session",
  }),
});
const chatData = await chatResponse.json();

// Venue popularity
const venuesResponse = await fetch(
  `${API_ENDPOINT}/venues/popularity?top_n=5`
);
const venuesData = await venuesResponse.json();

// Ticket prediction
const predictionResponse = await fetch(
  `${API_ENDPOINT}/predictions/tickets`,
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      artist_id: "artist-123",
      venue_id: "venue-456",
      event_date: "2025-12-31",
    }),
  }
);
const predictionData = await predictionResponse.json();

// Recommendations
const recsResponse = await fetch(
  `${API_ENDPOINT}/recommendations?user_id=user-123&top_n=5`
);
const recsData = await recsResponse.json();
```

---

## Monitoring

### CloudWatch Metrics

Monitor these metrics in CloudWatch:

- `4XXError` - Client errors
- `5XXError` - Server errors
- `Count` - Total requests
- `Latency` - Response time
- `IntegrationLatency` - Backend latency

### CloudWatch Logs

View logs:

```bash
aws logs tail /aws/apigateway/concert-ai-development --follow
```

### X-Ray Tracing

View request traces in AWS X-Ray console for detailed performance analysis.

---

## Related Documentation

- [API Gateway Setup Guide](../infrastructure/API_GATEWAY_SETUP_GUIDE.md)
- [Chatbot API Documentation](../../src/api/chatbot_api.py)
- [ML API Documentation](../../src/api/ml_api.py)

---

## Support

For issues or questions:
1. Check CloudWatch logs for errors
2. Review X-Ray traces for performance issues
3. Validate API Gateway configuration
4. Contact support team
