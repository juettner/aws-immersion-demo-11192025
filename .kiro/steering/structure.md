# Project Structure

## Directory Organization

```
concert-data-platform/
├── src/                          # Source code
│   ├── models/                   # Pydantic data models
│   ├── services/                 # Business logic and integrations
│   │   └── external_apis/        # External API clients (Spotify, Ticketmaster)
│   ├── infrastructure/           # AWS service clients and utilities
│   └── config/                   # Configuration management
├── web/                          # React frontend application
│   └── src/
│       ├── components/           # Reusable UI components
│       ├── pages/                # Page components
│       ├── services/             # API client
│       ├── hooks/                # Custom React hooks
│       ├── context/              # React context providers
│       ├── types/                # TypeScript type definitions
│       ├── styles/               # Global styles and theme
│       └── config/               # Frontend configuration
├── infrastructure/               # Infrastructure setup scripts
├── sample_data/                  # Sample datasets (CSV, JSON, XML)
├── docs/                         # Documentation
│   ├── api-ingestion/
│   ├── infrastructure/
│   ├── kinesis/
│   └── redshift/
├── .kiro/                        # Kiro configuration
│   ├── specs/                    # Feature specifications
│   └── steering/                 # AI assistant guidance rules
└── validate_*.py                 # Validation scripts (root level)
```

## Code Organization Patterns

### Models (`src/models/`)
- `base.py`: BaseEntity with common fields (created_at, updated_at), Location model
- Domain models: `artist.py`, `venue.py`, `concert.py`, `ticket_sale.py`
- ML models: `recommendation.py`, `ticket_sales_prediction.py`, `venue_popularity.py`
- All models use Pydantic for validation and serialization

### Services (`src/services/`)
- Service classes handle business logic and orchestration
- Naming: `<feature>_service.py` (e.g., `recommendation_service.py`)
- Example usage: `example_<feature>_usage.py`
- Tests: `test_<feature>.py` or `test_<feature>_integration.py`
- External API clients in `external_apis/` subdirectory

### Infrastructure (`src/infrastructure/`)
- AWS service clients: `<service>_client.py` (e.g., `redshift_client.py`, `kinesis_client.py`)
- Service-specific utilities: `<service>_<purpose>.py` (e.g., `redshift_schema.py`, `glue_job_manager.py`)
- Each client encapsulates boto3 interactions for a specific AWS service

### Configuration (`src/config/`)
- `settings.py`: Centralized Pydantic-based configuration with nested settings classes
- `environment.py`: Environment variable loading utilities
- Settings loaded from `.env` file via `Settings.from_env()`

## File Naming Conventions

- **Python modules**: lowercase with underscores (`ticket_sales_prediction_service.py`)
- **Classes**: PascalCase (`TicketSalesPredictionService`, `RedshiftClient`)
- **Functions/methods**: lowercase with underscores (`get_recommendations`, `execute_query`)
- **Constants**: UPPERCASE with underscores (`API_BASE_URL`, `DEFAULT_TIMEOUT`)
- **TypeScript/React**: PascalCase for components (`Button.tsx`), camelCase for utilities

## Validation Scripts

- Located at project root
- Pattern: `validate_<feature>_implementation.py`
- Purpose: Verify implementation structure, imports, and basic functionality
- Run before committing feature implementations

## Documentation

- Feature summaries: `<FEATURE>_SUMMARY.md` at root
- Detailed guides: `docs/<category>/` subdirectories
- README files in each major directory explain purpose and usage
- Infrastructure setup guides in `infrastructure/` directory

## AWS Resource Naming

- S3 Buckets: `concert-data-{environment}-{purpose}`
- Kinesis Streams: `concert-stream-{data-type}`
- Glue Jobs: `concert-etl-{job-name}`
- Redshift Cluster: `concert-warehouse-{environment}`
- SageMaker Endpoints: `{model-name}-{timestamp}`
- DynamoDB Tables: `concert-chatbot-{table-name}`

## Key Architectural Patterns

- **Separation of Concerns**: Models, services, and infrastructure are clearly separated
- **Dependency Injection**: Clients and services accept configuration via constructor
- **Async/Await**: External API clients use async patterns with httpx
- **Error Handling**: Structured logging with contextual information
- **Rate Limiting**: Token bucket pattern in base API client
- **Retry Logic**: Exponential backoff for transient failures
- **Type Safety**: Pydantic models for Python, TypeScript for frontend
