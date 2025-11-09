#!/bin/bash
# Deploy Redshift using CloudFormation

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

STACK_NAME="${STACK_NAME:-concert-redshift-stack}"
TEMPLATE_FILE="infrastructure/redshift_cloudformation.yaml"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Redshift CloudFormation Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Generate a secure password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

MASTER_PASSWORD=$(generate_password)

echo -e "\n${YELLOW}Deploying CloudFormation stack...${NC}"
echo "Stack Name: $STACK_NAME"
echo "Region: $AWS_REGION"

# Deploy the stack
aws cloudformation create-stack \
    --stack-name "$STACK_NAME" \
    --template-body file://"$TEMPLATE_FILE" \
    --parameters \
        ParameterKey=MasterUserPassword,ParameterValue="$MASTER_PASSWORD" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$AWS_REGION"

echo -e "${GREEN}✓ Stack creation initiated${NC}"

# Save password
cat > redshift_cloudformation_credentials.txt <<EOF
STACK_NAME=$STACK_NAME
MASTER_PASSWORD=$MASTER_PASSWORD
AWS_REGION=$AWS_REGION
EOF

echo -e "${GREEN}✓ Credentials saved to redshift_cloudformation_credentials.txt${NC}"

echo -e "\n${YELLOW}Waiting for stack to complete (this may take 10-15 minutes)...${NC}"

aws cloudformation wait stack-create-complete \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION"

echo -e "${GREEN}✓ Stack creation complete!${NC}"

# Get outputs
echo -e "\n${YELLOW}Retrieving stack outputs...${NC}"

CLUSTER_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ClusterEndpoint`].OutputValue' \
    --output text)

CLUSTER_PORT=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ClusterPort`].OutputValue' \
    --output text)

DATABASE_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`DatabaseName`].OutputValue' \
    --output text)

IAM_ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`IAMRoleArn`].OutputValue' \
    --output text)

# Update credentials file
cat >> redshift_cloudformation_credentials.txt <<EOF
CLUSTER_ENDPOINT=$CLUSTER_ENDPOINT
CLUSTER_PORT=$CLUSTER_PORT
DATABASE_NAME=$DATABASE_NAME
IAM_ROLE_ARN=$IAM_ROLE_ARN
EOF

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Connection Details:${NC}"
echo "Endpoint: $CLUSTER_ENDPOINT"
echo "Port: $CLUSTER_PORT"
echo "Database: $DATABASE_NAME"
echo "Username: admin"
echo "Password: (saved in redshift_cloudformation_credentials.txt)"
echo "IAM Role: $IAM_ROLE_ARN"

echo -e "\n${YELLOW}Environment Variables for .env:${NC}"
cat <<EOF
AWS_REDSHIFT_HOST=$CLUSTER_ENDPOINT
AWS_REDSHIFT_PORT=$CLUSTER_PORT
AWS_REDSHIFT_DATABASE=$DATABASE_NAME
AWS_REDSHIFT_USER=admin
AWS_REDSHIFT_PASSWORD=$MASTER_PASSWORD
AWS_SAGEMAKER_EXECUTION_ROLE=$IAM_ROLE_ARN
AWS_REGION=$AWS_REGION
EOF

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Update your .env file with the credentials above"
echo "2. Run: python infrastructure/initialize_redshift_schema.py"
echo "3. Load data using the RedshiftService"

echo -e "\n${YELLOW}To delete the stack later:${NC}"
echo "aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION"
