# API Gateway Setup Guide

## Overview

This guide covers the setup and configuration of AWS API Gateway for the Concert AI Platform. The API Gateway provides a unified REST API interface for the chatbot and analytics services.

## Architecture

The API Gateway serves as the entry point for all client requests, routing them to appropriate Lambda functions:

```
Client → API Gateway → Lambda Functions → Backend Services
```

### Endpoints

#### Chatbot Endpoints
- `POST /chat` - Send chat messages and receive responses
- `GET /history/{session_id}` - Retrieve conversation history

#### Analytics Endpoints
- `GET /venues/popularity` - Get venue popularity rankings
- `POST /predictions/tickets` - Predict ticket sales
- `GET /recommendations` - Get concert recommendations

## Features

### CORS Configuration
- **Enabled for all endpoints**
- Allows origins: `*` (configure for production)
- Allowed methods: `GET, POST, PUT, DELETE, OPTIONS`
- Allowed headers: `Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token`

### Throttling and Rate Limiting
- **Burst Limit**: 1000 requests
- **Rate Limit**: 500 requests per second
- **Quota**: 100,000 requests per day

### Request/Response Validation
- JSON schema validation for request bodies
- Required field validation
- Type checking and format validation

### Monitoring and Logging
- CloudWatch Logs integration
- X-Ray tracing enabled
- Metrics for all endpoints
- Custom CloudWatch dashboards

## Deployment Methods

### Method 1: CloudFormation (Recommended)

Deploy using the CloudFormation template for production environments:

```bash
# Set environment variables
export ENVIRONMENT=development
export AWS_REGION=us-east-1

# Deploy using the script
./infrastructure/deploy_api_gateway.sh
```

Or deploy directly with AWS CLI:

```bash
aws cloudformation deploy \
  --template-file infrastructure/api_gateway_config.yaml \
  --stack-name concert-ai-api-gateway-development \
  --parameter-overrides \
      Environment=development \
      ChatbotLambdaArn=arn:aws:lambda:us-east-1:123456789012:function:chatbot \
      VenuePopularityLambdaArn=arn:aws:lambda:us-east-1:123456789012:function:venue-popularity \
      TicketPredictionLambdaArn=arn:aws:lambda:us-east-1:123456789012:function:ticket-prediction \
      RecommendationLambdaArn=arn:aws:lambda:us-east-1:123456789012:function:recommendation \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

### Method 2: Python Script

Deploy using the Python setup script for development:

```bash
python3 infrastructure/setup_api_gateway.py \
  --environment development \
  --region us-east-1
```

### Method 3: Programmatic Setup

Use the API Gateway client in your own scripts:

```python
from infrastructure.api_gateway_client import APIGatewayClient

client = APIGatewayClient(region="us-east-1")

# Create REST API
api = client.create_rest_api(
    name="concert-ai-api",
    description="Concert AI Platform API"
)

# Create resources and methods
# ... (see setup_api_gateway.py for full example)
```

## Configuration

### Environment Variables

Set these environment variables before deployment:

```bash
# AWS Configuration
export AWS_REGION=us-east-1
export ENVIRONMENT=development

# Lambda Function ARNs (optional, will be auto-detected)
export CHATBOT_LAMBDA_ARN=arn:aws:lambda:...
export VENUE_LAMBDA_ARN=arn:aws:lambda:...
export PREDICTION_LAMBDA_ARN=arn:aws:lambda:...
export RECOMMENDATION_LAMBDA_ARN=arn:aws:lambda:...
```

### CloudFormation Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Environment | Environment name | development |
| ChatbotLambdaArn | Chatbot Lambda function ARN | Required |
| VenuePopularityLambdaArn | Venue popularity Lambda ARN | Required |
| TicketPredictionLambdaArn | Ticket prediction Lambda ARN | Required |
| RecommendationLambdaArn | Recommendation Lambda ARN | Required |

## Testing

### Test Chatbot Endpoint

```bash
# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name concert-ai-api-gateway-development \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --output text)

# Send chat message
curl -X POST "${API_ENDPOINT}/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the top venues?",
    "session_id": "test-session-123"
  }'
```

### Test Analytics Endpoints

```bash
# Get venue popularity
curl -X GET "${API_ENDPOINT}/venues/popularity?top_n=10"

# Predict ticket sales
curl -X POST "${API_ENDPOINT}/predictions/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_id": "artist-123",
    "venue_id": "venue-456",
    "event_date": "2025-12-31"
  }'

# Get recommendations
curl -X GET "${API_ENDPOINT}/recommendations?user_id=user-789&top_n=5"
```

### Test CORS

```bash
# OPTIONS request to check CORS headers
curl -X OPTIONS "${API_ENDPOINT}/chat" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

## Monitoring

### CloudWatch Metrics

Monitor these key metrics in CloudWatch:

- **4XXError** - Client errors
- **5XXError** - Server errors
- **Count** - Total requests
- **Latency** - Response time
- **IntegrationLatency** - Backend latency

### CloudWatch Logs

View API Gateway logs:

```bash
# View recent logs
aws logs tail /aws/apigateway/concert-ai-development --follow

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/apigateway/concert-ai-development \
  --filter-pattern "ERROR"
```

### X-Ray Tracing

View request traces in AWS X-Ray console to debug performance issues and errors.

## Security

### API Keys

API keys are created automatically during deployment. Retrieve the key:

```bash
# Get API key ID
API_KEY_ID=$(aws cloudformation describe-stacks \
  --stack-name concert-ai-api-gateway-development \
  --query 'Stacks[0].Outputs[?OutputKey==`APIKey`].OutputValue' \
  --output text)

# Get API key value
aws apigateway get-api-key \
  --api-key ${API_KEY_ID} \
  --include-value \
  --query 'value' \
  --output text
```

### IAM Permissions

The API Gateway requires these IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "arn:aws:lambda:*:*:function:concert-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### 1. Lambda Function Not Found

**Error**: `Invalid permissions on Lambda function`

**Solution**: Ensure Lambda functions exist and have correct permissions:

```bash
# Add Lambda permission for API Gateway
aws lambda add-permission \
  --function-name concert-chatbot-handler \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:123456789012:*/*/POST/chat"
```

#### 2. CORS Errors

**Error**: `No 'Access-Control-Allow-Origin' header`

**Solution**: Verify OPTIONS method is configured:

```bash
# Check if OPTIONS method exists
aws apigateway get-method \
  --rest-api-id ${API_ID} \
  --resource-id ${RESOURCE_ID} \
  --http-method OPTIONS
```

#### 3. Throttling Errors

**Error**: `429 Too Many Requests`

**Solution**: Increase throttling limits in usage plan:

```bash
aws apigateway update-usage-plan \
  --usage-plan-id ${USAGE_PLAN_ID} \
  --patch-operations \
      op=replace,path=/throttle/rateLimit,value=1000 \
      op=replace,path=/throttle/burstLimit,value=2000
```

#### 4. Integration Timeout

**Error**: `504 Gateway Timeout`

**Solution**: Increase Lambda timeout or optimize function:

```bash
aws lambda update-function-configuration \
  --function-name concert-chatbot-handler \
  --timeout 30
```

## Updating the API

### Add New Endpoint

1. Update CloudFormation template or Python script
2. Add new resource and method definitions
3. Configure integration with Lambda
4. Enable CORS
5. Redeploy

```bash
# Redeploy CloudFormation stack
aws cloudformation deploy \
  --template-file infrastructure/api_gateway_config.yaml \
  --stack-name concert-ai-api-gateway-development
```

### Update Existing Endpoint

1. Modify method or integration configuration
2. Create new deployment

```bash
# Create new deployment
aws apigateway create-deployment \
  --rest-api-id ${API_ID} \
  --stage-name development \
  --description "Updated endpoint configuration"
```

## Cleanup

### Delete API Gateway

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack \
  --stack-name concert-ai-api-gateway-development

# Or delete API directly
aws apigateway delete-rest-api --rest-api-id ${API_ID}
```

## Best Practices

1. **Use CloudFormation** for production deployments
2. **Enable X-Ray tracing** for debugging
3. **Set appropriate throttling limits** based on expected load
4. **Use API keys** for additional security
5. **Monitor CloudWatch metrics** regularly
6. **Configure custom domain** for production
7. **Use stages** for different environments
8. **Enable caching** for frequently accessed endpoints
9. **Implement request validation** to reduce Lambda invocations
10. **Use VPC links** for private integrations

## Next Steps

1. [Deploy Lambda Functions](./LAMBDA_DEPLOYMENT_GUIDE.md)
2. [Configure Custom Domain](./CUSTOM_DOMAIN_SETUP.md)
3. [Set Up CloudWatch Dashboards](./MONITORING_SETUP.md)
4. [Configure Web Application](../../web/README.md)

## References

- [AWS API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [API Gateway REST API Reference](https://docs.aws.amazon.com/apigateway/latest/api/)
- [CloudFormation API Gateway Resource Types](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/AWS_ApiGateway.html)
