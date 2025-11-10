# Concert Data Platform - Documentation

Welcome to the Concert Data Platform documentation. This guide will help you understand, set up, and use the platform for ingesting, processing, and analyzing concert data.

## 📚 Documentation Structure

### 🔌 API Ingestion
External API integration for data collection from Spotify and Ticketmaster.

- **[API Connectors Summary](api-ingestion/API_CONNECTORS_SUMMARY.md)** - Overview of API implementation
- **[Production Ingestion Guide](api-ingestion/PRODUCTION_INGESTION_GUIDE.md)** - Complete production setup
- **[Production Ingestion Fixed](api-ingestion/PRODUCTION_INGESTION_FIXED.md)** - Working implementation guide
- **[Run Ingestion README](api-ingestion/RUN_INGESTION_README.md)** - Quick start guide

### 🌊 Kinesis Streaming
Real-time data streaming setup and configuration.

- **[Kinesis Setup Guide](kinesis/KINESIS_SETUP_GUIDE.md)** - Complete setup instructions
- **[Kinesis Quickstart](kinesis/KINESIS_QUICKSTART.md)** - Get started in 3 steps
- **[Kinesis Setup Success](kinesis/KINESIS_SETUP_SUCCESS.md)** - Verification and next steps

### 🗄️ Redshift Data Warehouse
Data warehouse setup and deployment.

- **[Redshift Deployment Checklist](redshift/REDSHIFT_DEPLOYMENT_CHECKLIST.md)** - Pre-deployment checklist
- **[Redshift Deployment Summary](redshift/REDSHIFT_DEPLOYMENT_SUMMARY.md)** - Deployment overview
- **[Redshift Quickstart](redshift/REDSHIFT_QUICKSTART.md)** - Quick setup guide

### 🏗️ Infrastructure
Additional infrastructure components and services.

- **[Recommendation Engine Summary](infrastructure/RECOMMENDATION_ENGINE_SUMMARY.md)** - ML recommendation system
- **[Lake Formation README](../src/infrastructure/LAKE_FORMATION_README.md)** - Data governance setup
- **[Redshift Setup Guide](../infrastructure/REDSHIFT_SETUP_GUIDE.md)** - Detailed Redshift configuration

## 🚀 Quick Start

### 1. Set Up API Ingestion

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API credentials in .env
API_SPOTIFY_CLIENT_ID=your_client_id
API_SPOTIFY_CLIENT_SECRET=your_client_secret
API_TICKETMASTER_API_KEY=your_api_key

# Run ingestion
python -m src.services.external_apis.production_ingestion
```

📖 **Read**: [Production Ingestion Fixed](api-ingestion/PRODUCTION_INGESTION_FIXED.md)

### 2. Set Up Kinesis Stream

```bash
# Run setup script
./infrastructure/setup_kinesis_for_ingestion.sh

# Verify setup
python verify_kinesis_setup.py
```

📖 **Read**: [Kinesis Quickstart](kinesis/KINESIS_QUICKSTART.md)

### 3. Set Up Redshift

```bash
# Run Redshift setup
./infrastructure/redshift_setup.sh

# Initialize schema
python infrastructure/initialize_redshift_schema.py
```

📖 **Read**: [Redshift Quickstart](redshift/REDSHIFT_QUICKSTART.md)

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    External APIs                             │
│              (Spotify & Ticketmaster)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Ingestion Service                          │
│  • Rate limiting                                             │
│  • Retry logic                                               │
│  • Data transformation                                       │
└────────────┬────────────────────────┬───────────────────────┘
             │                        │
             ▼                        ▼
┌────────────────────────┐  ┌────────────────────────┐
│      Amazon S3         │  │   Amazon Kinesis       │
│    (Data Lake)         │  │   (Streaming)          │
│  concert-data-raw      │  │  concert-data-stream   │
└────────────┬───────────┘  └───────────┬────────────┘
             │                           │
             ▼                           ▼
┌────────────────────────┐  ┌────────────────────────┐
│     AWS Glue ETL       │  │    AWS Lambda          │
│   (Batch Processing)   │  │  (Real-time)           │
└────────────┬───────────┘  └───────────┬────────────┘
             │                           │
             └───────────┬───────────────┘
                         ▼
             ┌────────────────────────┐
             │   Amazon Redshift      │
             │   (Data Warehouse)     │
             └────────────────────────┘
```

## 🎯 Common Tasks

### Ingest Data from APIs

```bash
# Full ingestion
python -m src.services.external_apis.production_ingestion

# Scheduled jobs
python -m src.services.external_apis.scheduled_ingestion --job-type daily
```

### Monitor Kinesis Stream

```bash
# Check stream status
aws kinesis describe-stream --stream-name concert-data-stream

# View metrics
python verify_kinesis_setup.py
```

### Query Redshift

```bash
# Connect to Redshift
psql -h your-cluster.redshift.amazonaws.com -U admin -d concerts

# Run example queries
python src/services/example_redshift_usage.py
```

## 📁 Project Structure

```
aws-immersion-demo-11192025/
├── docs/                          # 📚 Documentation (you are here)
│   ├── api-ingestion/            # API integration docs
│   ├── kinesis/                  # Streaming docs
│   ├── redshift/                 # Data warehouse docs
│   └── infrastructure/           # Infrastructure docs
├── src/                          # Source code
│   ├── config/                   # Configuration
│   ├── models/                   # Data models
│   ├── services/                 # Business logic
│   │   └── external_apis/       # API connectors
│   └── infrastructure/           # AWS infrastructure code
├── infrastructure/               # Setup scripts
│   ├── setup_kinesis_for_ingestion.sh
│   ├── redshift_setup.sh
│   └── ...
└── .env                          # Environment variables
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Credentials
API_SPOTIFY_CLIENT_ID=your_spotify_client_id
API_SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
API_TICKETMASTER_API_KEY=your_ticketmaster_api_key

# AWS Configuration
AWS_REGION=us-east-1
AWS_S3_BUCKET_RAW=concert-data-raw
AWS_S3_BUCKET_PROCESSED=concert-data-processed
AWS_KINESIS_STREAM_NAME=concert-data-stream

# Redshift Configuration
AWS_REDSHIFT_HOST=your-cluster.redshift.amazonaws.com
AWS_REDSHIFT_DATABASE=concerts
AWS_REDSHIFT_USER=admin
AWS_REDSHIFT_PASSWORD=your_password
```

## 🧪 Testing

### Run Tests

```bash
# API connector tests
python -m pytest src/services/external_apis/test_api_connectors.py -v

# Validation scripts
python demo_production_flow.py
python verify_kinesis_setup.py
```

### Validation Scripts

- `demo_production_flow.py` - Test API ingestion
- `verify_kinesis_setup.py` - Verify Kinesis configuration
- `validate_redshift_implementation.py` - Test Redshift connection

## 💰 Cost Estimates

### Monthly Costs (Development)

| Service | Usage | Cost |
|---------|-------|------|
| S3 | 100 GB | ~$2.30 |
| Kinesis | 1 shard | ~$11 |
| Redshift | dc2.large (1 node) | ~$180 |
| Glue | 10 DPU-hours | ~$4.40 |
| Lambda | 1M requests | Free tier |
| **Total** | | **~$198/month** |

### Cost Optimization Tips

1. Use Redshift pause/resume for development
2. Start with 1 Kinesis shard, scale as needed
3. Use S3 lifecycle policies for old data
4. Leverage AWS free tier where possible

## 🆘 Troubleshooting

### Common Issues

#### API Credentials Not Working

```bash
# Check environment variables
python -c "import os; from src.config.environment import load_env_file; load_env_file(); print(os.getenv('API_SPOTIFY_CLIENT_ID'))"
```

#### Kinesis Stream Not Found

```bash
# List streams
aws kinesis list-streams --region us-east-1

# Create stream
./infrastructure/setup_kinesis_for_ingestion.sh
```

#### Redshift Connection Failed

```bash
# Test connection
psql -h $AWS_REDSHIFT_HOST -U $AWS_REDSHIFT_USER -d $AWS_REDSHIFT_DATABASE

# Check security groups and VPC settings
```

## 📖 Additional Resources

### AWS Documentation

- [Amazon Kinesis](https://docs.aws.amazon.com/kinesis/)
- [Amazon Redshift](https://docs.aws.amazon.com/redshift/)
- [AWS Glue](https://docs.aws.amazon.com/glue/)
- [Amazon S3](https://docs.aws.amazon.com/s3/)

### API Documentation

- [Spotify Web API](https://developer.spotify.com/documentation/web-api/)
- [Ticketmaster Discovery API](https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/)

### Project Documentation

- [Main README](../README.md)
- [Spec Requirements](../.kiro/specs/data-readiness-ai-demo/requirements.md)
- [Spec Design](../.kiro/specs/data-readiness-ai-demo/design.md)

## 🎉 Success Metrics

Track your implementation progress:

- ✅ API ingestion working
- ✅ Kinesis stream active
- ✅ S3 data lake populated
- ✅ Redshift cluster running
- ✅ ETL jobs processing data
- ✅ Queries returning results

---

**Last Updated**: November 9, 2025  
**Version**: 1.0  
**Status**: Production Ready