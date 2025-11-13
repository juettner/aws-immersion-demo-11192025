# Demo Scenarios Guide

## Overview

This document provides comprehensive demo scenarios for showcasing the Concert Data Platform's capabilities. Each scenario demonstrates specific features and can be executed independently or as part of a complete demo flow.

## Table of Contents

1. [Chatbot Conversation Scenarios](#chatbot-conversation-scenarios)
2. [Analytics Dashboard Scenarios](#analytics-dashboard-scenarios)
3. [ML Model Prediction Scenarios](#ml-model-prediction-scenarios)
4. [Data Pipeline Scenarios](#data-pipeline-scenarios)
5. [Complete Demo Flow](#complete-demo-flow)

---

## Chatbot Conversation Scenarios

### Scenario 1: Artist Lookup and Information

**Objective**: Demonstrate natural language understanding and data retrieval

**Conversation Script**:

```
User: "Tell me about The Rolling Stones"

Expected Response:
- Artist name, genre, popularity score
- Recent concert history
- Venue preferences
- Average ticket sales

User: "What venues have they performed at?"

Expected Response:
- List of venues with dates
- Venue capacities and locations
- Attendance statistics

User: "How popular are they compared to other rock artists?"

Expected Response:
- Popularity ranking
- Comparison with similar artists
- Trend analysis
```

**Key Features Demonstrated**:
- Natural language query processing
- Entity extraction (artist name)
- Multi-turn conversation with context
- Data aggregation from Redshift

---

### Scenario 2: Venue Search and Recommendations

**Objective**: Show recommendation engine and venue analytics

**Conversation Script**:

```
User: "What are the best venues in New York for rock concerts?"

Expected Response:
- Top-ranked venues by popularity
- Capacity and location details
- Recent concert performance metrics
- Booking frequency

User: "Which venue would be best for a mid-sized indie band?"

Expected Response:
- Venue recommendations based on capacity (500-2000)
- Historical performance data for similar artists
- Expected ticket sales predictions
- Pricing recommendations

User: "Show me upcoming concerts at Madison Square Garden"

Expected Response:
- Scheduled concerts with dates
- Artist information
- Ticket availability and pricing
- Historical attendance data
```

**Key Features Demonstrated**:
- Location-based filtering
- Recommendation algorithm
- Predictive analytics integration
- Context-aware responses

---

### Scenario 3: Concert Recommendations

**Objective**: Demonstrate personalized recommendations and ML integration

**Conversation Script**:

```
User: "I like rock and alternative music. What concerts should I attend?"

Expected Response:
- Personalized concert recommendations
- Artist similarity scoring
- Venue suitability analysis
- Date and pricing information

User: "What about something in the next month?"

Expected Response:
- Filtered recommendations by date range
- Urgency indicators (selling fast, etc.)
- Price comparisons
- Similar artist suggestions

User: "Which of these concerts are likely to sell out?"

Expected Response:
- Ticket sales predictions
- Confidence scores
- Historical sell-out patterns
- Booking recommendations
```

**Key Features Demonstrated**:
- Collaborative filtering
- Content-based recommendations
- ML model integration
- Conversation memory (preferences)

---

### Scenario 4: Data Analysis and Visualization

**Objective**: Show code interpreter and visualization capabilities

**Conversation Script**:

```
User: "Show me the trend of concert attendance over the past year"

Expected Response:
- Line chart showing attendance trends
- Statistical summary (avg, min, max)
- Seasonal patterns identified
- Growth/decline analysis

User: "Which genres are most popular?"

Expected Response:
- Bar chart of genre popularity
- Percentage breakdown
- Revenue by genre
- Emerging trends

User: "Compare ticket sales between venues in California"

Expected Response:
- Comparative bar chart
- Statistical analysis
- Venue rankings
- Revenue insights
```

**Key Features Demonstrated**:
- Dynamic data analysis
- Chart generation
- AgentCore Code Interpreter
- Multi-modal responses (text + images)

---

### Scenario 5: External Data Enrichment

**Objective**: Demonstrate real-time API integration

**Conversation Script**:

```
User: "Get me the latest information about Coldplay from Spotify"

Expected Response:
- Real-time Spotify data
- Current popularity metrics
- Recent releases
- Tour information

User: "Are there any upcoming Coldplay concerts on Ticketmaster?"

Expected Response:
- Live Ticketmaster event data
- Ticket availability
- Pricing information
- Venue details

User: "How does their current popularity compare to our historical data?"

Expected Response:
- Comparison analysis
- Trend visualization
- Prediction updates
- Insights on changes
```

**Key Features Demonstrated**:
- AgentCore Browser tool
- External API integration
- Data enrichment
- Real-time vs. historical comparison

---

## Analytics Dashboard Scenarios

### Scenario 6: Venue Popularity Dashboard

**Objective**: Showcase venue analytics and rankings

**Dashboard View**:
- **Top 10 Venues Chart**: Bar chart showing popularity scores
- **Geographic Distribution**: Map or list by location
- **Capacity Utilization**: Gauge charts showing fill rates
- **Revenue Metrics**: Total revenue per venue

**Interaction Flow**:
1. Load dashboard with default date range (last 6 months)
2. Filter by location (e.g., "California")
3. Sort by different metrics (popularity, revenue, capacity)
4. Click on venue for detailed drill-down

**Key Insights to Highlight**:
- Highest-performing venues
- Underutilized venues with potential
- Geographic trends
- Capacity vs. popularity correlation

---

### Scenario 7: Ticket Sales Predictions Dashboard

**Objective**: Display ML model predictions and confidence

**Dashboard View**:
- **Prediction Accuracy Chart**: Historical predictions vs. actuals
- **Upcoming Concerts**: Predicted sales with confidence scores
- **High-Risk Events**: Low-confidence predictions flagged
- **Revenue Forecast**: Projected revenue by month

**Interaction Flow**:
1. View upcoming concert predictions
2. Filter by confidence level (>70%, >80%, >90%)
3. Compare predictions across different artist-venue combinations
4. Drill into specific prediction details

**Key Insights to Highlight**:
- Model accuracy metrics (MAE, RMSE)
- High-confidence predictions for planning
- Risk identification for low-confidence events
- Revenue forecasting capabilities

---

### Scenario 8: Artist Popularity Trends

**Objective**: Show artist analytics and trend analysis

**Dashboard View**:
- **Top Artists Chart**: Ranked by popularity score
- **Genre Distribution**: Pie chart of artist genres
- **Growth Trends**: Line chart showing popularity over time
- **Concert Frequency**: Bar chart of performances per artist

**Interaction Flow**:
1. View top 20 artists by popularity
2. Filter by genre (rock, pop, alternative, etc.)
3. Select artist to see detailed trend
4. Compare multiple artists side-by-side

**Key Insights to Highlight**:
- Rising stars (fastest growth)
- Established performers (consistent popularity)
- Genre trends
- Booking opportunities

---

## ML Model Prediction Scenarios

### Scenario 9: Venue Popularity Prediction

**Test Queries**:

```python
# Query 1: Predict popularity for a specific venue
venue_id = "venue_001"
prediction = venue_popularity_service.predict_popularity(venue_id)

Expected Output:
{
    "venue_id": "venue_001",
    "venue_name": "Madison Square Garden",
    "predicted_rank": 1,
    "popularity_score": 95.8,
    "confidence": 0.92,
    "factors": {
        "avg_attendance_rate": 0.98,
        "revenue_per_event": 2500000,
        "booking_frequency": 45
    }
}

# Query 2: Compare multiple venues
venues = ["venue_001", "venue_002", "venue_003"]
comparison = venue_popularity_service.compare_venues(venues)

Expected Output: Ranked list with scores and insights
```

---

### Scenario 10: Ticket Sales Prediction

**Test Queries**:

```python
# Query 1: Predict sales for artist-venue combination
prediction = ticket_sales_service.predict_sales(
    artist_id="artist_123",
    venue_id="venue_456",
    event_date="2025-12-15"
)

Expected Output:
{
    "predicted_sales": 8500,
    "confidence_score": 0.85,
    "price_recommendation": "$75-$125",
    "risk_level": "low",
    "factors": {
        "artist_popularity": 78,
        "venue_capacity": 10000,
        "historical_avg": 8200
    }
}

# Query 2: Batch predictions for multiple events
events = [
    {"artist_id": "artist_123", "venue_id": "venue_456", "date": "2025-12-15"},
    {"artist_id": "artist_789", "venue_id": "venue_456", "date": "2025-12-20"}
]
predictions = ticket_sales_service.batch_predict(events)

Expected Output: List of predictions with confidence scores
```

---

### Scenario 11: Concert Recommendations

**Test Queries**:

```python
# Query 1: Get personalized recommendations
recommendations = recommendation_service.get_recommendations(
    user_preferences={"genres": ["rock", "alternative"], "location": "New York"},
    limit=10
)

Expected Output:
[
    {
        "concert_id": "concert_001",
        "artist": "Arctic Monkeys",
        "venue": "Brooklyn Steel",
        "date": "2025-11-20",
        "recommendation_score": 0.92,
        "reason": "Matches your genre preferences and location"
    },
    ...
]

# Query 2: Similar artist recommendations
similar_artists = recommendation_service.find_similar_artists(
    artist_id="artist_123",
    limit=5
)

Expected Output: List of similar artists with similarity scores
```

---

## Data Pipeline Scenarios

### Scenario 12: Real-Time Data Ingestion

**Objective**: Demonstrate Kinesis streaming and Lambda processing

**Demo Flow**:

1. **Generate streaming data**:
```bash
python src/services/stream_producer.py --source spotify --count 100
```

2. **Monitor Kinesis stream**:
```bash
aws kinesis describe-stream --stream-name concert-stream-events
```

3. **View Lambda processing logs**:
```bash
aws logs tail /aws/lambda/concert-data-processor --follow
```

4. **Verify data in S3**:
```bash
aws s3 ls s3://concert-data-raw/streaming/
```

**Key Features Demonstrated**:
- Real-time data ingestion
- Stream processing with Lambda
- Automatic S3 landing
- Error handling and retries

---

### Scenario 13: ETL Pipeline Execution

**Objective**: Show Glue ETL jobs and data transformation

**Demo Flow**:

1. **Trigger ETL job**:
```bash
python src/infrastructure/glue_job_manager.py --job artist-normalization --run
```

2. **Monitor job execution**:
```bash
python src/infrastructure/glue_job_manager.py --job artist-normalization --status
```

3. **View processed data**:
```bash
aws s3 ls s3://concert-data-processed/artists/
```

4. **Query Redshift**:
```sql
SELECT COUNT(*), MIN(created_at), MAX(created_at)
FROM concerts.artists
WHERE updated_at > CURRENT_DATE - 1;
```

**Key Features Demonstrated**:
- Automated ETL orchestration
- Data normalization and deduplication
- Quality monitoring
- Redshift loading

---

## Complete Demo Flow

### 30-Minute Executive Demo

**Objective**: Comprehensive showcase of all platform capabilities

#### Part 1: Data Ingestion (5 minutes)

1. Show synthetic data generation
2. Demonstrate API data ingestion (Spotify/Ticketmaster)
3. Display Kinesis streaming dashboard
4. Show S3 data lake structure

#### Part 2: Data Processing (5 minutes)

1. Trigger Glue ETL job
2. Show data normalization and deduplication
3. Display data quality metrics
4. Query Redshift data warehouse

#### Part 3: ML Models (7 minutes)

1. Run venue popularity predictions
2. Execute ticket sales predictions
3. Generate concert recommendations
4. Show model evaluation metrics

#### Part 4: AI Chatbot (8 minutes)

1. Artist lookup conversation (Scenario 1)
2. Venue recommendations (Scenario 2)
3. Data visualization request (Scenario 4)
4. External data enrichment (Scenario 5)

#### Part 5: Analytics Dashboard (5 minutes)

1. Venue popularity dashboard
2. Ticket sales predictions
3. Artist trends
4. Interactive filtering and drill-down

---

## Demo Preparation Checklist

### Before the Demo

- [ ] Generate synthetic data (10,000+ records)
- [ ] Run ETL pipeline to populate Redshift
- [ ] Train ML models with latest data
- [ ] Verify chatbot service is running
- [ ] Test web interface connectivity
- [ ] Prepare backup data/screenshots
- [ ] Test all API endpoints
- [ ] Clear conversation history for fresh demo

### During the Demo

- [ ] Start with data ingestion overview
- [ ] Show real-time processing capabilities
- [ ] Demonstrate ML predictions with explanations
- [ ] Highlight chatbot natural language understanding
- [ ] Show dashboard interactivity
- [ ] Emphasize AWS service integration
- [ ] Address questions with live queries

### After the Demo

- [ ] Provide access to demo environment
- [ ] Share documentation links
- [ ] Collect feedback
- [ ] Schedule follow-up discussions

---

## Troubleshooting Common Demo Issues

### Issue: Chatbot not responding

**Solution**:
```bash
# Check chatbot service status
curl http://localhost:8000/health

# Restart service if needed
python src/api/chatbot_api.py
```

### Issue: Dashboard not loading data

**Solution**:
```bash
# Verify API Gateway endpoints
python validate_api_gateway_setup.py

# Check Lambda function logs
aws logs tail /aws/lambda/venue-popularity-handler --follow
```

### Issue: ML predictions returning errors

**Solution**:
```bash
# Verify model endpoints
python validate_recommendation_engine.py

# Check Redshift connectivity
python validate_redshift_implementation.py
```

### Issue: No data in Redshift

**Solution**:
```bash
# Run complete demo pipeline
./run_complete_demo.sh

# Verify data load
python validate_demo_pipeline.py
```

---

## Demo Talking Points

### Key Messages

1. **Comprehensive Data Platform**: End-to-end solution from ingestion to insights
2. **AWS Native**: Leverages best-in-class AWS services (Redshift, SageMaker, Bedrock)
3. **AI-Powered**: Intelligent recommendations and predictions using ML
4. **Real-Time Capable**: Streaming data processing with Kinesis
5. **User-Friendly**: Natural language interface via AgentCore chatbot
6. **Scalable**: Serverless architecture for automatic scaling
7. **Governed**: Built-in data quality and access control

### Technical Highlights

- **Lakehouse Architecture**: Unified data lake and warehouse
- **Event-Driven**: Lambda-based processing for real-time data
- **ML Integration**: SageMaker for training and inference
- **AgentCore Services**: Memory, Code Interpreter, Browser tools
- **Modern Frontend**: React with TypeScript and real-time updates
- **Infrastructure as Code**: CloudFormation templates for reproducibility

---

## Next Steps After Demo

1. **Deep Dive Sessions**: Schedule technical deep dives on specific components
2. **Customization Discussion**: Adapt platform for specific use cases
3. **Integration Planning**: Connect to existing data sources
4. **Deployment Strategy**: Plan production deployment
5. **Training**: Provide team training on platform usage
6. **Support**: Establish ongoing support and maintenance plan
