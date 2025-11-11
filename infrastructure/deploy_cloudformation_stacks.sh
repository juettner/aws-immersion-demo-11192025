#!/bin/bash

# Deploy CloudFormation stacks for Concert Data Platform
# Usage: ./deploy_cloudformation_stacks.sh [environment] [region]

set -e

# Configuration
ENVIRONMENT=${1:-development}
REGION=${2:-us-east-1}
STACK_PREFIX="concert-platform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Concert Data Platform - CloudFormation Deployment"
echo "=========================================="
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "=========================================="

# Function to wait for stack completion
wait_for_stack() {
    local stack_name=$1
    echo -e "${YELLOW}Waiting for stack $stack_name to complete...${NC}"
    
    aws cloudformation wait stack-create-complete \
        --stack-name "$stack_name" \
        --region "$REGION" 2>/dev/null || \
    aws cloudformation wait stack-update-complete \
        --stack-name "$stack_name" \
        --region "$REGION" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Stack $stack_name completed successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Stack $stack_name failed${NC}"
        return 1
    fi
}

# Function to deploy or update stack
deploy_stack() {
    local stack_name=$1
    local template_file=$2
    shift 2
    local parameters=("$@")
    
    echo ""
    echo "=========================================="
    echo "Deploying: $stack_name"
    echo "Template: $template_file"
    echo "=========================================="
    
    # Check if stack exists
    if aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$REGION" &>/dev/null; then
        
        echo "Stack exists, updating..."
        aws cloudformation update-stack \
            --stack-name "$stack_name" \
            --template-body "file://$template_file" \
            --parameters "${parameters[@]}" \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION" 2>&1 | tee /tmp/stack-output.txt
        
        if grep -q "No updates are to be performed" /tmp/stack-output.txt; then
            echo -e "${YELLOW}No updates needed for $stack_name${NC}"
            return 0
        fi
    else
        echo "Stack does not exist, creating..."
        aws cloudformation create-stack \
            --stack-name "$stack_name" \
            --template-body "file://$template_file" \
            --parameters "${parameters[@]}" \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION"
    fi
    
    wait_for_stack "$stack_name"
}

# Get parameters from user
read -p "Enter Redshift master password (min 8 chars): " -s REDSHIFT_PASSWORD
echo ""

read -p "Enter alert email address (optional, press Enter to skip): " ALERT_EMAIL

read -p "Enter Bedrock Agent ID (optional, press Enter to skip): " BEDROCK_AGENT_ID

read -p "Enter Bedrock Agent Alias ID (optional, press Enter to skip): " BEDROCK_AGENT_ALIAS_ID

# Deploy stacks in order

# 1. Networking
NETWORK_STACK="${STACK_PREFIX}-networking-${ENVIRONMENT}"
deploy_stack "$NETWORK_STACK" \
    "infrastructure/cloudformation/01-networking.yaml" \
    "ParameterKey=Environment,ParameterValue=$ENVIRONMENT"

# 2. Storage and Processing
STORAGE_STACK="${STACK_PREFIX}-storage-${ENVIRONMENT}"
STORAGE_PARAMS=(
    "ParameterKey=Environment,ParameterValue=$ENVIRONMENT"
    "ParameterKey=NetworkStackName,ParameterValue=$NETWORK_STACK"
    "ParameterKey=RedshiftMasterUsername,ParameterValue=admin"
    "ParameterKey=RedshiftMasterPassword,ParameterValue=$REDSHIFT_PASSWORD"
)
deploy_stack "$STORAGE_STACK" \
    "infrastructure/cloudformation/02-storage-processing.yaml" \
    "${STORAGE_PARAMS[@]}"

# 3. Compute and Application
COMPUTE_STACK="${STACK_PREFIX}-compute-${ENVIRONMENT}"
COMPUTE_PARAMS=(
    "ParameterKey=Environment,ParameterValue=$ENVIRONMENT"
    "ParameterKey=NetworkStackName,ParameterValue=$NETWORK_STACK"
    "ParameterKey=StorageStackName,ParameterValue=$STORAGE_STACK"
)

if [ -n "$BEDROCK_AGENT_ID" ]; then
    COMPUTE_PARAMS+=("ParameterKey=BedrockAgentId,ParameterValue=$BEDROCK_AGENT_ID")
fi

if [ -n "$BEDROCK_AGENT_ALIAS_ID" ]; then
    COMPUTE_PARAMS+=("ParameterKey=BedrockAgentAliasId,ParameterValue=$BEDROCK_AGENT_ALIAS_ID")
fi

deploy_stack "$COMPUTE_STACK" \
    "infrastructure/cloudformation/03-compute-application.yaml" \
    "${COMPUTE_PARAMS[@]}"

# 4. Chatbot Infrastructure
CHATBOT_STACK="${STACK_PREFIX}-chatbot-${ENVIRONMENT}"
CHATBOT_PARAMS=(
    "ParameterKey=Environment,ParameterValue=$ENVIRONMENT"
    "ParameterKey=NetworkStackName,ParameterValue=$NETWORK_STACK"
    "ParameterKey=ComputeStackName,ParameterValue=$COMPUTE_STACK"
)

if [ -n "$BEDROCK_AGENT_ID" ]; then
    CHATBOT_PARAMS+=("ParameterKey=BedrockAgentId,ParameterValue=$BEDROCK_AGENT_ID")
fi

if [ -n "$BEDROCK_AGENT_ALIAS_ID" ]; then
    CHATBOT_PARAMS+=("ParameterKey=BedrockAgentAliasId,ParameterValue=$BEDROCK_AGENT_ALIAS_ID")
fi

deploy_stack "$CHATBOT_STACK" \
    "infrastructure/cloudformation/04-chatbot-infrastructure.yaml" \
    "${CHATBOT_PARAMS[@]}"

# 5. Monitoring and Observability
MONITORING_STACK="${STACK_PREFIX}-monitoring-${ENVIRONMENT}"
MONITORING_PARAMS=(
    "ParameterKey=Environment,ParameterValue=$ENVIRONMENT"
    "ParameterKey=ComputeStackName,ParameterValue=$COMPUTE_STACK"
    "ParameterKey=StorageStackName,ParameterValue=$STORAGE_STACK"
)

if [ -n "$ALERT_EMAIL" ]; then
    MONITORING_PARAMS+=("ParameterKey=AlertEmail,ParameterValue=$ALERT_EMAIL")
fi

deploy_stack "$MONITORING_STACK" \
    "infrastructure/cloudformation/05-monitoring-observability.yaml" \
    "${MONITORING_PARAMS[@]}"

# 6. Tracing and Logging
LOGGING_STACK="${STACK_PREFIX}-logging-${ENVIRONMENT}"
LOGGING_PARAMS=(
    "ParameterKey=Environment,ParameterValue=$ENVIRONMENT"
    "ParameterKey=ComputeStackName,ParameterValue=$COMPUTE_STACK"
    "ParameterKey=LogRetentionDays,ParameterValue=7"
)

deploy_stack "$LOGGING_STACK" \
    "infrastructure/cloudformation/06-tracing-logging.yaml" \
    "${LOGGING_PARAMS[@]}"

# Get outputs
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Retrieving stack outputs..."
echo ""

# Get API Gateway endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "$COMPUTE_STACK" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='RestAPIEndpoint'].OutputValue" \
    --output text)

echo "API Gateway Endpoint: $API_ENDPOINT"

# Get dashboard URLs
PIPELINE_DASHBOARD=$(aws cloudformation describe-stacks \
    --stack-name "$MONITORING_STACK" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='DataPipelineDashboardURL'].OutputValue" \
    --output text)

CHATBOT_DASHBOARD=$(aws cloudformation describe-stacks \
    --stack-name "$MONITORING_STACK" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='ChatbotDashboardURL'].OutputValue" \
    --output text)

echo ""
echo "CloudWatch Dashboards:"
echo "  - Data Pipeline: $PIPELINE_DASHBOARD"
echo "  - Chatbot: $CHATBOT_DASHBOARD"
echo ""
echo "=========================================="
echo -e "${GREEN}All stacks deployed successfully!${NC}"
echo "=========================================="
