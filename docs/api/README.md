# API Documentation

This directory contains API documentation for the Concert Data Platform.

## Overview

The platform provides REST APIs for:
- Machine Learning model inference
- Chatbot interactions
- Data analysis requests
- Recommendation queries

## API Documentation

### Production API (API Gateway)

**[API Gateway Reference](API_GATEWAY_REFERENCE.md)** - Complete endpoint reference for production API

**[API Gateway Setup Guide](../infrastructure/API_GATEWAY_SETUP_GUIDE.md)** - Deployment and configuration guide

**Base URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}`

**Features**:
- CORS enabled for all endpoints
- Throttling: 500 req/sec, burst 1000
- Request/response validation
- CloudWatch logging and X-Ray tracing

### Development APIs

**Chatbot API**: `src/api/chatbot_api.py`
- Local development server
- Interactive docs at `/docs`
- Base URL: `http://localhost:8000`

**ML API**: `src/api/ml_api.py`
- Direct ML model access
- Base URL: `http://localhost:8000/ml`

## API Endpoints

### Chatbot Endpoints
- `POST /chat` - Send chat messages and receive responses
- `GET /history/{session_id}` - Retrieve conversation history
- `POST /sessions` - Create new conversation session
- `GET /health` - Health check

### Analytics Endpoints
- `GET /venues/popularity` - Get venue popularity rankings
- `POST /predictions/tickets` - Predict ticket sales
- `GET /recommendations` - Get concert recommendations
- `GET /venues/{venue_id}` - Get venue details
- `GET /artists/{artist_id}` - Get artist details

## Quick Start

### Using API Gateway (Production)

```bash
# Deploy API Gateway
./infrastructure/deploy_api_gateway.sh

# Test endpoint
curl -X POST "${API_ENDPOINT}/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the top venues?"}'
```

### Using Local Development Server

```bash
# Start server
cd src/api
python run_api.py

# Test endpoint
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the top venues?"}'
```

## Authentication

APIs use AWS IAM authentication and API keys for secure access.

### API Gateway
- API keys (optional)
- AWS IAM authentication
- Throttling and rate limiting

### Development Server
- No authentication (development only)
- Configure for production use

## Monitoring

### API Gateway
- CloudWatch Metrics (4XX, 5XX, latency)
- CloudWatch Logs
- X-Ray tracing

### Development Server
- Structured logging with structlog
- Custom metrics tracking

## Related Documentation

- **[API Gateway Reference](API_GATEWAY_REFERENCE.md)** - Complete endpoint documentation
- **[API Gateway Setup Guide](../infrastructure/API_GATEWAY_SETUP_GUIDE.md)** - Deployment guide
- [Feature Summaries](../features/) - Feature capabilities
- [Services](../services/) - Service implementation
- [Guides](../guides/) - Usage tutorials
- [Infrastructure](../infrastructure/) - Infrastructure setup

## Validation

```bash
# Validate API Gateway setup
python validate_api_gateway_setup.py

# Validate chatbot API
python validate_chatbot_api.py

# Test API integration
python src/api/example_api_usage.py
```

---

[← Back to Documentation Index](../DOCUMENTATION_INDEX.md)
