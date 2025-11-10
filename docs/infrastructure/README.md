# Infrastructure Documentation

Documentation for additional infrastructure components, ML models, and advanced features.

## 📄 Documents

- **[Recommendation Engine Summary](RECOMMENDATION_ENGINE_SUMMARY.md)**
  - ML-based recommendation system
  - Collaborative and content-based filtering
  - Implementation details
  - Usage examples

## 🏗️ Infrastructure Components

### Data Lake & Governance
- **[Lake Formation README](../../src/infrastructure/LAKE_FORMATION_README.md)**
  - Data governance setup
  - Access control policies
  - Data catalog management
  - Security best practices

### ETL & Processing
- **AWS Glue Jobs**: `src/infrastructure/glue_etl_jobs.py`
- **Glue Job Manager**: `src/infrastructure/glue_job_manager.py`
- **Data Quality Service**: `src/services/data_quality_service.py`

### Streaming & Lambda
- **Kinesis Client**: `src/infrastructure/kinesis_client.py`
- **Lambda Functions**: `src/infrastructure/lambda_functions.py`
- **Lambda Deployment**: `src/infrastructure/lambda_deployment.py`

### Machine Learning
- **Recommendation Service**: `src/services/recommendation_service.py`
- **Ticket Sales Prediction**: `src/services/ticket_sales_prediction_service.py`
- **Venue Popularity**: `src/services/venue_popularity_service.py`

## 🤖 Machine Learning Features

### 1. Recommendation Engine

Provides personalized concert recommendations using:
- **Collaborative Filtering**: User-based recommendations
- **Content-Based Filtering**: Genre and artist similarity
- **Hybrid Approach**: Combined recommendations

```python
from src.services.recommendation_service import RecommendationService

recommender = RecommendationService()
recommendations = recommender.get_recommendations(user_id="user_123", limit=10)
```

### 2. Ticket Sales Prediction

Predicts ticket sales using:
- Artist popularity
- Venue capacity
- Historical data
- Seasonal trends

```python
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService

predictor = TicketSalesPredictionService()
prediction = predictor.predict_sales(concert_id="concert_456")
```

### 3. Venue Popularity Analysis

Analyzes venue performance:
- Attendance rates
- Revenue trends
- Capacity utilization
- Seasonal patterns

```python
from src.services.venue_popularity_service import VenuePopularityService

analyzer = VenuePopularityService()
metrics = analyzer.analyze_venue(venue_id="venue_789")
```

## 🔧 Setup Scripts

### Kinesis
```bash
./infrastructure/setup_kinesis_for_ingestion.sh
python infrastructure/setup_kinesis_ingestion.py
```

### Redshift
```bash
./infrastructure/redshift_setup.sh
python infrastructure/initialize_redshift_schema.py
python infrastructure/init_redshift_simple.py
```

### Validation
```bash
python validate_kinesis_implementation.py
python validate_redshift_implementation.py
python validate_governance_implementation.py
python validate_recommendation_engine.py
```

## 📊 Data Flow

```
External APIs
     ↓
API Connectors
     ↓
┌────────────┬────────────┐
│            │            │
S3           Kinesis      
(Raw Data)   (Stream)
│            │
↓            ↓
AWS Glue     Lambda       
│            │
└────┬───────┘
     ↓
  Redshift
     ↓
┌────────────┬────────────┐
│            │            │
Analytics    ML Models    
```

## 🎯 Use Cases

### 1. Real-Time Analytics
- Stream processing with Kinesis
- Lambda for event-driven actions
- Real-time dashboards

### 2. Batch Processing
- Daily ETL with AWS Glue
- Data quality checks
- Historical analysis

### 3. Machine Learning
- Recommendation engine
- Predictive analytics
- Trend analysis

### 4. Data Governance
- Lake Formation policies
- Access control
- Data lineage

## 💰 Cost Breakdown

| Component | Monthly Cost |
|-----------|-------------|
| S3 Storage (100 GB) | ~$2.30 |
| Kinesis (1 shard) | ~$11 |
| Glue (10 DPU-hours) | ~$4.40 |
| Lambda (1M requests) | Free tier |
| Redshift (dc2.large) | ~$180 |
| SageMaker (ml.t3.medium) | ~$40 |
| **Total** | **~$238/month** |

## 🔗 Related Documentation

- [API Ingestion](../api-ingestion/README.md)
- [Kinesis Setup](../kinesis/README.md)
- [Redshift Setup](../redshift/README.md)
- [Main Documentation](../README.md)

## 🆘 Troubleshooting

### Glue Job Failures
```bash
# Check job logs
aws logs tail /aws-glue/jobs/output --follow

# View job runs
aws glue get-job-runs --job-name concert-etl-job
```

### Lambda Errors
```bash
# View Lambda logs
aws logs tail /aws/lambda/concert-data-processor --follow

# Check function configuration
aws lambda get-function --function-name concert-data-processor
```

### ML Model Issues
```python
# Validate model
from src.services.recommendation_service import RecommendationService

recommender = RecommendationService()
recommender.validate_model()
```

## 📚 Additional Resources

### AWS Services
- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Amazon SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [AWS Lake Formation Documentation](https://docs.aws.amazon.com/lake-formation/)

### Code Examples
- `src/services/example_glue_etl_usage.py`
- `src/services/example_kinesis_usage.py`
- `src/services/example_recommendation_usage.py`
- `src/services/example_venue_popularity_usage.py`

## ✅ Implementation Checklist

- ✅ Kinesis stream configured
- ✅ Lambda functions deployed
- ✅ Glue jobs created
- ✅ Lake Formation policies set
- ✅ ML models trained
- ✅ Monitoring enabled
- ✅ Alerts configured

---

[← Back to Main Documentation](../README.md)