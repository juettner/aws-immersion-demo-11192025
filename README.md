# Concert Data Platform - AWS Data Readiness & AI Demo

A comprehensive data platform demonstrating AWS data services, machine learning capabilities, and AI-powered insights for the concert and live entertainment industry.

## Overview

This platform showcases modern data engineering and AI/ML practices by ingesting, processing, and analyzing concert data from multiple sources. It provides predictive analytics, recommendations, and an AI-powered chatbot interface for exploring concert insights.

## Architecture

The platform leverages the following AWS services:

- **Data Ingestion**: Kinesis Data Streams, Lambda, S3
- **Data Processing**: AWS Glue, Redshift, Lake Formation
- **Machine Learning**: Amazon SageMaker
- **AI Services**: Amazon Bedrock AgentCore (Runtime, Memory, Code Interpreter, Browser)
- **API & Web**: API Gateway, CloudFront
- **Monitoring**: CloudWatch, X-Ray

## Features

### ✅ Completed

#### 1. Data Models & Configuration
- Pydantic-based data models for Artist, Venue, Concert, and TicketSale entities
- Comprehensive validation and serialization
- Centralized configuration management for AWS services and external APIs

#### 2. Data Ingestion Service
- **External API Connectors**: Spotify and Ticketmaster integration with rate limiting and retry logic
- **File Upload Processor**: Support for CSV, JSON, and XML formats with validation
- **Kinesis Streaming**: Real-time data ingestion with Lambda processing
- Comprehensive error handling and data quality checks

#### 3. ETL Pipeline
- **AWS Glue Jobs**: Data transformation, normalization, and deduplication using fuzzy matching
- **Redshift Data Warehouse**: Optimized schema with distribution keys and stored procedures
- **Lake Formation**: Data governance, access control, and audit logging
- End-to-end integration tests validating data flow

#### 4. AI/ML Models
- **Venue Popularity Ranking**: Feature engineering and SageMaker model for ranking venues by performance metrics
- **Ticket Sales Prediction**: Regression model predicting sales with confidence scoring
- Both models include training pipelines, deployment, and evaluation capabilities

### 🚧 In Progress / Planned

#### 5. Recommendation Engine
- Collaborative filtering for concert recommendations
- Content-based artist and venue matching
- Personalized recommendation API

#### 6. Model Evaluation & Monitoring
- Performance metrics and validation pipelines
- Prediction drift detection
- Automated retraining triggers

#### 7. AgentCore-Powered AI Chatbot
- Natural language query processing
- Dynamic data analysis with Code Interpreter
- Real-time external data fetching with Browser tool
- Conversation persistence with Memory service
- Data visualization generation

#### 8. Web Interface
- React-based chat interface with WebSocket support
- Analytics dashboard with interactive visualizations
- API Gateway with authentication and rate limiting

#### 9. Infrastructure & Deployment
- Infrastructure as Code (CDK/Terraform)
- CI/CD pipeline with automated testing
- Monitoring and observability setup
- Performance optimization

#### 10. Demo Data & Integration
- Synthetic concert data generator
- End-to-end system validation
- Demo scenarios and user journeys

## Project Structure

```
concert-data-platform/
├── src/
│   ├── models/              # Pydantic data models
│   ├── services/            # Business logic and integrations
│   │   └── external_apis/   # Spotify, Ticketmaster clients
│   ├── infrastructure/      # AWS service clients and utilities
│   └── config/              # Configuration management
├── sample_data/             # Sample datasets for testing
├── .kiro/specs/             # Feature specifications and design docs
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Getting Started

### Prerequisites

- Python 3.9+
- AWS Account with appropriate permissions
- API keys for Spotify and Ticketmaster (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd concert-data-platform
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your AWS credentials and API keys
```

### Running Examples

#### Data Ingestion
```bash
python src/services/external_apis/example_usage.py
```

#### Kinesis Streaming
```bash
python src/services/example_kinesis_usage.py
```

#### ETL Pipeline
```bash
python src/services/example_glue_etl_usage.py
```

#### Redshift Queries
```bash
python src/services/example_redshift_usage.py
```

#### ML Predictions
```bash
# Venue popularity
python src/services/example_venue_popularity_usage.py

# Ticket sales prediction
python src/services/example_ticket_sales_prediction_usage.py
```

### Running Tests

```bash
# Ingestion tests
python src/services/run_ingestion_tests.py

# Kinesis integration tests
python src/services/test_kinesis_integration.py

# ETL integration tests
python src/services/test_etl_integration.py

# Redshift service tests
python src/services/test_redshift_service.py
```

### Validation Scripts

Validate implementations:
```bash
python validate_implementation_structure.py
python validate_kinesis_implementation.py
python validate_glue_etl_implementation.py
python validate_redshift_implementation.py
python validate_governance_implementation.py
python validate_venue_popularity_implementation.py
python validate_ticket_sales_prediction.py
```

## Data Models

### Artist
- Artist ID, name, genre, popularity score
- Spotify integration for metadata enrichment

### Venue
- Venue ID, name, location, capacity, type
- Ticketmaster integration for venue details

### Concert
- Concert ID, artist, venue, event date
- Ticket pricing, attendance, revenue tracking

### Ticket Sale
- Sale ID, concert, customer, quantity, price
- Purchase timestamp and payment details

## ML Models

### Venue Popularity Model
- **Features**: Concert frequency, attendance rates, revenue, artist diversity
- **Output**: Popularity ranking and score
- **Use Case**: Identify top-performing venues for booking decisions

### Ticket Sales Prediction Model
- **Features**: Artist popularity, venue capacity, historical sales, pricing, temporal factors
- **Output**: Predicted sales with confidence score
- **Use Case**: Forecast ticket sales for upcoming concerts

## AWS Services Configuration

### Required IAM Permissions
- S3: Read/Write access to data buckets
- Kinesis: Stream producer/consumer permissions
- Glue: Job execution and catalog access
- Redshift: Query execution and data loading
- SageMaker: Model training and endpoint deployment
- Lake Formation: Data governance and access control

### Resource Naming Convention
- S3 Buckets: `concert-data-{environment}-{purpose}`
- Kinesis Streams: `concert-stream-{data-type}`
- Glue Jobs: `concert-etl-{job-name}`
- Redshift Cluster: `concert-warehouse-{environment}`
- SageMaker Endpoints: `{model-name}-{timestamp}`

## Development Roadmap

See `.kiro/specs/data-readiness-ai-demo/tasks.md` for detailed implementation plan.

**Current Phase**: AI/ML Enhancement & Chatbot Development

**Next Milestones**:
1. Complete recommendation engine
2. Implement AgentCore chatbot
3. Build web interface
4. Deploy infrastructure
5. Generate demo data

## Contributing

This is a demo project showcasing AWS data and AI capabilities. For questions or suggestions, please open an issue.

## License

This project is for demonstration purposes.

## Documentation

- [Project Structure](PROJECT_STRUCTURE.md)
- [Lake Formation Setup](src/infrastructure/LAKE_FORMATION_README.md)
- [SageMaker Testing Guide](SAGEMAKER_TESTING_GUIDE.md)
- [Design Document](.kiro/specs/data-readiness-ai-demo/design.md)
- [Requirements](.kiro/specs/data-readiness-ai-demo/requirements.md)

## Contact

For AWS Immersion Day demonstrations and technical deep-dives.