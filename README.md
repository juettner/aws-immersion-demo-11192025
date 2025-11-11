# Concert Data Platform - AWS Data Readiness & AI Demo

A comprehensive data platform demonstrating AWS data services, machine learning capabilities, and AI-powered insights for the concert and live entertainment industry.

> **📚 [Complete Documentation Available in `docs/` folder](docs/README.md)**

## Project Status

**Overall Completion**: ~80% | **Current Phase**: Web Interface & Infrastructure Deployment

| Component | Status | Progress |
|-----------|--------|----------|
| Data Models & Configuration | ✅ Complete | 100% |
| Data Ingestion (APIs, Files, Streaming) | ✅ Complete | 100% |
| ETL Pipeline (Glue, Redshift, Lake Formation) | ✅ Complete | 100% |
| ML Models (Venue, Sales, Recommendations) | ✅ Complete | 100% |
| AI/ML Services (8 services) | ✅ Complete | 100% |
| API Layer (ML & Chatbot APIs) | ✅ Complete | 100% |
| API Gateway Configuration | ✅ Complete | 100% |
| Documentation | ✅ Complete | 100% |
| Web Interface | 🚧 In Progress | 60% |
| Infrastructure & Deployment | 🚧 In Progress | 30% |
| Demo Data & Integration | 🚧 Planned | 0% |

**Key Achievements**:
- ✅ Full data pipeline from ingestion to warehouse
- ✅ 3 production-ready ML models with SageMaker integration
- ✅ 8 AI/ML services including chatbot, NL-to-SQL, and data analysis
- ✅ RESTful APIs for ML inference and chat interactions
- ✅ **AWS API Gateway configured with CORS, throttling, and validation**
- ✅ Comprehensive documentation with 50+ guides and summaries
- ✅ React web interface with chat and analytics dashboards

**Next Steps**: Deploy Lambda functions, complete infrastructure automation, generate demo data

## Overview

This platform showcases modern data engineering and AI/ML practices by ingesting, processing, and analyzing concert data from multiple sources. It provides predictive analytics, recommendations, and an AI-powered chatbot interface for exploring concert insights.

## Architecture

The platform leverages the following AWS services:

- **Data Ingestion**: Kinesis Data Streams, Lambda, S3
- **Data Processing**: AWS Glue, Redshift, Lake Formation
- **Machine Learning**: Amazon SageMaker
- **AI Services**: Amazon Bedrock AgentCore (Runtime, Memory, Code Interpreter, Browser)
- **API Layer**: API Gateway (REST API with CORS, throttling, validation)
- **Web Interface**: React + Vite, hosted on S3/CloudFront
- **Monitoring**: CloudWatch Logs, CloudWatch Metrics, X-Ray Tracing

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
- **Recommendation Engine**: Collaborative and content-based filtering for personalized concert recommendations
  - User-based and item-based collaborative filtering
  - Content-based filtering using artist genres, popularity, and venue characteristics
  - Hybrid recommendation strategies combining multiple signals
  - Batch recommendation capabilities for multiple users
  - Artist and venue similarity scoring

#### 5. AI/ML Services
- **Model Evaluation Service**: Performance metrics, validation pipelines, and model comparison
- **Model Monitoring Service**: Real-time monitoring, drift detection, and alerting
- **Conversation Memory Service**: Persistent conversation context using DynamoDB and Bedrock AgentCore Memory
- **Data Analysis Service**: AI-powered data analysis with natural language queries
- **NL to SQL Service**: Natural language to SQL query translation
- **Chatbot Service**: Interactive AI assistant with multi-turn conversations
- **Data Visualization Service**: Automated chart and graph generation
- **External Data Enrichment**: Real-time data fetching and integration

#### 6. API Layer
- **ML API**: Model inference endpoints for predictions and recommendations
- **Chatbot API**: Chat interaction endpoints with streaming support
- RESTful API design with comprehensive error handling

#### 7. API Gateway Configuration
- **REST API**: Unified API Gateway for production deployments
- **Endpoints**: Chat (`/chat`, `/history`), Analytics (`/venues/popularity`, `/predictions/tickets`, `/recommendations`)
- **CORS**: Enabled for all endpoints with configurable origins
- **Throttling**: 500 req/sec rate limit, 1000 burst limit, 100K daily quota
- **Validation**: JSON schema validation for request/response
- **Monitoring**: CloudWatch Logs and X-Ray tracing enabled
- **Deployment**: CloudFormation template and Python automation scripts
- **Documentation**: Complete setup guide and API reference

#### 8. Documentation
- ✅ **Centralized Documentation Structure**: All docs organized in `docs/` folder
- ✅ **Feature Summaries**: Implementation details for all AI/ML features
- ✅ **Service Documentation**: Detailed service architecture and usage guides
- ✅ **How-To Guides**: Step-by-step tutorials and best practices
- ✅ **Infrastructure Guides**: AWS setup and configuration documentation
- ✅ **Documentation Index**: Searchable index with navigation by topic and role

### 🚧 In Progress / Planned

#### 9. Web Interface
- ✅ React-based chat interface with message history
- ✅ Analytics dashboard with interactive visualizations (Recharts)
- ✅ API integration with axios and React Query
- 🚧 WebSocket support for real-time updates
- 🚧 User authentication and session management

#### 10. Infrastructure & Deployment
- ✅ API Gateway CloudFormation template
- ✅ Automated deployment scripts (Bash + Python)
- ✅ API Gateway client for programmatic management
- 🚧 Lambda function deployment automation
- 🚧 Infrastructure as Code for complete stack (CDK/Terraform)
- 🚧 CI/CD pipeline with automated testing
- 🚧 Monitoring dashboards and alerting

#### 11. Demo Data & Integration
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
│   ├── api/                 # API endpoints (ML, Chatbot)
│   └── config/              # Configuration management
├── web/                     # React frontend application
├── docs/                    # Complete documentation (organized by category)
│   ├── features/            # Feature implementation summaries
│   ├── services/            # Service documentation
│   ├── guides/              # How-to guides and tutorials
│   ├── infrastructure/      # AWS setup and configuration
│   ├── api/                 # API documentation
│   ├── api-ingestion/       # Data ingestion guides
│   ├── kinesis/             # Streaming documentation
│   └── redshift/            # Data warehouse documentation
├── infrastructure/          # AWS setup scripts
├── sample_data/             # Sample datasets for testing
├── .kiro/specs/             # Feature specifications and design docs
├── validate_*.py            # Validation scripts
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed organization guide.

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

### Deploying API Gateway

Deploy the production API Gateway:

```bash
# Interactive deployment
./infrastructure/deploy_api_gateway.sh

# Or use Python script directly
python infrastructure/setup_api_gateway.py --environment development --region us-east-1

# Validate deployment
python validate_api_gateway_setup.py
```

See [API Gateway Setup Guide](docs/infrastructure/API_GATEWAY_SETUP_GUIDE.md) for detailed instructions.

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

# Recommendation engine
python src/services/example_recommendation_usage.py
```

#### AI Services
```bash
# Chatbot service
python src/services/example_chatbot_usage.py

# Conversation memory
python src/services/example_conversation_memory_usage.py

# NL to SQL
python src/services/example_nl_to_sql_usage.py

# Data analysis
python src/services/example_data_analysis_usage.py
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
# Infrastructure
python validate_api_gateway_setup.py
python validate_implementation_structure.py
python validate_kinesis_implementation.py
python validate_glue_etl_implementation.py
python validate_redshift_implementation.py
python validate_governance_implementation.py

# ML Models
python validate_venue_popularity_implementation.py
python validate_ticket_sales_prediction.py
python validate_recommendation_engine.py

# AI Services
python validate_chatbot_service.py
python validate_conversation_memory.py
python validate_nl_to_sql_service.py
python validate_data_analysis_service.py

# APIs
python validate_chatbot_api.py
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

### Recommendation Engine
- **Collaborative Filtering**: User-based and item-based approaches using cosine similarity
- **Content-Based Filtering**: Artist similarity (genre, popularity) and venue similarity (location, capacity, type)
- **Hybrid Strategies**: Combines multiple recommendation signals with weighted scoring
- **Output**: Personalized concert, artist, and venue recommendations with confidence scores
- **Use Case**: Suggest concerts to users based on preferences and historical attendance patterns

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

See [`.kiro/specs/data-readiness-ai-demo/tasks.md`](.kiro/specs/data-readiness-ai-demo/tasks.md) for detailed implementation plan.

**Current Phase**: Infrastructure Deployment & Integration

**Completed Phases**:
- ✅ Phase 1: Data Foundation (Models, Configuration, Ingestion)
- ✅ Phase 2: Data Processing (ETL, Warehouse, Governance)
- ✅ Phase 3: Machine Learning (3 Models + SageMaker Integration)
- ✅ Phase 4: AI Services (8 Services + APIs)
- ✅ Phase 5: Documentation (Centralized & Organized)
- ✅ Phase 6: Web Interface (React Components & Pages)
- ✅ Phase 7: API Gateway Configuration (REST API with CORS & Throttling)

**Next Milestones**:
1. Deploy Lambda functions for API Gateway integration
2. Complete infrastructure automation with IaC
3. Set up CI/CD pipeline with automated testing
4. Generate synthetic demo data and validation scenarios
5. Performance optimization and monitoring dashboards

## Documentation

All documentation is now centralized in the `docs/` folder for easy navigation:

- **[📚 Complete Documentation Hub](docs/README.md)** - Start here
- **[📑 Documentation Index](docs/DOCUMENTATION_INDEX.md)** - Full index with search
- **[🏗️ Project Structure](docs/PROJECT_STRUCTURE.md)** - Code organization guide

### Quick Links by Category

- **Features**: [AI/ML Implementation Summaries](docs/features/)
- **Services**: [Service Documentation](docs/services/)
- **Guides**: [How-To Guides & Tutorials](docs/guides/)
- **Infrastructure**: [AWS Setup & Configuration](docs/infrastructure/)
  - [API Gateway Setup Guide](docs/infrastructure/API_GATEWAY_SETUP_GUIDE.md)
  - [API Gateway Summary](docs/infrastructure/API_GATEWAY_SUMMARY.md)
- **API**: [API Documentation](docs/api/)
  - [API Gateway Reference](docs/api/API_GATEWAY_REFERENCE.md)
- **Data Ingestion**: [API Integration Guides](docs/api-ingestion/)
- **Streaming**: [Kinesis Setup](docs/kinesis/)
- **Data Warehouse**: [Redshift Configuration](docs/redshift/)

### Specifications

- [Design Document](.kiro/specs/data-readiness-ai-demo/design.md)
- [Requirements](.kiro/specs/data-readiness-ai-demo/requirements.md)
- [Implementation Tasks](.kiro/specs/data-readiness-ai-demo/tasks.md)
