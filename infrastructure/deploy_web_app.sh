#!/bin/bash

# Web Application Deployment Script
# Builds and deploys the React application to S3

set -e

# Default values
BUCKET_NAME="${BUCKET_NAME:-concert-data-platform-web}"
REGION="${REGION:-us-east-1}"
WEB_DIR="web"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Web Application Deployment${NC}"
echo "================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is required but not installed${NC}"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}✗ AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

echo -e "${GREEN}✓ AWS credentials configured${NC}"
echo ""

# Check if node_modules exists
if [ ! -d "$WEB_DIR/node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found. Installing dependencies...${NC}"
    cd "$WEB_DIR"
    npm install
    cd ..
    echo ""
fi

# Run the Python deployment script
python3 infrastructure/deploy_web_app.py \
    --bucket-name "$BUCKET_NAME" \
    --web-dir "$WEB_DIR" \
    --region "$REGION"

exit $?
