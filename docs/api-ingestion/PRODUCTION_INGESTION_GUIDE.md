# Production Data Ingestion Guide

## Overview

This guide explains how to run the external API connectors in a production environment with proper data persistence to AWS services.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Ingestion Pipeline                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   External APIs (Spotify/Ticketmaster)│
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │    Data Ingestion Service            │
        │  - Rate limiting                     │
        │  - Retry logic                       │
        │  - Data transformation               │
        └──────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
        ┌──────────────────┐  ┌──────────────────┐
        │   Amazon S3      │  │  Amazon Kinesis  │
        │  (Data Lake)     │  │  (Streaming)     │
        │  - Raw zone      │  │  - Real-time     │
        │  - Partitioned   │  │  - Processing    │
        └──────────────────┘  └──────────────────┘
                    │                   │
                    ▼                   ▼
        ┌──────────────────┐  ┌──────────────────┐
        │   AWS Glue       │  │  AWS Lambda      │
        │  (ETL)           │  │  (Processing)    │
        └──────────────────┘  └──────────────────┘
                    │                   │
                    └─────────┬─────────┘
                              ▼
                    ┌──────────────────┐
                    │  Amazon Redshift │
                    │  (Data Warehouse)│
                    └──────────────────┘
```

## Data Flow

### 1. **API Ingestion**
- Fetches data from Spotify and Ticketmaster APIs
- Applies rate limiting and retry logic
- Transforms data to normalized format

### 2. **S3 Storage (Data Lake - Raw Zone)**
- **Location**: `s3://{bucket}/raw/{source}/{data_type}/year={YYYY}/month={MM}/day={DD}/`
- **Format**: JSON files with metadata
- **Partitioning**: By date and source for efficient querying
- **Purpose**: 
  - Long-term storage
  - Data lineage
  - Reprocessing capability
  - Audit trail

### 3. **Kinesis Streaming**
- **Stream**: Configured in settings (default: `concert-data-stream`)
- **Format**: JSON records with enriched metadata
- **Purpose**:
  - Real-time processing
  - Event-driven workflows
  - Lambda triggers
  - Analytics

### 4. **Downstream Processing**
- **AWS Glue**: ETL jobs process S3 data
- **AWS Lambda**: Real-time processing of Kinesis streams
- **Amazon Redshift**: Final data warehouse for analytics

## Setup Instructions

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **API Credentials**:
   - Spotify: Client ID and Secret
   - Ticketmaster: API Key
3. **AWS Resources**:
   - S3 buckets (raw and processed)
   - Kinesis stream
   - IAM roles with appropriate permissions

### Step 1: Configure Environment Variables

Create or update your `.env` file:

```bash
# API Credentials
API_SPOTIFY_CLIENT_ID=your_spotify_client_id
API_SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
API_TICKETMASTER_API_KEY=your_ticketmaster_api_key

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# S3 Configuration
AWS_S3_BUCKET_RAW=concert-data-raw
AWS_S3_BUCKET_PROCESSED=concert-data-processed

# Kinesis Configuration
AWS_KINESIS_STREAM_NAME=concert-data-stream

# Rate Limiting
API_RATE_LIMIT_REQUESTS=100
API_RETRY_ATTEMPTS=3
API_RETRY_BACKOFF=1.0
```

### Step 2: Create AWS Resources

#### Create S3 Buckets

```bash
# Create raw data bucket
aws s3 mb s3://concert-data-raw --region us-east-1

# Create processed data bucket
aws s3 mb s3://concert-data-processed --region us-east-1

# Enable versioning (optional but recommended)
aws s3api put-bucket-versioning \
    --bucket concert-data-raw \
    --versioning-configuration Status=Enabled
```

#### Create Kinesis Stream

```bash
# Create Kinesis stream with 1 shard (adjust based on throughput needs)
aws kinesis create-stream \
    --stream-name concert-data-stream \
    --shard-count 1 \
    --region us-east-1

# Verify stream is active
aws kinesis describe-stream \
    --stream-name concert-data-stream \
    --region us-east-1
```

#### Create IAM Role (for Lambda/EC2)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::concert-data-raw/*",
        "arn:aws:s3:::concert-data-processed/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords",
        "kinesis:DescribeStream"
      ],
      "Resource": "arn:aws:kinesis:us-east-1:*:stream/concert-data-stream"
    }
  ]
}
```

### Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or using conda
conda install -c conda-forge boto3 structlog httpx pydantic
```

## Running the Pipeline

### Option 1: Manual Execution (Development/Testing)

```bash
# Run full ingestion pipeline
python -m src.services.external_apis.production_ingestion

# Run specific job types
python -m src.services.external_apis.scheduled_ingestion --job-type daily
python -m src.services.external_apis.scheduled_ingestion --job-type hourly
python -m src.services.external_apis.scheduled_ingestion --job-type artist_refresh
python -m src.services.external_apis.scheduled_ingestion --job-type venue_refresh
```

### Option 2: Cron Job (Linux/Mac)

Add to crontab (`crontab -e`):

```bash
# Daily ingestion at 2 AM UTC
0 2 * * * cd /path/to/project && python -m src.services.external_apis.scheduled_ingestion --job-type daily >> /var/log/ingestion_daily.log 2>&1

# Hourly event updates
0 * * * * cd /path/to/project && python -m src.services.external_apis.scheduled_ingestion --job-type hourly >> /var/log/ingestion_hourly.log 2>&1

# Artist refresh twice per week (Monday and Thursday at 3 AM)
0 3 * * 1,4 cd /path/to/project && python -m src.services.external_apis.scheduled_ingestion --job-type artist_refresh >> /var/log/ingestion_artists.log 2>&1

# Venue refresh weekly (Sunday at 4 AM)
0 4 * * 0 cd /path/to/project && python -m src.services.external_apis.scheduled_ingestion --job-type venue_refresh >> /var/log/ingestion_venues.log 2>&1
```

### Option 3: AWS Lambda (Recommended for Production)

#### Create Lambda Function

1. **Package the code**:
```bash
# Create deployment package
mkdir lambda_package
pip install -r requirements.txt -t lambda_package/
cp -r src/ lambda_package/
cd lambda_package && zip -r ../ingestion_lambda.zip . && cd ..
```

2. **Create Lambda function**:
```bash
aws lambda create-function \
    --function-name concert-data-ingestion \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-ingestion-role \
    --handler src.services.external_apis.scheduled_ingestion.lambda_handler \
    --zip-file fileb://ingestion_lambda.zip \
    --timeout 900 \
    --memory-size 512 \
    --environment Variables="{
        API_SPOTIFY_CLIENT_ID=xxx,
        API_SPOTIFY_CLIENT_SECRET=xxx,
        API_TICKETMASTER_API_KEY=xxx,
        AWS_S3_BUCKET_RAW=concert-data-raw,
        AWS_KINESIS_STREAM_NAME=concert-data-stream
    }"
```

3. **Create EventBridge rule for scheduling**:
```bash
# Daily ingestion at 2 AM UTC
aws events put-rule \
    --name concert-ingestion-daily \
    --schedule-expression "cron(0 2 * * ? *)"

# Add Lambda as target
aws events put-targets \
    --rule concert-ingestion-daily \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:YOUR_ACCOUNT:function:concert-data-ingestion","Input"='{"job_type":"daily"}'

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission \
    --function-name concert-data-ingestion \
    --statement-id concert-ingestion-daily \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:us-east-1:YOUR_ACCOUNT:rule/concert-ingestion-daily
```

### Option 4: AWS ECS/Fargate (For Long-Running Jobs)

Create a Docker container and run on ECS with scheduled tasks.

## Monitoring and Logging

### CloudWatch Logs

All logs are automatically sent to CloudWatch when running on Lambda:

```bash
# View logs
aws logs tail /aws/lambda/concert-data-ingestion --follow
```

### CloudWatch Metrics

Create custom metrics for monitoring:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='ConcertDataPipeline',
    MetricData=[
        {
            'MetricName': 'RecordsIngested',
            'Value': records_count,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'DataType', 'Value': 'artists'},
                {'Name': 'Source', 'Value': 'spotify'}
            ]
        }
    ]
)
```

### S3 Data Verification

```bash
# List ingested data
aws s3 ls s3://concert-data-raw/raw/spotify/artists/ --recursive

# Download and inspect a file
aws s3 cp s3://concert-data-raw/raw/spotify/artists/year=2024/month=11/day=08/artists_20241108_120000.json - | jq .
```

### Kinesis Stream Monitoring

```bash
# Get stream metrics
aws kinesis describe-stream-summary \
    --stream-name concert-data-stream

# View shard iterator
aws kinesis get-shard-iterator \
    --stream-name concert-data-stream \
    --shard-id shardId-000000000000 \
    --shard-iterator-type LATEST
```

## Data Persistence Details

### S3 Structure

```
s3://concert-data-raw/
├── raw/
│   ├── spotify/
│   │   └── artists/
│   │       └── year=2024/
│   │           └── month=11/
│   │               └── day=08/
│   │                   └── artists_20241108_120000.json
│   └── ticketmaster/
│       ├── venues/
│       │   └── year=2024/...
│       └── events/
│           └── year=2024/...
```

### JSON File Format

```json
{
  "ingestion_result": {
    "success": true,
    "source": "spotify",
    "data_type": "artists",
    "records_processed": 50,
    "records_successful": 48,
    "records_failed": 2,
    "timestamp": "2024-11-08T12:00:00Z"
  },
  "records": [
    {
      "artist_id": "spotify_4Z8W4fKeB5YxbusRsdQVPb",
      "name": "Radiohead",
      "genre": ["alternative rock", "art rock"],
      "popularity_score": 85.0,
      "spotify_id": "4Z8W4fKeB5YxbusRsdQVPb",
      "source": "spotify"
    }
  ]
}
```

### Kinesis Record Format

```json
{
  "artist_id": "spotify_4Z8W4fKeB5YxbusRsdQVPb",
  "name": "Radiohead",
  "genre": ["alternative rock", "art rock"],
  "popularity_score": 85.0,
  "spotify_id": "4Z8W4fKeB5YxbusRsdQVPb",
  "source": "spotify",
  "data_type": "artists",
  "ingestion_timestamp": "2024-11-08T12:00:00Z"
}
```

## Downstream Processing

### AWS Glue ETL

The data in S3 can be processed by AWS Glue jobs (already implemented in your project):

```python
# Glue job reads from S3 raw zone
from src.infrastructure.glue_etl_jobs import process_raw_data

# Process and move to processed zone
process_raw_data(
    source_bucket='concert-data-raw',
    target_bucket='concert-data-processed',
    data_type='artists'
)
```

### Lambda Processing (Kinesis Consumer)

```python
# Lambda function triggered by Kinesis
def lambda_handler(event, context):
    for record in event['Records']:
        # Decode Kinesis data
        payload = json.loads(base64.b64decode(record['kinesis']['data']))
        
        # Process record (e.g., write to Redshift, trigger alerts, etc.)
        process_record(payload)
```

### Redshift Loading

Data flows from S3 to Redshift via your existing infrastructure:

```python
from src.services.redshift_service import RedshiftService

# Load data from S3 to Redshift
redshift = RedshiftService()
redshift.load_from_s3(
    table='artists',
    s3_path='s3://concert-data-processed/artists/',
    format='JSON'
)
```

## Troubleshooting

### Common Issues

1. **API Rate Limiting**
   - Symptom: 429 errors in logs
   - Solution: Adjust `API_RATE_LIMIT_REQUESTS` in settings

2. **S3 Permission Errors**
   - Symptom: Access Denied errors
   - Solution: Verify IAM role has s3:PutObject permission

3. **Kinesis Throttling**
   - Symptom: ProvisionedThroughputExceededException
   - Solution: Increase shard count or implement batching

4. **Lambda Timeout**
   - Symptom: Task timed out after X seconds
   - Solution: Increase Lambda timeout or reduce batch size

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Cost Optimization

### Estimated Costs (Monthly)

- **S3 Storage**: ~$0.023/GB (Standard tier)
- **Kinesis**: ~$0.015/shard-hour + $0.014/million PUT requests
- **Lambda**: Free tier covers most usage, then $0.20/million requests
- **Data Transfer**: Minimal within same region

### Optimization Tips

1. **Use S3 Lifecycle Policies**: Move old data to Glacier
2. **Kinesis Shard Optimization**: Start with 1 shard, scale as needed
3. **Lambda Memory**: Right-size based on actual usage
4. **Batch Processing**: Process multiple records together

## Security Best Practices

1. **Encrypt data at rest** (S3 and Kinesis)
2. **Use IAM roles** instead of access keys
3. **Enable CloudTrail** for audit logging
4. **Rotate API credentials** regularly
5. **Use VPC endpoints** for private connectivity
6. **Enable S3 bucket versioning** for data recovery

## Next Steps

1. Set up CloudWatch alarms for failures
2. Implement data quality checks
3. Create data catalog in AWS Glue
4. Set up Athena for ad-hoc queries on S3 data
5. Configure Redshift Spectrum for querying S3 directly

## Support

For issues or questions:
- Check logs in CloudWatch
- Review API documentation (Spotify/Ticketmaster)
- Consult AWS documentation for service-specific issues