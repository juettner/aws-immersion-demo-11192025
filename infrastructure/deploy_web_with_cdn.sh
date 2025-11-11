#!/bin/bash

# Complete Web Application Deployment with CDN
# Builds, deploys to S3, and invalidates CloudFront cache

set -e

# Default values
BUCKET_NAME="${BUCKET_NAME:-concert-data-platform-web}"
REGION="${REGION:-us-east-1}"
WEB_DIR="web"
INVALIDATE_CACHE="${INVALIDATE_CACHE:-true}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Web Application Deployment with CDN      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${GREEN}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is required but not installed${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm is required but not installed${NC}"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}✗ AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Step 1: Build and deploy to S3
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 1: Building and deploying to S3${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

python3 infrastructure/deploy_web_app.py \
    --bucket-name "$BUCKET_NAME" \
    --web-dir "$WEB_DIR" \
    --region "$REGION"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Deployment to S3 failed${NC}"
    exit 1
fi

echo ""

# Step 2: Invalidate CloudFront cache (if enabled)
if [ "$INVALIDATE_CACHE" = "true" ]; then
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${BLUE}Step 2: Invalidating CloudFront cache${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo ""
    
    python3 infrastructure/invalidate_cloudfront.py \
        --bucket-name "$BUCKET_NAME"
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Cache invalidation failed or no CloudFront distribution found${NC}"
        echo -e "${YELLOW}   Your site is still accessible via S3 website URL${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping CloudFront cache invalidation${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Deployment Complete!                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Your application has been deployed successfully.${NC}"
echo ""
echo -e "${BLUE}Access your application:${NC}"
echo -e "  S3 Website: http://${BUCKET_NAME}.s3-website-${REGION}.amazonaws.com"
echo -e "  CloudFront: Check the output above for the CloudFront URL"
echo ""
echo -e "${YELLOW}Note: CloudFront changes may take a few minutes to propagate${NC}"
echo ""

exit 0
