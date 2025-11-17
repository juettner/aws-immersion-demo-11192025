#!/bin/bash

# Incremental Production Deployment
# Use this when you already have some resources deployed

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REGION="us-east-1"
ACCOUNT_ID="853297241922"

echo -e "${BLUE}=========================================="
echo "Incremental Deployment - Concert Platform"
echo "==========================================${NC}"

# Step 1: Generate fresh demo data
echo -e "\n${BLUE}Step 1: Generating Demo Data${NC}"
python generate_synthetic_data.py \
    --num-artists 1000 \
    --num-venues 500 \
    --num-concerts 10000 \
    --num-ticket-sales 50000 \
    --output-dir data/synthetic

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Demo data generated${NC}"
else
    echo -e "${RED}✗ Failed to generate demo data${NC}"
    exit 1
fi

# Step 2: Upload to S3
echo -e "\n${BLUE}Step 2: Uploading Data to S3${NC}"
aws s3 sync data/synthetic/ s3://concert-data-raw/synthetic/ --region $REGION
echo -e "${GREEN}✓ Data uploaded to S3${NC}"

# Step 3: Initialize/Update Redshift Schema
echo -e "\n${BLUE}Step 3: Initializing Redshift Schema${NC}"
python infrastructure/initialize_redshift_schema.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Redshift schema ready${NC}"
else
    echo -e "${YELLOW}⚠ Redshift initialization had issues (may already exist)${NC}"
fi

# Step 4: Load data into Redshift
echo -e "\n${BLUE}Step 4: Loading Data into Redshift${NC}"
python -c "
from src.services.redshift_service import RedshiftService
from src.config.settings import Settings

settings = Settings.from_env()
service = RedshiftService(settings)

print('Loading data from S3 to Redshift...')
result = service.load_data_from_s3('s3://concert-data-raw/synthetic/')
print(f'Load result: {result}')
"
echo -e "${GREEN}✓ Data loaded into Redshift${NC}"

# Step 5: Train ML Models
echo -e "\n${BLUE}Step 5: Training ML Models${NC}"
python train_demo_models.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ML models trained${NC}"
else
    echo -e "${YELLOW}⚠ ML model training had issues${NC}"
fi

# Step 6: Test Chatbot Service
echo -e "\n${BLUE}Step 6: Testing Chatbot Service${NC}"
echo "Starting chatbot service in background..."
python src/api/chatbot_api.py &
CHATBOT_PID=$!
sleep 5

# Test if chatbot is responding
curl -s http://localhost:8000/health > /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Chatbot service is running (PID: $CHATBOT_PID)${NC}"
else
    echo -e "${YELLOW}⚠ Chatbot service may not be responding${NC}"
fi

# Step 7: Run Quick Tests
echo -e "\n${BLUE}Step 7: Running Quick Tests${NC}"
python demo_test_queries.py --scenario 1 --non-interactive || echo -e "${YELLOW}⚠ Demo test had issues${NC}"

# Summary
echo -e "\n${GREEN}=========================================="
echo "Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "Services running:"
echo "  - Chatbot API: http://localhost:8000 (PID: $CHATBOT_PID)"
echo ""
echo "To stop chatbot: kill $CHATBOT_PID"
echo ""
echo "Next steps:"
echo "  1. Test chatbot: python demo_test_queries.py"
echo "  2. Run full validation: python validate_end_to_end_system.py"
echo "  3. Deploy web app: cd web && npm run build"
echo ""
