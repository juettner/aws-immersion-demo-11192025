# Kinesis Streaming Documentation

Documentation for Amazon Kinesis Data Streams setup and configuration for real-time data ingestion.

## 📄 Documents

### Quick Start
- **[Kinesis Quickstart](KINESIS_QUICKSTART.md)** ⭐ **START HERE**
  - Get started in 3 steps
  - Setup options (Bash, Python, CLI)
  - Verification steps
  - Cost estimates

- **[Kinesis Setup Success](KINESIS_SETUP_SUCCESS.md)**
  - Setup confirmation
  - Stream details
  - Next steps
  - Integration guide

### Comprehensive Guide
- **[Kinesis Setup Guide](KINESIS_SETUP_GUIDE.md)**
  - Complete setup instructions
  - Manual and automated options
  - Lambda consumer setup
  - Monitoring and troubleshooting
  - Advanced configuration

## 🚀 Quick Setup

### Option 1: Automated Script (Recommended)

```bash
./infrastructure/setup_kinesis_for_ingestion.sh
```

### Option 2: Python Script

```bash
python infrastructure/setup_kinesis_ingestion.py
```

### Option 3: Verify Existing Setup

```bash
python verify_kinesis_setup.py
```

## 📊 What Gets Created

- **Stream Name**: `concert-data-stream`
- **Shard Count**: 1 (1 MB/s write, 2 MB/s read)
- **Retention**: 24 hours
- **Encryption**: Enabled (AWS managed key)
- **Enhanced Monitoring**: Enabled
- **IAM Policy**: `ConcertDataIngestionKinesisPolicy`

## 🔗 Stream Details

```
Stream ARN: arn:aws:kinesis:us-east-1:ACCOUNT_ID:stream/concert-data-stream
Status: ACTIVE
Region: us-east-1
```

## 💰 Cost

- **1 shard**: ~$11/month
- **PUT operations**: ~$0.56/month (1M records)
- **Total**: ~$12/month

## 🔍 Verification

```bash
# Check stream status
aws kinesis describe-stream \
    --stream-name concert-data-stream \
    --region us-east-1

# Run verification script
python verify_kinesis_setup.py
```

## 📈 Monitoring

### CloudWatch Console
```
https://console.aws.amazon.com/kinesis/home?region=us-east-1#/streams/details/concert-data-stream/monitoring
```

### Key Metrics
- **IncomingRecords**: Records written per second
- **IncomingBytes**: Data volume
- **WriteProvisionedThroughputExceeded**: Throttling events
- **IteratorAgeMilliseconds**: Consumer lag

## 🔗 Related Documentation

- [API Ingestion](../api-ingestion/PRODUCTION_INGESTION_FIXED.md) - Data source
- [Main Documentation](../README.md) - Full documentation index
- [Setup Scripts](../../infrastructure/) - Automation scripts

## 🆘 Troubleshooting

### Stream Not Found
```bash
aws kinesis list-streams --region us-east-1
```

### Permission Denied
```bash
# Check IAM permissions
aws iam list-attached-user-policies --user-name YOUR_USERNAME
```

### Throttling
```bash
# Increase shard count
aws kinesis update-shard-count \
    --stream-name concert-data-stream \
    --target-shard-count 2 \
    --scaling-type UNIFORM_SCALING
```

## ✅ Success Checklist

- ✅ Stream created and active
- ✅ Enhanced monitoring enabled
- ✅ Encryption configured
- ✅ IAM policy created
- ✅ Test record sent successfully
- ✅ CloudWatch metrics available

---

[← Back to Main Documentation](../README.md)