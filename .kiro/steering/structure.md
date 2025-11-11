---
inclusion: always
---

# Project Structure & Conventions

## Directory Layout

- `src/models/` - Pydantic data models (domain + ML models)
- `src/services/` - Business logic, orchestration, and integrations
- `src/services/external_apis/` - External API clients (Spotify, Ticketmaster)
- `src/infrastructure/` - AWS service clients (boto3 wrappers)
- `src/config/` - Centralized Pydantic configuration
- `web/src/` - React frontend (components, pages, hooks, services)
- `infrastructure/` - Setup scripts for AWS resources
- `docs/` - ALL documentation (except root README.md)
  - `docs/api/` - API documentation
  - `docs/api-ingestion/` - API integration guides
  - `docs/features/` - Feature implementation summaries
  - `docs/guides/` - How-to guides and tutorials
  - `docs/infrastructure/` - Infrastructure setup and configuration
  - `docs/kinesis/` - Kinesis streaming documentation
  - `docs/redshift/` - Redshift data warehouse documentation
  - `docs/services/` - Service-specific documentation
- `validate_*.py` - Root-level validation scripts

## Naming Conventions

**Python:**
- Modules: `lowercase_with_underscores.py`
- Classes: `PascalCase`
- Functions/methods: `lowercase_with_underscores()`
- Constants: `UPPERCASE_WITH_UNDERSCORES`

**TypeScript/React:**
- Components: `PascalCase.tsx`
- Utilities: `camelCase.ts`

**File Patterns:**
- Services: `<feature>_service.py`
- Examples: `example_<feature>_usage.py`
- Tests: `test_<feature>.py` or `test_<feature>_integration.py`
- Validation: `validate_<feature>_implementation.py` (root level)
- AWS clients: `<service>_client.py`

**AWS Resources:**
- S3: `concert-data-{environment}-{purpose}`
- Kinesis: `concert-stream-{data-type}`
- Glue: `concert-etl-{job-name}`
- Redshift: `concert-warehouse-{environment}`
- SageMaker: `{model-name}-{timestamp}`
- DynamoDB: `concert-chatbot-{table-name}`

## Code Organization Rules

**Models (`src/models/`):**
- All models use Pydantic for validation
- `base.py` contains BaseEntity (created_at, updated_at) and Location
- Domain models: artist, venue, concert, ticket_sale
- ML models: recommendation, ticket_sales_prediction, venue_popularity

**Services (`src/services/`):**
- Handle business logic and orchestration
- Accept configuration via constructor (dependency injection)
- Include example usage and test files alongside implementation

**Infrastructure (`src/infrastructure/`):**
- Each AWS service gets its own client class
- Encapsulate all boto3 interactions
- Service-specific utilities use pattern: `<service>_<purpose>.py`

**Configuration (`src/config/`):**
- `settings.py` uses nested Pydantic settings classes
- Load via `Settings.from_env()` from `.env` file
- Categories: ExternalAPISettings, AWSSettings, AgentCoreSettings, DatabaseSettings

## Architectural Patterns

- **Separation of Concerns**: Models, services, infrastructure are distinct layers
- **Type Safety**: Pydantic (Python), TypeScript (frontend)
- **Async/Await**: Use httpx for external API clients
- **Error Handling**: Structured logging with context
- **Rate Limiting**: Token bucket pattern in base API client
- **Retry Logic**: Exponential backoff for transient failures

## Documentation Standards

- ALL documentation (except root README.md) goes in `docs/` folder
- Feature implementation summaries: `docs/features/<FEATURE>_SUMMARY.md`
- Service documentation: `docs/services/<SERVICE>_README.md`
- How-to guides: `docs/guides/<GUIDE_NAME>.md`
- Infrastructure setup: `docs/infrastructure/<COMPONENT>_GUIDE.md`
- API documentation: `docs/api/README.md`
- Each docs subdirectory has a README explaining purpose
- Use `docs/DOCUMENTATION_INDEX.md` for navigation

## Validation Workflow

Run `validate_<feature>_implementation.py` scripts before committing to verify structure, imports, and basic functionality.
