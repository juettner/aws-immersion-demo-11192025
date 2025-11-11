# Concert Data Platform - Quick Start Guide

Get the entire platform running in minutes with this step-by-step guide.

## Prerequisites

- Python 3.9+
- Node.js 18+
- AWS Account with credentials configured
- AWS CLI installed
- Git

## 1. Initial Setup (5 minutes)

```bash
# Clone and navigate to project
cd concert-data-platform

# Set up Python environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt

# Set up frontend
cd web
npm install
cd ..
```

## 2. Configure Environment (2 minutes)

Create `.env` file in project root:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# External APIs (optional for basic testing)
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
TICKETMASTER_API_KEY=your_ticketmaster_api_key

# Redshift (if using)
REDSHIFT_HOST=your-cluster.region.redshift.amazonaws.com
REDSHIFT_PORT=5439
REDSHIFT_DATABASE=concert_data
REDSHIFT_USER=admin
REDSHIFT_PASSWORD=your_password

# Bedrock AgentCore
AGENTCORE_AGENT_ID=your_agent_id
AGENTCORE_AGENT_ALIAS_ID=your_alias_id
```

## 3. AWS Infrastructure Setup

### Option A: Quick Demo (No AWS Resources)

```bash
# Test services locally without AWS
python src/services/example_chatbot_usage.py
python src/services/example_recommendation_usage.py
```

### Option B: Full AWS Setup (30 minutes)

```bash
# 1. Set up Kinesis streams
bash infrastructure/setup_kinesis_for_ingestion.sh

# 2. Set up Redshift (if needed)
bash infrastructure/redshift_setup.sh

# 3. Initialize Redshift schema
python infrastructure/initialize_redshift_schema.py

# 4. Verify setup
python verify_kinesis_setup.py
python validate_redshift_implementation.py
```

## 4. Start the Backend APIs (1 minute)

```bash
# Terminal 1: Start ML API
python src/api/ml_api.py
# Runs on http://localhost:8000

# Terminal 2: Start Chatbot API
python src/api/chatbot_api.py
# Runs on http://localhost:8001
```

## 5. Start the Frontend (1 minute)

```bash
# Terminal 3: Start React app
cd web
npm run dev
# Runs on http://localhost:5173
```

## 6. Access the Application

Open your browser to:
- **Frontend**: http://localhost:5173
- **ML API Docs**: http://localhost:8000/docs
- **Chatbot API Docs**: http://localhost:8001/docs

## Quick Feature Tests

### Test Data Ingestion

```bash
# Ingest sample data from APIs
python src/services/external_apis/example_usage.py

# Or use file upload
python src/services/file_processor.py
```

### Test ML Models

```bash
# Venue popularity ranking
python src/services/example_venue_popularity_usage.py

# Ticket sales prediction
python src/services/example_ticket_sales_prediction_usage.py

# Recommendations
python src/services/example_recommendation_usage.py
```

### Test AI Chatbot

```bash
# Test chatbot service
python src/services/example_chatbot_usage.py

# Or use the web interface at http://localhost:5173/chatbot
```

### Test Data Analysis

```bash
# Natural language to SQL
python src/services/example_nl_to_sql_usage.py

# Data analysis
python src/services/example_data_analysis_usage.py

# Visualizations
python src/services/example_visualization_usage.py
```

## Common Commands Cheat Sheet

### Backend

```bash
# Activate Python environment
source .venv/bin/activate

# Run validation scripts
python validate_chatbot_service.py
python validate_recommendation_engine.py
python validate_ticket_sales_prediction.py

# Run tests
pytest src/services/test_*.py

# Format code
black src/
flake8 src/
```

### Frontend

```bash
cd web

# Development
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint and format
npm run lint
npm run format
```

### AWS Operations

```bash
# Deploy Lambda functions
python src/infrastructure/lambda_deployment.py

# Run Glue ETL jobs
python src/services/example_glue_etl_usage.py

# Load data to Redshift
python src/infrastructure/redshift_data_loader.py

# Test production pipeline
python test_production_pipeline.py
```

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend won't start
```bash
cd web
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### AWS Connection Issues
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check region
echo $AWS_REGION
```

### Database Connection Issues
```bash
# Test Redshift connection
python -c "from src.infrastructure.redshift_client import RedshiftClient; client = RedshiftClient(); print('Connected!')"
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│                   http://localhost:5173                      │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             ▼                                ▼
┌────────────────────────┐      ┌────────────────────────────┐
│   ML API (FastAPI)     │      │  Chatbot API (FastAPI)     │
│   localhost:8000       │      │  localhost:8001            │
└────────┬───────────────┘      └────────┬───────────────────┘
         │                               │
         ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS Services Layer                        │
│  • Kinesis (Streaming)    • Bedrock AgentCore (AI)         │
│  • Redshift (Warehouse)   • SageMaker (ML Models)          │
│  • Glue (ETL)             • DynamoDB (Conversations)        │
│  • S3 (Storage)           • Lambda (Processing)             │
└─────────────────────────────────────────────────────────────┘
```

## Next Steps

1. **Load Sample Data**: Run `python demo_production_flow.py`
2. **Explore APIs**: Visit http://localhost:8000/docs
3. **Try Chatbot**: Open http://localhost:5173/chatbot
4. **View Documentation**: Check `docs/DOCUMENTATION_INDEX.md`

## Production Deployment

For production deployment:

```bash
# Build frontend
cd web
npm run build

# Deploy to AWS
# (Add your deployment scripts here)

# Run production ingestion
bash run_production_ingestion.sh
```

## Support & Documentation

- **Full Documentation**: `docs/DOCUMENTATION_INDEX.md`
- **API Reference**: `docs/api/README.md`
- **Infrastructure Guides**: `docs/infrastructure/README.md`
- **Feature Summaries**: `docs/features/`

## Quick Health Check

Run this to verify everything is working:

```bash
# Backend health
curl http://localhost:8000/health
curl http://localhost:8001/health

# Frontend health
curl http://localhost:5173

# AWS connectivity
python -c "import boto3; print('AWS OK' if boto3.client('sts').get_caller_identity() else 'AWS FAIL')"
```

---

**Time to Full Setup**: ~10 minutes (local) | ~45 minutes (with AWS)

**Minimum to Start Coding**: Steps 1-2 only (2 minutes)
