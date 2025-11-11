#!/bin/bash

# Deploy AWS API Gateway for Concert AI Platform
# This script sets up API Gateway with all required routes, CORS, and throttling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="${ENVIRONMENT:-development}"
REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="concert-ai-api-gateway-${ENVIRONMENT}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}API Gateway Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"
echo "Stack Name: ${STACK_NAME}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Please configure AWS credentials using 'aws configure'"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS credentials configured (Account: ${ACCOUNT_ID})${NC}"
echo ""

# Function to check if Lambda function exists
check_lambda_function() {
    local function_name=$1
    if aws lambda get-function --function-name "${function_name}" --region "${REGION}" &> /dev/null; then
        echo -e "${GREEN}✓ Lambda function found: ${function_name}${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Lambda function not found: ${function_name}${NC}"
        return 1
    fi
}

# Check for Lambda functions
echo -e "${YELLOW}Checking for Lambda functions...${NC}"
CHATBOT_LAMBDA="concert-chatbot-handler-${ENVIRONMENT}"
VENUE_LAMBDA="concert-venue-popularity-${ENVIRONMENT}"
PREDICTION_LAMBDA="concert-ticket-prediction-${ENVIRONMENT}"
RECOMMENDATION_LAMBDA="concert-recommendation-${ENVIRONMENT}"

check_lambda_function "${CHATBOT_LAMBDA}" || echo "  (Will use placeholder ARN)"
check_lambda_function "${VENUE_LAMBDA}" || echo "  (Will use placeholder ARN)"
check_lambda_function "${PREDICTION_LAMBDA}" || echo "  (Will use placeholder ARN)"
check_lambda_function "${RECOMMENDATION_LAMBDA}" || echo "  (Will use placeholder ARN)"
echo ""

# Option 1: Deploy using CloudFormation (if Lambda ARNs are available)
deploy_with_cloudformation() {
    echo -e "${YELLOW}Deploying API Gateway using CloudFormation...${NC}"
    
    # Get Lambda ARNs
    CHATBOT_ARN=$(aws lambda get-function --function-name "${CHATBOT_LAMBDA}" --region "${REGION}" --query 'Configuration.FunctionArn' --output text 2>/dev/null || echo "")
    VENUE_ARN=$(aws lambda get-function --function-name "${VENUE_LAMBDA}" --region "${REGION}" --query 'Configuration.FunctionArn' --output text 2>/dev/null || echo "")
    PREDICTION_ARN=$(aws lambda get-function --function-name "${PREDICTION_LAMBDA}" --region "${REGION}" --query 'Configuration.FunctionArn' --output text 2>/dev/null || echo "")
    RECOMMENDATION_ARN=$(aws lambda get-function --function-name "${RECOMMENDATION_LAMBDA}" --region "${REGION}" --query 'Configuration.FunctionArn' --output text 2>/dev/null || echo "")
    
    # Use placeholder ARNs if functions don't exist
    CHATBOT_ARN="${CHATBOT_ARN:-arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${CHATBOT_LAMBDA}}"
    VENUE_ARN="${VENUE_ARN:-arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${VENUE_LAMBDA}}"
    PREDICTION_ARN="${PREDICTION_ARN:-arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${PREDICTION_LAMBDA}}"
    RECOMMENDATION_ARN="${RECOMMENDATION_ARN:-arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${RECOMMENDATION_LAMBDA}}"
    
    # Deploy CloudFormation stack
    aws cloudformation deploy \
        --template-file infrastructure/api_gateway_config.yaml \
        --stack-name "${STACK_NAME}" \
        --parameter-overrides \
            Environment="${ENVIRONMENT}" \
            ChatbotLambdaArn="${CHATBOT_ARN}" \
            VenuePopularityLambdaArn="${VENUE_ARN}" \
            TicketPredictionLambdaArn="${PREDICTION_ARN}" \
            RecommendationLambdaArn="${RECOMMENDATION_ARN}" \
        --capabilities CAPABILITY_IAM \
        --region "${REGION}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ CloudFormation deployment successful${NC}"
        
        # Get outputs
        API_ENDPOINT=$(aws cloudformation describe-stacks \
            --stack-name "${STACK_NAME}" \
            --region "${REGION}" \
            --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
            --output text)
        
        API_ID=$(aws cloudformation describe-stacks \
            --stack-name "${STACK_NAME}" \
            --region "${REGION}" \
            --query 'Stacks[0].Outputs[?OutputKey==`APIId`].OutputValue' \
            --output text)
        
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}Deployment Complete!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo "API ID: ${API_ID}"
        echo "API Endpoint: ${API_ENDPOINT}"
        echo ""
        echo "Endpoints:"
        echo "  - POST ${API_ENDPOINT}/chat"
        echo "  - GET  ${API_ENDPOINT}/history/{session_id}"
        echo "  - GET  ${API_ENDPOINT}/venues/popularity"
        echo "  - POST ${API_ENDPOINT}/predictions/tickets"
        echo "  - GET  ${API_ENDPOINT}/recommendations"
        echo ""
        echo "CORS: Enabled for all endpoints"
        echo "Throttling: 500 req/sec, burst 1000"
        echo "Quota: 100,000 requests/day"
        echo -e "${GREEN}========================================${NC}"
    else
        echo -e "${RED}✗ CloudFormation deployment failed${NC}"
        exit 1
    fi
}

# Option 2: Deploy using Python script
deploy_with_python() {
    echo -e "${YELLOW}Deploying API Gateway using Python script...${NC}"
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        exit 1
    fi
    
    # Run Python setup script
    python3 infrastructure/setup_api_gateway.py \
        --environment "${ENVIRONMENT}" \
        --region "${REGION}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Python deployment successful${NC}"
    else
        echo -e "${RED}✗ Python deployment failed${NC}"
        exit 1
    fi
}

# Ask user which deployment method to use
echo -e "${YELLOW}Choose deployment method:${NC}"
echo "1) CloudFormation (recommended for production)"
echo "2) Python script (for development/testing)"
echo ""
read -p "Enter choice [1-2]: " choice

case $choice in
    1)
        deploy_with_cloudformation
        ;;
    2)
        deploy_with_python
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}API Gateway deployment completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Update your web application's API endpoint configuration"
echo "2. Test the endpoints using curl or Postman"
echo "3. Monitor API Gateway metrics in CloudWatch"
echo ""
echo "To test the API:"
echo "  curl -X POST ${API_ENDPOINT}/chat -H 'Content-Type: application/json' -d '{\"message\":\"Hello\"}'"
echo ""
