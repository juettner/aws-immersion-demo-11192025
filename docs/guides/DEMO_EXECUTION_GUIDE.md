# Concert Data Platform - Demo Execution Guide

## Overview

This guide provides step-by-step instructions for executing a complete demonstration of the Concert Data Platform. Follow these instructions to showcase all platform capabilities in a structured, impressive manner.

## Prerequisites

### Environment Setup

1. **AWS Credentials Configured**:
```bash
aws configure list
# Verify credentials are set
```

2. **Python Environment Active**:
```bash
source .venv/bin/activate
python --version  # Should be 3.9+
```

3. **Environment Variables Set**:
```bash
# Verify .env file exists and contains:
cat .env | grep -E "AWS_|SPOTIFY_|TICKETMASTER_|BEDROCK_"
```

4. **Dependencies Installed**:
```bash
pip install -r requirements.txt
cd web && npm install && cd ..
```

### Infrastructure Verification

```bash
# Verify Redshift is accessible
python validate_redshift_implementation.py

# Verify API Gateway is configured
python validate_api_gateway_setup.py

# Verify Lambda functions are deployed
python validate_api_lambda_handlers.py

# Verify web deployment
python validate_web_deployment.py
```

---

## Demo Execution Steps

### Phase 1: Data Generation and Ingestion (10 minutes)

#### Step 1.1: Generate Synthetic Concert Data

```bash
# Generate comprehensive demo dataset
python generate_synthetic_data.py \
    --num-artists 1000 \
    --num-venues 500 \
    --num-concerts 10000 \
    --num-sales 50000 \
    --output-dir ./demo_data \
    --upload-to-s3
```

**Expected Output**:
- 1,000 artists with diverse genres and popularity scores
- 500 venues across multiple locations and capacities
- 10,000 concerts spanning past and future dates
- 50,000 ticket sales with realistic patterns
- Data uploaded to S3 raw data bucket

**Demo Talking Points**:
- Synthetic data mimics real-world concert industry patterns
- Configurable generation for different demo scenarios
- Automatic S3 upload for pipeline ingestion
- Referential integrity maintained across entities

#### Step 1.2: Run Complete Data Pipeline

```bash
# Execute end-to-end pipeline
./run_complete_demo.sh
```

**What This Does**:
1. Triggers Glue ETL jobs for data normalization
2. Performs fuzzy matching deduplication
3. Loads processed data into Redshift
4. Runs data quality checks
5. Generates initial analytics

**Expected Duration**: 5-7 minutes

**Monitor Progress**:
```bash
# Watch Glue job status
aws glue get-job-runs --job-name concert-etl-artist-normalization --max-results 1

# Check Redshift load status
python src/services/example_redshift_usage.py
```

**Demo Talking Points**:
- Automated ETL orchestration with AWS Glue
- Intelligent deduplication using fuzzy matching
- Data quality monitoring and alerting
- Efficient Redshift loading with COPY commands

#### Step 1.3: Verify Data Load

```bash
# Validate pipeline execution
python validate_demo_pipeline.py
```

**Expected Output**:
```
✓ Artists table: 1,000 records
✓ Venues table: 500 records
✓ Concerts table: 10,000 records
✓ Ticket sales table: 50,000 records
✓ Data quality: 99.8% pass rate
✓ Referential integrity: 100% valid
```

**Demo Talking Points**:
- Comprehensive data validation
- Quality metrics tracking
- Referential integrity enforcement
- Ready for ML training and analytics

---

### Phase 2: ML Model Training and Predictions (10 minutes)

#### Step 2.1: Train ML Models

```bash
# Train all ML models with demo data
python train_demo_models.py
```

**What This Does**:
1. Extracts training data from Redshift
2. Trains venue popularity ranking model
3. Trains ticket sales prediction model
4. Trains recommendation engine (collaborative + content-based)
5. Evaluates model performance
6. Saves models for inference

**Expected Duration**: 3-5 minutes

**Expected Output**:
```
Training Venue Popularity Model...
✓ Model trained with MAE: 2.3, RMSE: 3.1

Training Ticket Sales Prediction Model...
✓ Model trained with MAE: 245, RMSE: 387

Training Recommendation Engine...
✓ Collaborative filtering ready
✓ Content-based filtering ready

All models saved and ready for inference.
```

**Demo Talking Points**:
- Automated feature engineering from raw data
- Multiple ML algorithms for different use cases
- Model evaluation with standard metrics
- Ready for real-time predictions

#### Step 2.2: Test Venue Popularity Predictions

```bash
# Run venue popularity predictions
python src/services/example_venue_popularity_usage.py
```

**Expected Output**:
```
Top 10 Venues by Predicted Popularity:

1. Madison Square Garden (New York, NY)
   - Popularity Score: 95.8
   - Avg Attendance Rate: 98%
   - Revenue per Event: $2.5M
   - Booking Frequency: 45 events/year

2. The Forum (Los Angeles, CA)
   - Popularity Score: 92.3
   - Avg Attendance Rate: 95%
   - Revenue per Event: $1.8M
   - Booking Frequency: 38 events/year

[... more venues ...]
```

**Demo Talking Points**:
- ML-powered venue ranking
- Multiple factors considered (attendance, revenue, frequency)
- Actionable insights for booking decisions
- Confidence scores for predictions

#### Step 2.3: Test Ticket Sales Predictions

```bash
# Run ticket sales predictions
python src/services/example_ticket_sales_prediction_usage.py
```

**Expected Output**:
```
Ticket Sales Predictions for Upcoming Concerts:

Concert: Arctic Monkeys @ Brooklyn Steel (2025-11-20)
- Predicted Sales: 8,500 tickets
- Confidence: 85%
- Recommended Price: $75-$125
- Risk Level: Low
- Expected Revenue: $850,000

Concert: The Strokes @ Terminal 5 (2025-11-25)
- Predicted Sales: 6,200 tickets
- Confidence: 78%
- Recommended Price: $60-$100
- Risk Level: Medium
- Expected Revenue: $496,000

[... more predictions ...]
```

**Demo Talking Points**:
- Predictive analytics for revenue forecasting
- Confidence scoring for risk assessment
- Price optimization recommendations
- Historical pattern analysis

#### Step 2.4: Test Recommendation Engine

```bash
# Run recommendation engine
python src/services/example_recommendation_usage.py
```

**Expected Output**:
```
Personalized Concert Recommendations:

Based on preferences: Rock, Alternative | Location: New York

1. Arctic Monkeys @ Brooklyn Steel (2025-11-20)
   - Recommendation Score: 92%
   - Reason: Matches genre preferences, high artist similarity
   - Price: $75-$125

2. The National @ Radio City Music Hall (2025-11-22)
   - Recommendation Score: 88%
   - Reason: Similar to your favorite artists
   - Price: $80-$150

[... more recommendations ...]

Similar Artists to Arctic Monkeys:
1. The Strokes (Similarity: 0.89)
2. Franz Ferdinand (Similarity: 0.85)
3. Interpol (Similarity: 0.82)
```

**Demo Talking Points**:
- Collaborative and content-based filtering
- Personalized recommendations
- Artist similarity scoring
- Location-aware suggestions

---

### Phase 3: AI Chatbot Demonstration (15 minutes)

#### Step 3.1: Start Chatbot Service

```bash
# Start chatbot API in background (using helper script)
./run_chatbot.sh &
CHATBOT_PID=$!

# OR set PYTHONPATH manually:
# PYTHONPATH=. python src/api/chatbot_api.py &

# Verify service is running
sleep 3
curl http://localhost:8000/health
```

**Expected Output**:
```json
{
  "status": "healthy",
  "service": "concert-chatbot",
  "version": "1.0.0",
  "timestamp": "2025-11-13T10:30:00Z"
}
```

#### Step 3.2: Execute Chatbot Scenarios

**Scenario A: Artist Lookup**

```bash
# Test artist lookup
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about The Rolling Stones",
    "session_id": "demo_session_1"
  }'
```

**Expected Response**:
```json
{
  "response": "The Rolling Stones are a legendary rock band with a popularity score of 94.5. They've performed at 45 venues in our database, with an average attendance of 18,500 per concert. Their most popular venues include Madison Square Garden and The Forum. Would you like to know more about their upcoming concerts or venue preferences?",
  "data": {
    "artist_id": "artist_789",
    "name": "The Rolling Stones",
    "genre": ["rock", "classic rock"],
    "popularity_score": 94.5,
    "total_concerts": 45,
    "avg_attendance": 18500
  },
  "session_id": "demo_session_1"
}
```

**Demo Talking Points**:
- Natural language understanding
- Entity extraction (artist name)
- Data retrieval from Redshift
- Conversational response generation

**Scenario B: Venue Recommendations**

```bash
# Test venue recommendations
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the best venues in New York for rock concerts?",
    "session_id": "demo_session_1"
  }'
```

**Expected Response**:
```json
{
  "response": "Based on our analysis, the top rock venues in New York are:\n\n1. Madison Square Garden - Capacity: 20,000, Popularity: 95.8\n2. Brooklyn Steel - Capacity: 1,800, Popularity: 88.3\n3. Terminal 5 - Capacity: 3,000, Popularity: 85.7\n\nThese venues have the highest attendance rates and revenue for rock concerts. Would you like details about any specific venue?",
  "data": {
    "venues": [
      {"name": "Madison Square Garden", "capacity": 20000, "popularity": 95.8},
      {"name": "Brooklyn Steel", "capacity": 1800, "popularity": 88.3},
      {"name": "Terminal 5", "capacity": 3000, "popularity": 85.7}
    ]
  },
  "session_id": "demo_session_1"
}
```

**Demo Talking Points**:
- Location-based filtering
- ML-powered venue ranking
- Context retention from previous conversation
- Actionable recommendations

**Scenario C: Data Visualization**

```bash
# Test visualization generation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me the trend of concert attendance over the past year",
    "session_id": "demo_session_1"
  }'
```

**Expected Response**:
```json
{
  "response": "I've analyzed concert attendance trends over the past year. The data shows a 15% increase in average attendance, with peak months in June-August (summer festival season) and December (holiday concerts). Here's a visualization of the trend.",
  "visualization": {
    "type": "line_chart",
    "image_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...",
    "data": {
      "months": ["2024-11", "2024-12", "2025-01", ...],
      "attendance": [12500, 15800, 11200, ...]
    }
  },
  "session_id": "demo_session_1"
}
```

**Demo Talking Points**:
- AgentCore Code Interpreter integration
- Dynamic data analysis
- Chart generation
- Multi-modal responses (text + image)

#### Step 3.3: Test Conversation Memory

```bash
# Test memory persistence
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What was the first artist I asked about?",
    "session_id": "demo_session_1"
  }'
```

**Expected Response**:
```json
{
  "response": "You first asked about The Rolling Stones. We discussed their popularity score of 94.5 and their performance history at 45 venues.",
  "session_id": "demo_session_1"
}
```

**Demo Talking Points**:
- AgentCore Memory integration
- Conversation context retention
- DynamoDB-backed persistence
- Cross-session memory

---

### Phase 4: Web Interface Demonstration (10 minutes)

#### Step 4.1: Start Web Application

```bash
# Start web development server
cd web
npm run dev &
WEB_PID=$!
cd ..

# Wait for server to start
sleep 5
```

**Access**: Open browser to `http://localhost:5173`

#### Step 4.2: Demonstrate Analytics Dashboard

**Navigation**: Click "Dashboard" in navigation menu

**Demo Flow**:

1. **Venue Popularity View**:
   - Show top 10 venues bar chart
   - Highlight interactive tooltips
   - Filter by location (select "New York")
   - Show updated rankings

2. **Ticket Sales Predictions View**:
   - Display upcoming concert predictions
   - Show confidence scores
   - Filter by confidence level (>80%)
   - Highlight high-risk events

3. **Artist Trends View**:
   - Show artist popularity rankings
   - Filter by genre (select "Rock")
   - Display trend line for selected artist
   - Compare multiple artists

**Demo Talking Points**:
- Real-time data from API Gateway
- Interactive filtering and drill-down
- Responsive design for all devices
- Integration with ML predictions

#### Step 4.3: Demonstrate Chatbot Interface

**Navigation**: Click "Chatbot" in navigation menu

**Demo Flow**:

1. **Initial Query**:
   - Type: "What concerts are happening this weekend?"
   - Show natural language processing
   - Display formatted response with data

2. **Follow-up Query**:
   - Type: "Which one would you recommend for a rock fan?"
   - Show context retention
   - Display personalized recommendations

3. **Visualization Request**:
   - Type: "Show me a chart of venue capacities"
   - Show chart generation
   - Display embedded visualization

4. **Conversation History**:
   - Scroll up to show previous messages
   - Highlight conversation flow
   - Show message timestamps

**Demo Talking Points**:
- Intuitive chat interface
- Real-time responses
- Multi-modal content (text, tables, charts)
- Conversation history persistence

---

### Phase 5: Infrastructure and Monitoring (5 minutes)

#### Step 5.1: Show CloudWatch Dashboards

```bash
# Open CloudWatch dashboard
aws cloudwatch get-dashboard --dashboard-name concert-platform-overview
```

**Demo Points**:
- Lambda function metrics (invocations, errors, duration)
- API Gateway metrics (requests, latency, 4xx/5xx errors)
- Redshift metrics (query performance, connections)
- Kinesis metrics (incoming records, processing lag)

#### Step 5.2: Show X-Ray Tracing

```bash
# Get recent traces
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s)
```

**Demo Points**:
- End-to-end request tracing
- Service map visualization
- Performance bottleneck identification
- Error tracking and debugging

#### Step 5.3: Show CloudFormation Stacks

```bash
# List deployed stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
```

**Demo Points**:
- Infrastructure as Code
- Modular stack design
- Automated deployment
- Version control and rollback

---

## Demo Cleanup

### Stop Running Services

```bash
# Stop chatbot service
kill $CHATBOT_PID

# Stop web server
kill $WEB_PID

# Deactivate virtual environment
deactivate
```

### Optional: Clear Demo Data

```bash
# Clear Redshift tables (if needed for fresh demo)
python src/infrastructure/redshift_client.py --clear-tables

# Clear S3 demo data
aws s3 rm s3://concert-data-raw/demo/ --recursive
aws s3 rm s3://concert-data-processed/demo/ --recursive

# Clear DynamoDB conversation history
aws dynamodb delete-table --table-name concert-chatbot-conversations
```

---

## Troubleshooting

### Issue: Chatbot service won't start

**Solution**:
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 $(lsof -t -i :8000)

# Start with proper PYTHONPATH
./run_chatbot.sh

# OR manually:
PYTHONPATH=. python src/api/chatbot_api.py

# Check Bedrock credentials
aws bedrock list-foundation-models --region us-east-1
```

### Issue: Web interface not loading

**Solution**:
```bash
# Check if port 5173 is in use
lsof -i :5173

# Rebuild web application
cd web
rm -rf node_modules dist
npm install
npm run build
npm run dev
```

### Issue: No data in Redshift

**Solution**:
```bash
# Verify Redshift connectivity
python validate_redshift_implementation.py

# Re-run data pipeline
./run_complete_demo.sh

# Check Glue job logs
aws logs tail /aws-glue/jobs/output --follow
```

### Issue: ML predictions failing

**Solution**:
```bash
# Verify models are trained
ls -la models/

# Retrain models
python train_demo_models.py

# Check model evaluation
python validate_model_evaluation_implementation.py
```

---

## Demo Best Practices

### Preparation

1. **Run full demo at least once before presenting**
2. **Have backup screenshots/videos for critical features**
3. **Test all API endpoints beforehand**
4. **Prepare answers to common questions**
5. **Have AWS console open in separate tab**

### During Demo

1. **Start with business context, not technical details**
2. **Show, don't just tell - execute live commands**
3. **Highlight AWS service integration throughout**
4. **Pause for questions after each phase**
5. **Have backup plan if live demo fails**

### After Demo

1. **Provide access to demo environment**
2. **Share documentation and code repository**
3. **Schedule technical deep-dive sessions**
4. **Collect feedback for improvements**
5. **Follow up with specific use case discussions**

---

## Demo Timing Guide

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| Setup & Verification | 5 min | Check prerequisites, verify infrastructure |
| Data Generation | 10 min | Generate data, run pipeline, verify load |
| ML Training | 10 min | Train models, test predictions |
| Chatbot Demo | 15 min | Multiple conversation scenarios |
| Web Interface | 10 min | Dashboard and chat UI |
| Infrastructure | 5 min | Monitoring, tracing, IaC |
| Q&A | 10 min | Answer questions, discuss next steps |
| **Total** | **65 min** | Full comprehensive demo |

### Quick Demo (30 minutes)

- Skip data generation (use pre-loaded data)
- Show 2-3 chatbot scenarios only
- Brief dashboard walkthrough
- Focus on business value over technical details

### Technical Deep Dive (90 minutes)

- Include all phases above
- Add code walkthrough
- Show CloudFormation templates
- Demonstrate deployment process
- Discuss architecture decisions
- Live troubleshooting examples

---

## Success Metrics

### Demo Effectiveness

- [ ] All features demonstrated successfully
- [ ] No critical errors during demo
- [ ] Audience engagement and questions
- [ ] Clear understanding of platform capabilities
- [ ] Interest in next steps/follow-up

### Technical Validation

- [ ] All services running smoothly
- [ ] Response times under 2 seconds
- [ ] ML predictions with >70% confidence
- [ ] Data quality >95%
- [ ] Zero data loss in pipeline

---

## Additional Resources

- **Full Documentation**: `docs/DOCUMENTATION_INDEX.md`
- **API Reference**: `docs/api/README.md`
- **Architecture Guide**: `.kiro/specs/data-readiness-ai-demo/design.md`
- **Deployment Guide**: `DEPLOYMENT.md`
- **Quick Start**: `QUICKSTART.md`

---

## Contact and Support

For questions or issues during demo preparation:

1. Review troubleshooting section above
2. Check validation scripts: `validate_*.py`
3. Review CloudWatch logs for errors
4. Consult documentation in `docs/` folder
