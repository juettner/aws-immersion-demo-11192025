# Troubleshooting Guide

## Common Issues and Solutions

### Python Module Import Errors

#### Issue: `ModuleNotFoundError: No module named 'src'`

**Error Example**:
```
Traceback (most recent call last):
  File "/path/to/src/api/chatbot_api.py", line 17, in <module>
    from src.services.chatbot_service import (
ModuleNotFoundError: No module named 'src'
```

**Cause**: Python can't find the `src` module because the project root isn't in the Python path.

**Solutions**:

1. **Use the helper scripts** (Recommended):
```bash
# For chatbot API
./run_chatbot.sh

# For ML API
./run_ml_api.sh
```

2. **Set PYTHONPATH manually**:
```bash
# From project root
PYTHONPATH=. python src/api/chatbot_api.py

# Or export it for the session
export PYTHONPATH="${PWD}:${PYTHONPATH}"
python src/api/chatbot_api.py
```

3. **Use Python's -m flag**:
```bash
# Run as a module
python -m src.api.chatbot_api
```

4. **Add to your shell profile** (Permanent fix):
```bash
# Add to ~/.zshrc or ~/.bashrc
export PYTHONPATH="/Users/juettner/Projects/aws-immersion-demo-11192025:${PYTHONPATH}"
```

---

### Chatbot Service Issues

#### Issue: Chatbot service won't start

**Check 1: Port already in use**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 $(lsof -t -i :8000)
```

**Check 2: Missing dependencies**
```bash
# Verify all dependencies are installed
pip install -r requirements.txt

# Check specific imports
python -c "from fastapi import FastAPI; print('FastAPI OK')"
python -c "import boto3; print('boto3 OK')"
```

**Check 3: AWS credentials**
```bash
# Verify AWS credentials are configured
aws configure list

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

**Check 4: Environment variables**
```bash
# Check .env file exists
cat .env | grep -E "AWS_|BEDROCK_"

# Verify settings can be loaded
python -c "from src.config.settings import Settings; s = Settings.from_env(); print('Settings OK')"
```

#### Issue: Chatbot returns errors

**Check logs**:
```bash
# If running in background, check logs
tail -f chatbot.log

# Or run in foreground to see errors
./run_chatbot.sh
```

**Common errors**:
- **"Agent not found"**: Check `BEDROCK_AGENT_ID` in `.env`
- **"Access denied"**: Verify IAM permissions for Bedrock
- **"Timeout"**: Check network connectivity to AWS services

---

### Database Connection Issues

#### Issue: Cannot connect to Redshift

**Check 1: Redshift cluster is running**
```bash
# Check cluster status
aws redshift describe-clusters --cluster-identifier your-cluster-name

# Verify endpoint
python -c "from src.config.settings import Settings; s = Settings.from_env(); print(s.aws.redshift_host)"
```

**Check 2: Network connectivity**
```bash
# Test connection
nc -zv your-redshift-endpoint.amazonaws.com 5439

# Or use psql
psql -h your-redshift-endpoint.amazonaws.com -U admin -d concerts -p 5439
```

**Check 3: Credentials**
```bash
# Verify credentials in .env
cat .env | grep REDSHIFT

# Test connection with Python
python validate_redshift_implementation.py
```

---

### ML Model Issues

#### Issue: Model predictions failing

**Check 1: Models are trained**
```bash
# Check if model files exist
ls -la models/

# Retrain if needed
python train_demo_models.py
```

**Check 2: Data availability**
```bash
# Verify data in Redshift
python -c "
from src.infrastructure.redshift_client import RedshiftClient
from src.config.settings import Settings
client = RedshiftClient(Settings.from_env().aws)
result = client.execute_query('SELECT COUNT(*) FROM concerts.artists')
print(f'Artists: {result[0][\"count\"]}')
"
```

**Check 3: Model evaluation**
```bash
# Run model validation
python validate_venue_popularity_implementation.py
python validate_ticket_sales_prediction.py
python validate_recommendation_engine.py
```

---

### Web Interface Issues

#### Issue: Web interface not loading

**Check 1: Development server running**
```bash
# Check if port 5173 is in use
lsof -i :5173

# Start dev server
cd web
npm run dev
```

**Check 2: Dependencies installed**
```bash
cd web

# Check node_modules
ls node_modules/ | wc -l

# Reinstall if needed
rm -rf node_modules package-lock.json
npm install
```

**Check 3: Build errors**
```bash
cd web

# Check for TypeScript errors
npm run lint

# Try building
npm run build
```

**Check 4: API connectivity**
```bash
# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/venues/popularity
```

---

### Data Pipeline Issues

#### Issue: No data in Redshift after pipeline run

**Check 1: Glue jobs status**
```bash
# Check Glue job runs
aws glue get-job-runs --job-name concert-etl-artist-normalization --max-results 5

# Check for errors
aws logs tail /aws-glue/jobs/output --follow
```

**Check 2: S3 data**
```bash
# Verify data in S3
aws s3 ls s3://concert-data-raw/ --recursive | head -20
aws s3 ls s3://concert-data-processed/ --recursive | head -20
```

**Check 3: Kinesis streams**
```bash
# Check stream status
aws kinesis describe-stream --stream-name concert-stream-artists

# Check Lambda processing
aws logs tail /aws/lambda/concert-data-processor --follow
```

**Check 4: Run validation**
```bash
# Validate complete pipeline
python validate_demo_pipeline.py
```

---

### Demo Script Issues

#### Issue: Demo test queries failing

**Check 1: Chatbot service running**
```bash
# Verify chatbot is accessible
curl http://localhost:8000/health

# Start if not running
./run_chatbot.sh &
```

**Check 2: Run with correct Python path**
```bash
# Use PYTHONPATH
PYTHONPATH=. python demo_test_queries.py

# Or use the script directly (it should handle PYTHONPATH)
python demo_test_queries.py
```

**Check 3: Check for errors**
```bash
# Run in verbose mode
python demo_test_queries.py --scenario 1
```

---

### Validation Script Issues

#### Issue: Validation scripts failing

**Check 1: All services running**
```bash
# Quick validation (no services needed)
python quick_system_validation.py

# Full validation (requires services)
./run_chatbot.sh &
sleep 5
python validate_end_to_end_system.py
```

**Check 2: AWS connectivity**
```bash
# Test AWS access
aws sts get-caller-identity

# Test specific services
aws s3 ls
aws redshift describe-clusters
aws kinesis list-streams
```

---

## Environment Setup Issues

### Issue: Virtual environment not activated

**Solution**:
```bash
# Activate virtual environment
source .venv/bin/activate

# Verify activation
which python
# Should show: /path/to/project/.venv/bin/python
```

### Issue: Missing dependencies

**Solution**:
```bash
# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "boto3|fastapi|pydantic|pandas"
```

### Issue: Environment variables not set

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Verify
echo $AWS_REGION
echo $REDSHIFT_HOST
```

---

## Quick Diagnostic Commands

### Check System Status
```bash
# Run quick validation
python quick_system_validation.py

# Check all services
./check_services.sh  # If exists
```

### Check Python Environment
```bash
# Python version
python --version

# Installed packages
pip list

# Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Check AWS Configuration
```bash
# AWS CLI version
aws --version

# Current identity
aws sts get-caller-identity

# Default region
aws configure get region
```

### Check Running Services
```bash
# Check ports
lsof -i :8000  # Chatbot API
lsof -i :5173  # Web dev server
lsof -i :8080  # ML API (if separate)

# Check processes
ps aux | grep -E "chatbot|ml_api|npm"
```

---

## Getting Help

If you're still experiencing issues:

1. **Check logs**: Look for error messages in service logs
2. **Run validation**: Use `python quick_system_validation.py`
3. **Review documentation**: Check `docs/` folder for specific guides
4. **Check AWS console**: Verify resources are running
5. **Test connectivity**: Ensure network access to AWS services

### Useful Validation Commands
```bash
# Quick system check
python quick_system_validation.py

# Validate specific components
python validate_redshift_implementation.py
python validate_chatbot_service.py
python validate_recommendation_engine.py

# Full end-to-end validation
python validate_end_to_end_system.py
```

---

## Common Command Reference

### Starting Services
```bash
# Chatbot API
./run_chatbot.sh

# ML API
./run_ml_api.sh

# Web interface
cd web && npm run dev
```

### Running Demos
```bash
# Interactive demo
python demo_test_queries.py

# Generate data
python generate_synthetic_data.py

# Run pipeline
./run_complete_demo.sh

# Train models
python train_demo_models.py
```

### Validation
```bash
# Quick check
python quick_system_validation.py

# Full validation
python validate_end_to_end_system.py

# Component validation
python validate_*.py
```

---

**Last Updated**: November 13, 2025
