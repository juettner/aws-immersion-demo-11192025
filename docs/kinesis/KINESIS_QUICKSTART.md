# Kinesis Setup - Quick Start Guide

## TL;DR - Get Started in 3 Steps

```bash
# 1. Set up the Kinesis stream
./infrastructure/setup_kinesis_for_ingestion.sh

# 2. Verify it's working
python verify_kinesis_setup.py

# 3. Run the ingestion pipeline
python -m src.services.external_apis.production_ingestion
```

That's it! Your data will now flow from APIs → Kinesis → downstream processing.

---

## What Gets Created

When you run the setup, you'll get:

✅ **Kinesis Data Stream**
- Name: `concert-data-stream` (configurable in `.env`)
- 1 shard (handles 1 MB/s writes, 2 MB/s reads)
- 24-hour data retention
- Enhanced monitoring enabled
- Server-side encryption (optional)

✅ **IAM Policy**
- Policy name: `ConcertDataIngestionKinesisPolicy`
- Permissions for put/get records
- Ready to attach to Lambda or EC2 roles

✅ **CloudWatch Monitoring**
- Metrics for incoming/outgoing records
- Throughput monitoring
- Iterator age tracking

---

## Setup Options

### Option 1: Bash Script (Recommended)

```bash
./infrastructure/setup_kinesis_for_ingestion.sh
```

**Pros:**
- Fully automated
- Interactive prompts
- Comprehensive error handling
- Creates IAM policy automatically

### Option 2: Python Script

```bash
python infrastructure/setup_kinesis_ingestion.py
```

**Pros:**
- Integrates with existing Python code
- Programmatic access
- Easy to customize

### Option 3: Manual AWS CLI

```bash
# Create stream
aws kinesis create-stream \
    --stream-name concert-data-stream \
    --shard-count 1 \
    --region us-east-1

# Wait for active
aws kinesis wait stream-exists \
    --stream-name concert-data-stream
```

**Pros:**
- Full control
- No dependencies
- Good for CI/CD

---

## Verification

### Quick Check

```bash
python verify_kinesis_setup.py
```

This will:
- ✅ Check if stream exists
- ✅ Verify permissions
- ✅ Send test record
- ✅ Check CloudWatch metrics

### Manual Verification

```bash
# Check stream status
aws kinesis describe-stream \
    --stream-name concert-data-stream \
    --region us-east-1

# Send test record
aws kinesis put-record \
    --stream-name concert-data-stream \
    --partition-key test \
    --data '{"test": true}' \
    --region us-east-1
```

---

## Integration with API Ingestion

Once Kinesis is set up, your API ingestion pipeline automatically streams data to it:

```python
# This code already works - no changes needed!
from src.services.external_apis.production_ingestion import ProductionDataPipeline

async with ProductionDataPipeline() as pipeline:
    results = await pipeline.run_full_ingestion()
    # Data automatically goes to:
    # - S3: s3://concert-data-raw/raw/...
    # - Kinesis: concert-data-stream
```

### Data Flow

```
Spotify API ──┐
              ├──> Ingestion Service ──┬──> S3 (Raw Data Lake)
Ticketmaster ─┘                        └──> Kinesis Stream
                                              │
                                              ├──> Lambda (Real-time)
                                              ├──> Kinesis Analytics
                                              └──> Kinesis Firehose
```

---

## What Happens to the Data?

### In Kinesis Stream

Records look like this:

```json
{
  "artist_id": "spotify_4Z8W4fKeB5YxbusRsdQVPb",
  "name": "Radiohead",
  "genre": ["alternative rock", "art rock"],
  "popularity_score": 85.0,
  "source": "spotify",
  "data_type": "artists",
  "ingestion_timestamp": "2024-11-08T12:00:00Z"
}
```

### Downstream Processing

1. **Lambda Functions** (real-time)
   - Process records as they arrive
   - Write to Redshift
   - Trigger notifications
   - Update caches

2. **Kinesis Data Analytics** (optional)
   - Real-time SQL queries
   - Aggregations
   - Anomaly detection

3. **Kinesis Firehose** (optional)
   - Automatic S3 backup
   - Data transformation
   - Compression

---

## Monitoring

### CloudWatch Console

View metrics at:
```
https://console.aws.amazon.com/kinesis/home?region=us-east-1#/streams/details/concert-data-stream/monitoring
```

### Key Metrics to Watch

| Metric | What It Means | Alert If |
|--------|---------------|----------|
| IncomingRecords | Records written/sec | Drops to 0 unexpectedly |
| WriteProvisionedThroughputExceeded | Throttling events | > 0 consistently |
| IteratorAgeMilliseconds | Consumer lag | > 60000 (1 minute) |
| IncomingBytes | Data volume | Exceeds shard capacity |

### CLI Monitoring

```bash
# Get recent metrics
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

---

## Troubleshooting

### Stream Not Found

```bash
# List all streams
aws kinesis list-streams --region us-east-1

# Check if you're in the right region
echo $AWS_REGION
```

### Permission Denied

```bash
# Check your IAM permissions
aws iam get-user

# Attach the policy
aws iam attach-user-policy \
    --user-name YOUR_USERNAME \
    --policy-arn arn:aws:iam::ACCOUNT_ID:policy/ConcertDataIngestionKinesisPolicy
```

### Throttling Errors

**Problem**: `WriteProvisionedThroughputExceeded`

**Solution**: Increase shard count

```bash
aws kinesis update-shard-count \
    --stream-name concert-data-stream \
    --target-shard-count 2 \
    --scaling-type UNIFORM_SCALING \
    --region us-east-1
```

---

## Cost

### Pricing (us-east-1)

- **Shard Hour**: $0.015/hour = **~$11/month per shard**
- **PUT Payload Units**: $0.014 per million units
- **Extended Retention**: $0.020 per shard-hour (beyond 24 hours)

### Example Costs

| Scenario | Shards | Records/Day | Monthly Cost |
|----------|--------|-------------|--------------|
| Development | 1 | 100K | ~$11 |
| Production (Small) | 2 | 1M | ~$23 |
| Production (Medium) | 5 | 10M | ~$58 |

**Tip**: Start with 1 shard and scale up as needed.

---

## Next Steps

### 1. Set Up Lambda Consumer

Create a Lambda function to process the stream:

```python
# lambda_function.py
import json
import base64

def lambda_handler(event, context):
    for record in event['Records']:
        data = json.loads(base64.b64decode(record['kinesis']['data']))
        print(f"Processing: {data.get('name')}")
        # Your processing logic here
```

Deploy and connect to stream:

```bash
aws lambda create-event-source-mapping \
    --function-name concert-data-processor \
    --event-source-arn arn:aws:kinesis:REGION:ACCOUNT:stream/concert-data-stream \
    --starting-position LATEST
```

### 2. Set Up CloudWatch Alarms

```bash
# Alert on throttling
aws cloudwatch put-metric-alarm \
    --alarm-name kinesis-throttling \
    --metric-name WriteProvisionedThroughputExceeded \
    --namespace AWS/Kinesis \
    --statistic Sum \
    --period 300 \
    --threshold 1 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=StreamName,Value=concert-data-stream
```

### 3. Enable Kinesis Data Firehose (Optional)

Automatically backup to S3:

```bash
aws firehose create-delivery-stream \
    --delivery-stream-name concert-data-backup \
    --kinesis-stream-source-configuration \
        KinesisStreamARN=arn:aws:kinesis:REGION:ACCOUNT:stream/concert-data-stream,RoleARN=arn:aws:iam::ACCOUNT:role/firehose-role \
    --s3-destination-configuration \
        BucketARN=arn:aws:s3:::concert-data-raw,Prefix=kinesis-backup/
```

---

## Resources

- **Full Setup Guide**: `KINESIS_SETUP_GUIDE.md`
- **Production Ingestion Guide**: `PRODUCTION_INGESTION_GUIDE.md`
- **API Connectors Summary**: `API_CONNECTORS_SUMMARY.md`
- **AWS Kinesis Docs**: https://docs.aws.amazon.com/kinesis/

---

## Support

If you encounter issues:

1. Run verification: `python verify_kinesis_setup.py`
2. Check CloudWatch logs
3. Review IAM permissions
4. Verify region configuration

For detailed troubleshooting, see `KINESIS_SETUP_GUIDE.md`.