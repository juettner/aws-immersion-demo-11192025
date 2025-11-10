#!/bin/bash

# Kinesis Stream Setup for API Data Ingestion
# This script creates and configures the Kinesis stream for external API data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "  Kinesis Stream Setup for API Ingestion"
echo -e "==========================================${NC}"
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✓ Environment variables loaded${NC}"
else
    echo -e "${RED}✗ .env file not found${NC}"
    exit 1
fi

# Set defaults
STREAM_NAME=${AWS_KINESIS_STREAM_NAME:-concert-data-stream}
SHARD_COUNT=${AWS_KINESIS_SHARD_COUNT:-1}
REGION=${AWS_REGION:-us-east-1}

echo ""
echo "Configuration:"
echo "  Stream Name: $STREAM_NAME"
echo "  Shard Count: $SHARD_COUNT"
echo "  Region: $REGION"
echo ""

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}✗ AWS credentials not configured${NC}"
    echo "Please run: aws configure"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS credentials valid${NC}"
echo "  Account: $AWS_ACCOUNT"
echo ""

# Check if stream already exists
echo "Checking if Kinesis stream exists..."
if aws kinesis describe-stream --stream-name "$STREAM_NAME" --region "$REGION" &> /dev/null; then
    echo -e "${YELLOW}⚠ Stream already exists: $STREAM_NAME${NC}"
    
    # Get current shard count
    CURRENT_SHARDS=$(aws kinesis describe-stream \
        --stream-name "$STREAM_NAME" \
        --region "$REGION" \
        --query 'StreamDescription.Shards | length(@)' \
        --output text)
    
    echo "  Current shard count: $CURRENT_SHARDS"
    echo "  Status: $(aws kinesis describe-stream --stream-name "$STREAM_NAME" --region "$REGION" --query 'StreamDescription.StreamStatus' --output text)"
    echo ""
    
    read -p "Do you want to update the stream? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping stream creation."
        echo ""
        echo -e "${GREEN}Stream is ready to use!${NC}"
        exit 0
    fi
    
    # Update shard count if different
    if [ "$CURRENT_SHARDS" != "$SHARD_COUNT" ]; then
        echo "Updating shard count from $CURRENT_SHARDS to $SHARD_COUNT..."
        aws kinesis update-shard-count \
            --stream-name "$STREAM_NAME" \
            --target-shard-count "$SHARD_COUNT" \
            --scaling-type UNIFORM_SCALING \
            --region "$REGION"
        echo -e "${GREEN}✓ Shard count updated${NC}"
    fi
else
    echo "Creating Kinesis stream..."
    
    # Create the stream
    aws kinesis create-stream \
        --stream-name "$STREAM_NAME" \
        --shard-count "$SHARD_COUNT" \
        --region "$REGION" \
        --stream-mode-details StreamMode=PROVISIONED
    
    echo -e "${GREEN}✓ Stream created${NC}"
    echo ""
    
    # Wait for stream to become active
    echo "Waiting for stream to become active..."
    aws kinesis wait stream-exists \
        --stream-name "$STREAM_NAME" \
        --region "$REGION"
    
    echo -e "${GREEN}✓ Stream is active${NC}"
fi

echo ""

# Enable enhanced monitoring (optional)
echo "Configuring enhanced monitoring..."
aws kinesis enable-enhanced-monitoring \
    --stream-name "$STREAM_NAME" \
    --shard-level-metrics IncomingBytes,IncomingRecords,OutgoingBytes,OutgoingRecords,WriteProvisionedThroughputExceeded,ReadProvisionedThroughputExceeded,IteratorAgeMilliseconds \
    --region "$REGION" &> /dev/null || echo -e "${YELLOW}⚠ Enhanced monitoring already enabled${NC}"

echo -e "${GREEN}✓ Enhanced monitoring configured${NC}"
echo ""

# Enable encryption (optional but recommended)
echo "Enabling server-side encryption..."
read -p "Enable encryption with AWS managed key? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    aws kinesis start-stream-encryption \
        --stream-name "$STREAM_NAME" \
        --encryption-type KMS \
        --key-id alias/aws/kinesis \
        --region "$REGION" 2>/dev/null && echo -e "${GREEN}✓ Encryption enabled${NC}" || echo -e "${YELLOW}⚠ Encryption already enabled or failed${NC}"
fi

echo ""

# Add tags
echo "Adding tags to stream..."
aws kinesis add-tags-to-stream \
    --stream-name "$STREAM_NAME" \
    --tags Project=ConcertDataPlatform,Environment=${APP_ENVIRONMENT:-development},Purpose=APIDataIngestion,ManagedBy=Terraform \
    --region "$REGION"

echo -e "${GREEN}✓ Tags added${NC}"
echo ""

# Get stream details
echo -e "${BLUE}=========================================="
echo "  Stream Details"
echo -e "==========================================${NC}"

STREAM_ARN=$(aws kinesis describe-stream \
    --stream-name "$STREAM_NAME" \
    --region "$REGION" \
    --query 'StreamDescription.StreamARN' \
    --output text)

STREAM_STATUS=$(aws kinesis describe-stream \
    --stream-name "$STREAM_NAME" \
    --region "$REGION" \
    --query 'StreamDescription.StreamStatus' \
    --output text)

RETENTION_HOURS=$(aws kinesis describe-stream \
    --stream-name "$STREAM_NAME" \
    --region "$REGION" \
    --query 'StreamDescription.RetentionPeriodHours' \
    --output text)

echo "Stream Name: $STREAM_NAME"
echo "Stream ARN: $STREAM_ARN"
echo "Status: $STREAM_STATUS"
echo "Shard Count: $SHARD_COUNT"
echo "Retention Period: $RETENTION_HOURS hours"
echo "Region: $REGION"
echo ""

# Create IAM policy for stream access
echo -e "${BLUE}=========================================="
echo "  IAM Policy"
echo -e "==========================================${NC}"

POLICY_NAME="ConcertDataIngestionKinesisPolicy"

# Check if policy exists
if aws iam get-policy --policy-arn "arn:aws:iam::${AWS_ACCOUNT}:policy/${POLICY_NAME}" &> /dev/null; then
    echo -e "${YELLOW}⚠ IAM policy already exists: $POLICY_NAME${NC}"
else
    echo "Creating IAM policy for Kinesis access..."
    
    cat > /tmp/kinesis-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords",
        "kinesis:DescribeStream",
        "kinesis:DescribeStreamSummary",
        "kinesis:GetRecords",
        "kinesis:GetShardIterator",
        "kinesis:ListShards"
      ],
      "Resource": "$STREAM_ARN"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:ListStreams"
      ],
      "Resource": "*"
    }
  ]
}
EOF
    
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file:///tmp/kinesis-policy.json \
        --description "Policy for Concert Data Ingestion to write to Kinesis stream" \
        --region "$REGION"
    
    rm /tmp/kinesis-policy.json
    
    echo -e "${GREEN}✓ IAM policy created${NC}"
    echo "  Policy ARN: arn:aws:iam::${AWS_ACCOUNT}:policy/${POLICY_NAME}"
    echo ""
    echo "Attach this policy to your Lambda execution role or EC2 instance profile:"
    echo "  aws iam attach-role-policy --role-name YOUR_ROLE_NAME --policy-arn arn:aws:iam::${AWS_ACCOUNT}:policy/${POLICY_NAME}"
fi

echo ""

# Test stream
echo -e "${BLUE}=========================================="
echo "  Testing Stream"
echo -e "==========================================${NC}"

echo "Sending test record to stream..."

TEST_DATA='{"test": true, "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'", "message": "Test record from setup script"}'

aws kinesis put-record \
    --stream-name "$STREAM_NAME" \
    --partition-key "test" \
    --data "$TEST_DATA" \
    --region "$REGION" > /dev/null

echo -e "${GREEN}✓ Test record sent successfully${NC}"
echo ""

# Show how to read from stream
echo "To read from the stream:"
echo ""
echo "# Get shard iterator"
echo "SHARD_ID=\$(aws kinesis list-shards --stream-name $STREAM_NAME --region $REGION --query 'Shards[0].ShardId' --output text)"
echo "SHARD_ITERATOR=\$(aws kinesis get-shard-iterator --stream-name $STREAM_NAME --shard-id \$SHARD_ID --shard-iterator-type LATEST --region $REGION --query 'ShardIterator' --output text)"
echo ""
echo "# Get records"
echo "aws kinesis get-records --shard-iterator \$SHARD_ITERATOR --region $REGION"
echo ""

# Summary
echo -e "${BLUE}=========================================="
echo "  Setup Complete!"
echo -e "==========================================${NC}"
echo ""
echo -e "${GREEN}✓ Kinesis stream is ready for API data ingestion${NC}"
echo ""
echo "Next steps:"
echo "  1. Update your .env file with the stream name (already set)"
echo "  2. Run the ingestion pipeline: python -m src.services.external_apis.production_ingestion"
echo "  3. Monitor the stream in CloudWatch"
echo "  4. Set up Lambda consumers for real-time processing"
echo ""
echo "Useful commands:"
echo "  # Monitor stream metrics"
echo "  aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name IncomingRecords --dimensions Name=StreamName,Value=$STREAM_NAME --start-time \$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) --end-time \$(date -u +%Y-%m-%dT%H:%M:%S) --period 60 --statistics Sum --region $REGION"
echo ""
echo "  # View stream details"
echo "  aws kinesis describe-stream --stream-name $STREAM_NAME --region $REGION"
echo ""
echo "  # List all streams"
echo "  aws kinesis list-streams --region $REGION"
echo ""