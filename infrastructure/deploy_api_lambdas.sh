#!/bin/bash

# Deploy API Lambda Functions
# This script deploys Lambda functions for API Gateway endpoints

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}API Lambda Functions Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Load environment variables
if [ -f .env ]; then
    echo -e "${YELLOW}Loading environment variables from .env${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}Warning: .env file not found${NC}"
fi

# Check for required environment variables
REQUIRED_VARS=(
    "AWS_REGION"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: Required environment variable $var is not set${NC}"
        exit 1
    fi
done

# Set defaults
AWS_REGION=${AWS_REGION:-us-east-1}
ROLE_ARN=${LAMBDA_EXECUTION_ROLE_ARN:-}
S3_BUCKET=${LAMBDA_DEPLOYMENT_BUCKET:-}
API_GATEWAY_ID=${API_GATEWAY_ID:-}

echo "Configuration:"
echo "  AWS Region: $AWS_REGION"
echo "  Role ARN: ${ROLE_ARN:-'Will be created'}"
echo "  S3 Bucket: ${S3_BUCKET:-'Not using S3'}"
echo "  API Gateway ID: ${API_GATEWAY_ID:-'Not configured'}"
echo ""

# Build deployment command
DEPLOY_CMD="python infrastructure/deploy_api_lambdas.py --region $AWS_REGION"

if [ -n "$ROLE_ARN" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --role-arn $ROLE_ARN"
fi

if [ -n "$S3_BUCKET" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --s3-bucket $S3_BUCKET"
fi

if [ -n "$API_GATEWAY_ID" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --api-gateway-id $API_GATEWAY_ID"
fi

# Execute deployment
echo -e "${GREEN}Starting Lambda deployment...${NC}"
echo ""

if $DEPLOY_CMD; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Configure API Gateway to use these Lambda functions"
    echo "2. Test the endpoints using the API Gateway URL"
    echo "3. Update frontend configuration with API endpoint URLs"
    echo ""
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Deployment failed!${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Please check the error messages above and try again."
    exit 1
fi
