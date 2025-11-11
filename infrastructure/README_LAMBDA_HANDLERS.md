# API Lambda Handlers - Quick Start

## Overview

This directory contains Lambda function handlers and deployment scripts for the Concert Data Platform API.

## Files

- **`api_lambda_handlers.py`** (in `src/infrastructure/`): Lambda function handlers
- **`deploy_api_lambdas.py`**: Python deployment script
- **`deploy_api_lambdas.sh`**: Shell script wrapper for deployment
- **`validate_api_lambda_handlers.py`** (in root): Validation script

## Quick Deploy

```bash
# 1. Set environment variables in .env
cp .env.example .env
# Edit .env with your AWS configuration

# 2. Deploy Lambda functions
./infrastructure/deploy_api_lambdas.sh
```

## Lambda Functions

| Function | Endpoint | Purpose |
|----------|----------|---------|
| `concert-api-chatbot` | `POST /chat` | Chatbot message processing |
| `concert-api-venue-popularity` | `POST /venues/popularity` | Venue rankings |
| `concert-api-ticket-prediction` | `POST /tickets/predict` | Ticket sales predictions |
| `concert-api-recommendations` | `POST /recommendations` | Concert recommendations |
| `concert-api-health-check` | `GET /health` | Health check |

## Environment Variables

Required in `.env`:

```bash
AWS_REGION=us-east-1
REDSHIFT_CLUSTER_ID=your-cluster-id
REDSHIFT_DATABASE=concert_data

# Optional
BEDROCK_AGENT_ID=your-agent-id
BEDROCK_AGENT_ALIAS_ID=your-alias-id
SAGEMAKER_VENUE_ENDPOINT=your-endpoint
SAGEMAKER_TICKET_ENDPOINT=your-endpoint
```

## Testing

```bash
# Validate implementation
python validate_api_lambda_handlers.py

# Test individual handler
aws lambda invoke \
  --function-name concert-api-health-check \
  --payload '{}' \
  response.json
```

## Documentation

See [LAMBDA_HANDLERS_GUIDE.md](../docs/infrastructure/LAMBDA_HANDLERS_GUIDE.md) for complete documentation.

## IAM Permissions

Lambda execution role needs:
- `AWSLambdaBasicExecutionRole` (CloudWatch Logs)
- `AmazonRedshiftDataFullAccess` (Redshift queries)
- `AmazonBedrockFullAccess` (Bedrock Agent)
- `AmazonSageMakerFullAccess` (SageMaker endpoints)

## Monitoring

View logs:
```bash
aws logs tail /aws/lambda/concert-api-chatbot --follow
```

## Troubleshooting

1. **Deployment fails**: Check IAM permissions and AWS credentials
2. **Function errors**: Check CloudWatch Logs for details
3. **Timeout**: Increase timeout in function configuration
4. **Memory**: Increase memory allocation

## Next Steps

1. Deploy Lambda functions
2. Configure API Gateway routes
3. Test endpoints
4. Set up monitoring and alarms
