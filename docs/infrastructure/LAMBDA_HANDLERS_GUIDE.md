# Lambda Handlers Guide

## Overview

This guide covers the AWS Lambda function handlers that power the Concert Data Platform API endpoints. These serverless functions provide scalable, cost-effective API processing for chatbot interactions, ML predictions, and data queries.

## Architecture

```
API Gateway → Lambda Functions → AWS Services
                ├── Bedrock Agent (Chatbot)
                ├── Redshift Data API (Queries)
                ├── SageMaker Runtime (Predictions)
                └── CloudWatch Logs (Monitoring)
```

## Lambda Functions

### 1. Chatbot Handler

**Function Name:** `concert-api-chatbot`  
**Handler:** `api_lambda_handlers.chatbot_handler`  
**Endpoint:** `POST /chat`

Processes chatbot messages using AWS Bedrock Agent Runtime.

**Request:**
```json
{
  "message": "Tell me about popular artists",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id"
}
```

**Response:**
```json
{
  "message": "Here are the popular artists...",
  "session_id": "abc-123",
  "intent": "artist_lookup",
  "confidence": 0.9,
  "data": {},
  "suggestions": ["Show me venues", "Recommend concerts"],
  "timestamp": "2025-11-11T15:30:00Z"
}
```

**Environment Variables:**
- `BEDROCK_AGENT_ID`: AWS Bedrock Agent ID
- `BEDROCK_AGENT_ALIAS_ID`: Agent alias ID
- `REDSHIFT_CLUSTER_ID`: Redshift cluster identifier
- `REDSHIFT_DATABASE`: Database name

**IAM Permissions Required:**
- `bedrock:InvokeAgent`
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

### 2. Venue Popularity Handler

**Function Name:** `concert-api-venue-popularity`  
**Handler:** `api_lambda_handlers.venue_popularity_handler`  
**Endpoint:** `POST /venues/popularity`

Queries venue popularity rankings from Redshift.

**Request:**
```json
{
  "top_n": 10,
  "min_events": 5
}
```

**Response:**
```json
{
  "venues": [
    {
      "venue_id": "venue_001",
      "name": "Madison Square Garden",
      "city": "New York",
      "state": "NY",
      "capacity": 20000,
      "venue_type": "arena",
      "total_concerts": 150,
      "avg_attendance_rate": 0.95,
      "revenue_per_event": 500000.0,
      "booking_frequency": 12.5,
      "popularity_rank": 1
    }
  ],
  "total_venues": 10,
  "timestamp": "2025-11-11T15:30:00Z"
}
```

**Environment Variables:**
- `REDSHIFT_CLUSTER_ID`: Redshift cluster identifier
- `REDSHIFT_DATABASE`: Database name

**IAM Permissions Required:**
- `redshift-data:ExecuteStatement`
- `redshift-data:DescribeStatement`
- `redshift-data:GetStatementResult`
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

### 3. Ticket Prediction Handler

**Function Name:** `concert-api-ticket-prediction`  
**Handler:** `api_lambda_handlers.ticket_prediction_handler`  
**Endpoint:** `POST /tickets/predict`

Predicts ticket sales using SageMaker ML model.

**Request:**
```json
{
  "artist_id": "artist_001",
  "venue_id": "venue_001",
  "event_date": "2025-12-31",
  "ticket_price": 75.0
}
```

**Response:**
```json
{
  "predicted_sales": 15000.0,
  "confidence": 0.85,
  "features_used": {
    "artist_id": "artist_001",
    "venue_id": "venue_001",
    "event_date": "2025-12-31",
    "ticket_price": 75.0
  },
  "timestamp": "2025-11-11T15:30:00Z"
}
```

**Environment Variables:**
- `SAGEMAKER_TICKET_ENDPOINT`: SageMaker endpoint name
- `REDSHIFT_CLUSTER_ID`: Redshift cluster identifier (for feature extraction)
- `REDSHIFT_DATABASE`: Database name

**IAM Permissions Required:**
- `sagemaker:InvokeEndpoint`
- `redshift-data:ExecuteStatement`
- `redshift-data:DescribeStatement`
- `redshift-data:GetStatementResult`
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

### 4. Recommendations Handler

**Function Name:** `concert-api-recommendations`  
**Handler:** `api_lambda_handlers.recommendations_handler`  
**Endpoint:** `POST /recommendations`

Generates concert recommendations based on user preferences.

**Request:**
```json
{
  "user_id": "user_123",
  "artist_preferences": ["rock", "alternative"],
  "location": "New York",
  "top_n": 10
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "concert_id": "concert_001",
      "artist_name": "The Rolling Stones",
      "genre": "rock",
      "artist_popularity": 95.0,
      "venue_name": "Madison Square Garden",
      "city": "New York",
      "state": "NY",
      "capacity": 20000,
      "event_date": "2025-12-31",
      "score": 1.0,
      "reasoning": "Popular rock artist"
    }
  ],
  "total_recommendations": 10,
  "recommendation_type": "genre_filtered",
  "timestamp": "2025-11-11T15:30:00Z"
}
```

**Environment Variables:**
- `REDSHIFT_CLUSTER_ID`: Redshift cluster identifier
- `REDSHIFT_DATABASE`: Database name

**IAM Permissions Required:**
- `redshift-data:ExecuteStatement`
- `redshift-data:DescribeStatement`
- `redshift-data:GetStatementResult`
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

### 5. Health Check Handler

**Function Name:** `concert-api-health-check`  
**Handler:** `api_lambda_handlers.health_check_handler`  
**Endpoint:** `GET /health`

Returns health status of API and dependent services.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-11T15:30:00Z",
  "version": "1.0.0",
  "services": {
    "redshift": "configured",
    "bedrock_agent": "configured",
    "sagemaker_venue": "not_configured",
    "sagemaker_ticket": "configured"
  }
}
```

## Deployment

### Prerequisites

1. **AWS CLI configured** with appropriate credentials
2. **Python 3.11+** installed
3. **IAM role** for Lambda execution (or script will create one)
4. **Environment variables** set in `.env` file

### Environment Variables

Create or update `.env` file:

```bash
# AWS Configuration
AWS_REGION=us-east-1

# Redshift Configuration
REDSHIFT_CLUSTER_ID=concert-warehouse-dev
REDSHIFT_DATABASE=concert_data

# Bedrock Agent Configuration (optional)
BEDROCK_AGENT_ID=your-agent-id
BEDROCK_AGENT_ALIAS_ID=your-alias-id

# SageMaker Endpoints (optional)
SAGEMAKER_VENUE_ENDPOINT=venue-popularity-endpoint
SAGEMAKER_TICKET_ENDPOINT=ticket-sales-endpoint

# Lambda Configuration (optional)
LAMBDA_EXECUTION_ROLE_ARN=arn:aws:iam::123456789012:role/LambdaRole
LAMBDA_DEPLOYMENT_BUCKET=my-lambda-deployments
API_GATEWAY_ID=your-api-gateway-id
```

### Deployment Steps

#### Option 1: Using Shell Script (Recommended)

```bash
# Make script executable
chmod +x infrastructure/deploy_api_lambdas.sh

# Deploy all Lambda functions
./infrastructure/deploy_api_lambdas.sh
```

#### Option 2: Using Python Script

```bash
# Deploy with automatic role creation
python infrastructure/deploy_api_lambdas.py --region us-east-1

# Deploy with existing role
python infrastructure/deploy_api_lambdas.py \
  --region us-east-1 \
  --role-arn arn:aws:iam::123456789012:role/LambdaRole

# Deploy with S3 bucket for large packages
python infrastructure/deploy_api_lambdas.py \
  --region us-east-1 \
  --s3-bucket my-lambda-deployments

# Deploy with API Gateway permissions
python infrastructure/deploy_api_lambdas.py \
  --region us-east-1 \
  --api-gateway-id abc123xyz
```

### Deployment Output

```
========================================
DEPLOYMENT SUMMARY
========================================

chatbot: SUCCESS
  Function Name: concert-api-chatbot
  Function ARN: arn:aws:lambda:us-east-1:123456789012:function:concert-api-chatbot

venue-popularity: SUCCESS
  Function Name: concert-api-venue-popularity
  Function ARN: arn:aws:lambda:us-east-1:123456789012:function:concert-api-venue-popularity

ticket-prediction: SUCCESS
  Function Name: concert-api-ticket-prediction
  Function ARN: arn:aws:lambda:us-east-1:123456789012:function:concert-api-ticket-prediction

recommendations: SUCCESS
  Function Name: concert-api-recommendations
  Function ARN: arn:aws:lambda:us-east-1:123456789012:function:concert-api-recommendations

health-check: SUCCESS
  Function Name: concert-api-health-check
  Function ARN: arn:aws:lambda:us-east-1:123456789012:function:concert-api-health-check

========================================
```

## Testing

### Local Testing

Run validation script:

```bash
python validate_api_lambda_handlers.py
```

### Testing Individual Handlers

```python
from src.infrastructure.api_lambda_handlers import chatbot_handler

# Mock event and context
event = {
    'body': '{"message": "Hello"}'
}

class MockContext:
    request_id = 'test-123'

response = chatbot_handler(event, MockContext())
print(response)
```

### Testing via AWS CLI

```bash
# Invoke chatbot handler
aws lambda invoke \
  --function-name concert-api-chatbot \
  --payload '{"body": "{\"message\": \"Hello\"}"}' \
  response.json

# View response
cat response.json
```

### Testing via API Gateway

```bash
# Get API Gateway URL
API_URL=$(aws apigateway get-rest-apis \
  --query "items[?name=='ConcertAPI'].id" \
  --output text)

# Test chatbot endpoint
curl -X POST \
  "https://${API_URL}.execute-api.us-east-1.amazonaws.com/prod/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about popular artists"}'
```

## Monitoring

### CloudWatch Logs

View logs for a specific function:

```bash
# Get log group name
LOG_GROUP="/aws/lambda/concert-api-chatbot"

# View recent logs
aws logs tail $LOG_GROUP --follow
```

### CloudWatch Metrics

Key metrics to monitor:

- **Invocations**: Number of function invocations
- **Duration**: Execution time
- **Errors**: Number of errors
- **Throttles**: Number of throttled requests
- **ConcurrentExecutions**: Number of concurrent executions

### Custom Metrics

Handlers emit structured logs that can be used for custom metrics:

```json
{
  "event": "Chatbot handler invoked",
  "request_id": "abc-123",
  "level": "info",
  "timestamp": "2025-11-11T15:30:00Z"
}
```

## Error Handling

### Common Errors

#### 1. Missing Environment Variables

**Error:** Service not configured  
**Solution:** Set required environment variables in Lambda configuration

```bash
aws lambda update-function-configuration \
  --function-name concert-api-chatbot \
  --environment Variables="{BEDROCK_AGENT_ID=your-id,BEDROCK_AGENT_ALIAS_ID=your-alias}"
```

#### 2. IAM Permission Denied

**Error:** AccessDeniedException  
**Solution:** Add required permissions to Lambda execution role

```bash
aws iam attach-role-policy \
  --role-name ConcertAPILambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

#### 3. Timeout Errors

**Error:** Task timed out after X seconds  
**Solution:** Increase function timeout

```bash
aws lambda update-function-configuration \
  --function-name concert-api-venue-popularity \
  --timeout 60
```

#### 4. Memory Errors

**Error:** Runtime exited with error: signal: killed  
**Solution:** Increase function memory

```bash
aws lambda update-function-configuration \
  --function-name concert-api-ticket-prediction \
  --memory-size 1024
```

### Error Response Format

All handlers return standardized error responses:

```json
{
  "error": "Error message",
  "details": "Detailed error information",
  "timestamp": "2025-11-11T15:30:00Z"
}
```

## Performance Optimization

### Cold Start Optimization

1. **Minimize package size**: Only include necessary dependencies
2. **Use Lambda layers**: Share common dependencies across functions
3. **Provisioned concurrency**: Keep functions warm for critical endpoints

```bash
aws lambda put-provisioned-concurrency-config \
  --function-name concert-api-chatbot \
  --provisioned-concurrent-executions 2 \
  --qualifier LATEST
```

### Memory Configuration

Recommended memory settings:

- **Chatbot**: 512 MB (handles Bedrock Agent calls)
- **Venue Popularity**: 512 MB (processes Redshift queries)
- **Ticket Prediction**: 512 MB (SageMaker invocations)
- **Recommendations**: 512 MB (complex queries)
- **Health Check**: 256 MB (simple status check)

### Timeout Configuration

Recommended timeout settings:

- **Chatbot**: 30 seconds
- **Venue Popularity**: 60 seconds (complex queries)
- **Ticket Prediction**: 30 seconds
- **Recommendations**: 60 seconds (complex queries)
- **Health Check**: 10 seconds

## Security Best Practices

### 1. Least Privilege IAM Policies

Create custom policies with minimal permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeAgent"
      ],
      "Resource": "arn:aws:bedrock:*:*:agent/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "redshift-data:ExecuteStatement",
        "redshift-data:DescribeStatement",
        "redshift-data:GetStatementResult"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. Environment Variable Encryption

Encrypt sensitive environment variables:

```bash
aws lambda update-function-configuration \
  --function-name concert-api-chatbot \
  --kms-key-arn arn:aws:kms:us-east-1:123456789012:key/your-key-id
```

### 3. VPC Configuration

For enhanced security, deploy Lambda functions in VPC:

```bash
aws lambda update-function-configuration \
  --function-name concert-api-chatbot \
  --vpc-config SubnetIds=subnet-123,subnet-456,SecurityGroupIds=sg-789
```

### 4. API Gateway Authorization

Configure API Gateway with:
- API keys
- IAM authorization
- Cognito user pools
- Lambda authorizers

## Troubleshooting

### Debug Mode

Enable detailed logging:

```python
import os
os.environ['LOG_LEVEL'] = 'DEBUG'
```

### Common Issues

1. **Handler not found**: Check handler path in function configuration
2. **Import errors**: Ensure all dependencies are in deployment package
3. **Timeout**: Increase timeout or optimize query performance
4. **Memory**: Monitor memory usage and increase if needed

### Support

For issues or questions:
1. Check CloudWatch Logs for error details
2. Review validation script output
3. Consult AWS Lambda documentation
4. Contact platform team

## Next Steps

1. **Configure API Gateway**: Set up routes to Lambda functions
2. **Set up monitoring**: Create CloudWatch dashboards and alarms
3. **Load testing**: Test functions under expected load
4. **Documentation**: Update API documentation with endpoint details
