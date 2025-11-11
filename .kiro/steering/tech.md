# Technology Stack

## Backend

- **Language**: Python 3.9+
- **Data Validation**: Pydantic 2.x for models and configuration
- **HTTP Clients**: httpx (async), requests
- **Data Processing**: pandas, numpy
- **Fuzzy Matching**: fuzzywuzzy, python-levenshtein
- **Database**: SQLAlchemy 2.x, psycopg2-binary
- **Logging**: structlog
- **Testing**: pytest, pytest-asyncio, pytest-mock
- **Code Quality**: black, flake8, mypy

## Frontend (Web Interface)

- **Framework**: React 19.2 with TypeScript
- **Build Tool**: Vite 7.x
- **State Management**: @tanstack/react-query
- **HTTP Client**: axios
- **Routing**: react-router-dom
- **Charts**: recharts
- **Linting**: ESLint 9.x with typescript-eslint
- **Formatting**: Prettier

## AWS Services

- **Data Ingestion**: Kinesis Data Streams, Lambda, S3
- **Data Processing**: AWS Glue, Redshift, Lake Formation
- **Machine Learning**: Amazon SageMaker
- **AI Services**: Amazon Bedrock AgentCore (Runtime, Memory, Code Interpreter, Browser)
- **Storage**: DynamoDB (conversations, preferences)
- **SDK**: boto3, botocore, sagemaker

## Common Commands

### Python Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run validation scripts
python validate_<feature>_implementation.py

# Run example usage
python src/services/example_<feature>_usage.py

# Run tests
python src/services/test_<feature>.py
pytest

# Code formatting
black src/
flake8 src/
mypy src/
```

### Web Frontend

```bash
# Navigate to web directory
cd web

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Format code
npm run format
npm run format:check

# Preview production build
npm run preview
```

## Development Environment

- **Virtual Environment**: `.venv/` (Python)
- **Node Modules**: `web/node_modules/`
- **Environment Variables**: `.env` (root), `web/.env.development`
- **Shell**: zsh on macOS

## Configuration

- Centralized settings in `src/config/settings.py` using Pydantic
- Environment-based configuration loaded from `.env`
- Settings categories: ExternalAPISettings, AWSSettings, AgentCoreSettings, DatabaseSettings
