#!/bin/bash

# Production Data Ingestion Runner
# This script helps you run the production ingestion pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  Concert Data Production Ingestion"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: .env file not found${NC}"
    echo "Please create a .env file with your API credentials."
    echo ""
    echo "Required variables:"
    echo "  API_SPOTIFY_CLIENT_ID"
    echo "  API_SPOTIFY_CLIENT_SECRET"
    echo "  API_TICKETMASTER_API_KEY"
    echo "  AWS_REGION"
    echo "  AWS_S3_BUCKET_RAW"
    echo "  AWS_KINESIS_STREAM_NAME"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check for required environment variables
REQUIRED_VARS=(
    "API_SPOTIFY_CLIENT_ID"
    "API_SPOTIFY_CLIENT_SECRET"
    "API_TICKETMASTER_API_KEY"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}ERROR: Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

echo -e "${GREEN}✓ Environment variables loaded${NC}"
echo ""

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${YELLOW}WARNING: AWS credentials not configured or invalid${NC}"
    echo "Data will not be persisted to S3 or Kinesis."
    echo "Configure AWS CLI with: aws configure"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ AWS credentials valid${NC}"
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    echo "  Account: $AWS_ACCOUNT"
    echo "  Region: ${AWS_REGION:-us-east-1}"
    echo ""
fi

# Check if S3 bucket exists
if [ ! -z "$AWS_S3_BUCKET_RAW" ]; then
    if aws s3 ls "s3://$AWS_S3_BUCKET_RAW" &> /dev/null; then
        echo -e "${GREEN}✓ S3 bucket exists: $AWS_S3_BUCKET_RAW${NC}"
    else
        echo -e "${YELLOW}WARNING: S3 bucket not found: $AWS_S3_BUCKET_RAW${NC}"
        read -p "Create bucket? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            aws s3 mb "s3://$AWS_S3_BUCKET_RAW" --region "${AWS_REGION:-us-east-1}"
            echo -e "${GREEN}✓ Bucket created${NC}"
        fi
    fi
    echo ""
fi

# Check if Kinesis stream exists
if [ ! -z "$AWS_KINESIS_STREAM_NAME" ]; then
    if aws kinesis describe-stream --stream-name "$AWS_KINESIS_STREAM_NAME" &> /dev/null; then
        echo -e "${GREEN}✓ Kinesis stream exists: $AWS_KINESIS_STREAM_NAME${NC}"
    else
        echo -e "${YELLOW}WARNING: Kinesis stream not found: $AWS_KINESIS_STREAM_NAME${NC}"
        read -p "Create stream? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            aws kinesis create-stream \
                --stream-name "$AWS_KINESIS_STREAM_NAME" \
                --shard-count 1 \
                --region "${AWS_REGION:-us-east-1}"
            echo "Waiting for stream to become active..."
            aws kinesis wait stream-exists --stream-name "$AWS_KINESIS_STREAM_NAME"
            echo -e "${GREEN}✓ Stream created${NC}"
        fi
    fi
    echo ""
fi

# Menu for job selection
echo "Select ingestion job to run:"
echo "  1) Full ingestion (daily)"
echo "  2) Hourly event updates"
echo "  3) Artist refresh"
echo "  4) Venue refresh"
echo "  5) Test run (minimal data)"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        JOB_TYPE="daily"
        echo -e "${GREEN}Running full daily ingestion...${NC}"
        ;;
    2)
        JOB_TYPE="hourly"
        echo -e "${GREEN}Running hourly event updates...${NC}"
        ;;
    3)
        JOB_TYPE="artist_refresh"
        echo -e "${GREEN}Running artist refresh...${NC}"
        ;;
    4)
        JOB_TYPE="venue_refresh"
        echo -e "${GREEN}Running venue refresh...${NC}"
        ;;
    5)
        JOB_TYPE="test"
        echo -e "${GREEN}Running test ingestion...${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "  Starting Ingestion Pipeline"
echo "=========================================="
echo ""

# Run the ingestion
if [ "$JOB_TYPE" = "test" ]; then
    # Test run with minimal data
    python -m src.services.external_apis.production_ingestion
else
    # Production run
    python -m src.services.external_apis.scheduled_ingestion --job-type "$JOB_TYPE"
fi

EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Ingestion completed successfully${NC}"
else
    echo -e "${RED}✗ Ingestion failed with exit code $EXIT_CODE${NC}"
fi
echo "=========================================="

exit $EXIT_CODE