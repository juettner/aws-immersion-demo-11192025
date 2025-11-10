# Kinesis Stream Setup Guide for API Data Ingestion

## Quick Start

### Option 1: Automated Setup (Bash Script)

```bash
# Run the setup script
./infrastructure/setup_kinesis_for_ingestion.sh
```

This script will:
- ✅ Create the Kinesis stream
- ✅ Configure enhanced monitoring
- ✅ Enable encryption (optional)
- ✅ Add tags
- ✅ Create IAM policy
- ✅ Send test record
- ✅ Display stream details

### Option 2: Python Setup Script

```bash
# Run the Python setup
python infrastructure/setup_kinesis_ingestion.py
```

This provides the same functionality with Python integration.

### Option 3: Manual AWS CLI Setup

```bash
# 1. Create the stream
aws kinesis create-stream \
    --stream-name concert-data-stream \
    --shard-count 1 \
    --region us-east-1

# 2. Wait for stream to become active
aws kinesis wait stream-exists \
    --stream-name concert-data-stream \
    --region us-east-1

# 3. Enable enhanced monitoring
aws kinesis enable-enhanced-monitoring \
    --stream-name concert-data-stream \
    --shard-level-metrics IncomingBytes IncomingRecords OutgoingBytes OutgoingRecords \
    --region us-east-1

# 4. Enable encryption (optional)
aws kinesis start-stream-encryption \
    --stream-name concert-data-stream \
    --encryption-type KMS \
    --key-id alias/aws/kinesis \
    --region us-east-1

# 5. Add tags
aws kinesis add-tags-to-stream \
    --stream-name concert-data-stream \
    --tags Project=ConcertDataPlatform Environment=development \
    --region us-east-1
```

## Configuration

### Environment Variables

Make sure these are set in your `.env` file:

```bash
# Kinesis Configuration
AWS_KINESIS_STREAM_NAME=concert-data-stream
AWS_KINESIS_SHARD_COUNT=1

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Shard Count Sizing

Choose shard count based on your expected throughput:

| Shard Count | Write Capacity | Read Capacity | Cost/Month |
|-------------|----------------|---------------|------------|
| 1 | 1 MB/s (1000 records/s) | 2 MB/s | ~$11 |
| 2 | 2 MB/s (2000 records/s) | 4 MB/s | ~$22 |
| 5 | 5 MB/s (5000 records/s) | 10 MB/s | ~$55 |

**Recommendation**: Start with 1 shard and scale up if needed.

## Verification

### Check Stream Status

```bash
# Describe the stream
aws kinesis describe-stream \
    --stream-name concert-data-stream \
    --region us-east-1

# List all streams
aws kinesis list-streams --region us-east-1
```

### Send Test Record

```bash
# Send a test record
aws kinesis put-record \
    --stream-name concert-data-stream \
    --partition-key test \
    --data '{"test": true, "timestamp": "2024-11-08T12:00:00Z"}' \
    --region us-east-1
```

### Read from Stream

```bash
# Get shard ID
SHARD_ID=$(aws kinesis list-shards \
    --stream-name concert-data-stream \
    --region us-east-1 \
    --query 'Shards[0].ShardId' \
    --output text)

# Get shard iterator
SHARD_ITERATOR=$(aws kinesis get-shard-iterator \
    --stream-name concert-data-stream \
    --shard-id $SHARD_ID \
    --shard-iterator-type LATEST \
    --region us-east-1 \
    --query 'ShardIterator' \
    --output text)

# Get records
aws kinesis get-records \
    --shard-iterator $SHARD_ITERATOR \
    --region us-east-1
```

## Integration with API Ingestion

### Using the Production Pipeline

```python
import asyncio
from src.services.external_apis.production_ingestion import ProductionDataPipeline

async def main():
    async with ProductionDataPipeline() as pipeline:
        # Run full ingestion - data will be streamed to Kinesis
        results = await pipeline.run_full_ingestion()
        print(f"Streamed {results['summary']['total_records_streamed_to_kinesis']} records")

asyncio.run(main())
```

### Direct Kinesis Integration

```python
import boto3
import json
from src.config.settings import settings

# Create Kinesis client
kinesis = boto3.client('kinesis', **settings.get_aws_credentials())

# Send record
record = {
    'artist_id': 'spotify_123',
    'name': 'Example Artist',
    'popularity_score': 85.0
}

response = kinesis.put_record(
    StreamName=settings.aws.kinesis_stream_name,
    Data=json.dumps(record).encode('utf-8'),
    PartitionKey=record['artist_id']
)

print(f"Record sent to shard: {response['ShardId']}")
```

## Monitoring

### CloudWatch Metrics

Key metrics to monitor:

1. **IncomingRecords**: Number of records written
2. **IncomingBytes**: Data volume written
3. **WriteProvisionedThroughputExceeded**: Throttling events
4. **IteratorAgeMilliseconds**: Consumer lag

### View Metrics in Console

```
https://console.aws.amazon.com/kinesis/home?region=us-east-1#/streams/details/concert-data-stream/monitoring
```

### CLI Metrics Query

```bash
# Get incoming records for last 5 minutes
aws cloudwatch get-metric-statistics \
    --namespace AWS/Kinesis \
    --metric-name IncomingRecords \
    --dimensions Name=StreamName,Value=concert-data-stream \
    --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 60 \
    --statistics Sum \
    --region us-east-1
```

## Lambda Consumer Setup

### Create Lambda Function

```python
# lambda_function.py
import json
import base64

def lambda_handler(event, context):
    """Process records from Kinesis stream."""
    
    for record in event['Records']:
        # Decode Kinesis data
        payload = json.loads(base64.b64decode(record['kinesis']['data']))
        
        # Process the record
        print(f"Processing {payload.get('data_type')}: {payload.get('name', 'N/A')}")
        
        # Your processing logic here
        # - Write to Redshift
        # - Trigger notifications
        # - Update caches
        # - etc.
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Processed {len(event["Records"])} records')
    }
```

### Configure Event Source Mapping

```bash
# Create event source mapping
aws lambda create-event-source-mapping \
    --function-name concert-data-processor \
    --event-source-arn arn:aws:kinesis:us-east-1:ACCOUNT_ID:stream/concert-data-stream \
    --starting-position LATEST \
    --batch-size 100 \
    --maximum-batching-window-in-seconds 5 \
    --region us-east-1
```

## Troubleshooting

### Stream Not Found

```bash
# Verify stream exists
aws kinesis list-streams --region us-east-1

# Check region
echo $AWS_REGION
```

### Permission Denied

```bash
# Check IAM permissions
aws iam get-user

# Verify policy is attached
aws iam list-attached-user-policies --user-name YOUR_USERNAME
```

### Throttling (WriteProvisionedThroughputExceeded)

**Solutions:**
1. Increase shard count
2. Implement exponential backoff
3. Batch records using `put_records` instead of `put_record`

```bash
# Update shard count
aws kinesis update-shard-count \
    --stream-name concert-data-stream \
    --target-shard-count 2 \
    --scaling-type UNIFORM_SCALING \
    --region us-east-1
```

### High Iterator Age

This means consumers are falling behind. Solutions:
1. Increase consumer processing capacity
2. Add more Lambda concurrent executions
3. Optimize consumer code
4. Increase shard count

## Cost Optimization

### Pricing (us-east-1)

- **Shard Hour**: $0.015/hour = ~$11/month per shard
- **PUT Payload Units**: $0.014 per million units (25 KB per unit)
- **Extended Retention**: $0.020 per shard-hour (beyond 24 hours)

### Cost Reduction Tips

1. **Right-size shard count**: Start small, scale as needed
2. **Batch records**: Use `put_records` to reduce API calls
3. **Optimize record size**: Keep records under 25 KB
4. **Use standard retention**: 24 hours is usually sufficient
5. **Monitor usage**: Set up CloudWatch alarms for unexpected spikes

### Example Monthly Cost

For 1 shard with 1M records/day (avg 1 KB each):
- Shard cost: $11/month
- PUT cost: ~$0.56/month (40 PUT units per 1M records)
- **Total**: ~$12/month

## Advanced Configuration

### Increase Retention Period

```bash
# Increase to 7 days (168 hours)
aws kinesis increase-stream-retention-period \
    --stream-name concert-data-stream \
    --retention-period-hours 168 \
    --region us-east-1
```

### Enable On-Demand Mode

```bash
# Switch to on-demand (auto-scaling)
aws kinesis update-stream-mode \
    --stream-arn arn:aws:kinesis:us-east-1:ACCOUNT_ID:stream/concert-data-stream \
    --stream-mode-details StreamMode=ON_DEMAND \
    --region us-east-1
```

### Fan-Out Consumers

For multiple consumers reading at full speed:

```bash
# Register consumer
aws kinesis register-stream-consumer \
    --stream-arn arn:aws:kinesis:us-east-1:ACCOUNT_ID:stream/concert-data-stream \
    --consumer-name my-consumer \
    --region us-east-1
```

## Integration with Existing Infrastructure

Your project already has Kinesis infrastructure code. Here's how it integrates:

### Existing Components

1. **`src/infrastructure/kinesis_client.py`**: Kinesis client wrapper
2. **`src/services/stream_producer.py`**: Stream producer service
3. **`src/services/kinesis_integration_service.py`**: Integration service
4. **`src/infrastructure/lambda_functions.py`**: Lambda consumers

### Using Existing Infrastructure

```python
# Use existing Kinesis client
from src.infrastructure.kinesis_client import KinesisClient

kinesis = KinesisClient()
kinesis.put_record(
    stream_name='concert-data-stream',
    data={'artist_id': 'spotify_123'},
    partition_key='spotify_123'
)

# Use stream producer
from src.services.stream_producer import StreamProducer

producer = StreamProducer()
await producer.send_artist_data(artist_data)
```

## Next Steps

1. ✅ Set up Kinesis stream (this guide)
2. ✅ Run API ingestion pipeline
3. ⬜ Set up Lambda consumers
4. ⬜ Configure CloudWatch alarms
5. ⬜ Set up Kinesis Data Firehose (optional, for S3 backup)
6. ⬜ Implement Kinesis Data Analytics (optional, for real-time analytics)

## Resources

- [AWS Kinesis Documentation](https://docs.aws.amazon.com/kinesis/)
- [Kinesis Best Practices](https://docs.aws.amazon.com/streams/latest/dev/best-practices.html)
- [Kinesis Pricing](https://aws.amazon.com/kinesis/data-streams/pricing/)
- [CloudWatch Metrics for Kinesis](https://docs.aws.amazon.com/streams/latest/dev/monitoring-with-cloudwatch.html)