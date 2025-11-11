# Infrastructure Documentation

Documentation for additional infrastructure components, ML models, and advanced features.

## 📄 Documents

### Infrastructure as Code
- **[CloudFormation Deployment Guide](CLOUDFORMATION_DEPLOYMENT_GUIDE.md)** ⭐
  - Complete infrastructure deployment
  - 6 modular CloudFormation templates
  - 88+ AWS resources
  - Automated deployment script
  - Validation and troubleshooting

- **[Infrastructure as Code Summary](INFRASTRUCTURE_AS_CODE_SUMMARY.md)**
  - Architecture overview
  - Design decisions
  - Resource naming conventions
  - Security and cost optimization

- **[Task 7 Implementation Summary](TASK_7_IMPLEMENTATION_SUMMARY.md)**
  - Implementation details
  - Completion status
  - Validation results

### API & Compute
- **[API Gateway Setup Guide](API_GATEWAY_SETUP_GUIDE.md)**
  - REST API configuration
  - CORS and throttling
  - Lambda integrations
  - Deployment instructions

- **[API Gateway Summary](API_GATEWAY_SUMMARY.md)**
  - Implementation overview
  - Endpoint documentation

- **[Lambda Handlers Guide](LAMBDA_HANDLERS_GUIDE.md)**
  - Serverless API handlers
  - Deployment automation
  - Testing and validation

- **[Lambda Implementation Summary](LAMBDA_IMPLEMENTATION_SUMMARY.md)**
  - Handler implementations
  - Integration details

### Web & ML
- **[Web Deployment Guide](WEB_DEPLOYMENT_GUIDE.md)**
  - S3 static hosting setup
  - CloudFront CDN configuration
  - Automated deployment scripts
  - Cache invalidation strategies

- **[Web Deployment Summary](WEB_DEPLOYMENT_SUMMARY.md)**
  - Deployment implementation details

- **[Recommendation Engine Summary](RECOMMENDATION_ENGINE_SUMMARY.md)**
  - ML-based recommendation system
  - Collaborative and content-based filtering
  - Implementation details
  - Usage examples

## 🏗️ Infrastructure Components

### Infrastructure as Code (CloudFormation)
- **Networking**: VPC, subnets, NAT gateway, security groups
- **Storage & Processing**: S3, Redshift Serverless, Glue, Kinesis
- **Compute & Application**: Lambda, API Gateway, DynamoDB
- **Chatbot Infrastructure**: DynamoDB tables, EventBridge, maintenance
- **Monitoring & Observability**: CloudWatch dashboards, alarms, SNS
- **Tracing & Logging**: CloudWatch Logs, X-Ray, log filters

See [CloudFormation Deployment Guide](CLOUDFORMATION_DEPLOYMENT_GUIDE.md) for details.

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
- **API Gateway Client**: `infrastructure/api_gateway_client.py`

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

### Complete Infrastructure Deployment (CloudFormation)
```bash
# Validate all CloudFormation templates
python validate_cloudformation_templates.py

# Deploy all infrastructure stacks
cd infrastructure
./deploy_cloudformation_stacks.sh development us-east-1
```

This deploys:
- Networking (VPC, subnets, security groups)
- Storage & Processing (S3, Redshift, Glue, Kinesis)
- Compute & Application (Lambda, API Gateway, DynamoDB)
- Chatbot Infrastructure
- Monitoring & Observability
- Tracing & Logging

See [CloudFormation Deployment Guide](CLOUDFORMATION_DEPLOYMENT_GUIDE.md) for details.

### Individual Component Deployment

#### Web Application
```bash
# Complete deployment (S3 + CloudFront + cache invalidation)
./infrastructure/deploy_web_with_cdn.sh

# Initial setup (first time only)
python3 infrastructure/setup_s3_hosting.py
python3 infrastructure/setup_cloudfront.py

# Deploy to S3 only
./infrastructure/deploy_web_app.sh

# Invalidate CloudFront cache
python3 infrastructure/invalidate_cloudfront.py

# Validate deployment setup
python3 validate_web_deployment.py
```

#### API Gateway
```bash
# Deploy API Gateway
./infrastructure/deploy_api_gateway.sh

# Or use Python script
python infrastructure/setup_api_gateway.py --environment development

# Validate setup
python validate_api_gateway_setup.py
```

#### Lambda Functions
```bash
# Deploy Lambda handlers
./infrastructure/deploy_api_lambdas.sh

# Or use Python script
python infrastructure/deploy_api_lambdas.py --region us-east-1

# Validate deployment
python validate_api_lambda_handlers.py
```

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
# Infrastructure as Code
python validate_cloudformation_templates.py

# Individual components
python validate_api_gateway_setup.py
python validate_api_lambda_handlers.py
python validate_kinesis_implementation.py
python validate_redshift_implementation.py
python validate_governance_implementation.py
python validate_recommendation_engine.py
python validate_web_deployment.py
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