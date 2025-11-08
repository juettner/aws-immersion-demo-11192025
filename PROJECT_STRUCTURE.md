# Project Structure

This document describes the directory structure and organization of the Concert Data Platform project.

## Directory Layout

```
concert-data-platform/
├── src/                          # Main source code directory
│   ├── __init__.py              # Main package initialization
│   ├── models/                   # Data models with Pydantic validation
│   │   ├── __init__.py          # Models package exports
│   │   ├── base.py              # Base entity and common types
│   │   ├── artist.py            # Artist data model
│   │   ├── venue.py             # Venue data model
│   │   ├── concert.py           # Concert data model
│   │   ├── ticket_sale.py       # Ticket sale data model
│   │   └── validation_examples.py # Model usage examples
│   ├── services/                 # Business logic and service layer
│   │   └── __init__.py          # Services package initialization
│   ├── infrastructure/           # Infrastructure and AWS integrations
│   │   └── __init__.py          # Infrastructure package initialization
│   └── config/                   # Configuration management
│       ├── __init__.py          # Config package exports
│       ├── settings.py          # Main configuration classes
│       └── environment.py       # Environment-specific configuration
├── .env.example                  # Example environment variables
├── requirements.txt              # Python dependencies
├── PROJECT_STRUCTURE.md          # This file
└── README.md                     # Project documentation
```

## Package Descriptions

### `src/models/`
Contains all data models using Pydantic for validation and serialization:
- **Artist**: Musical artists and bands with metadata
- **Venue**: Concert venues with location and capacity information
- **Concert**: Concert events linking artists and venues
- **TicketSale**: Individual ticket purchase transactions
- **Base classes**: Common entity patterns and location types

### `src/services/`
Will contain business logic and service layer components:
- Data ingestion services
- ETL processing services
- AI insights engine
- External API connectors

### `src/infrastructure/`
Will contain AWS infrastructure and deployment components:
- AWS service clients and configurations
- Infrastructure as Code (CDK/Terraform)
- Monitoring and observability setup

### `src/config/`
Configuration management system:
- **Settings**: Centralized configuration for all services
- **Environment**: Environment-specific configuration loading
- Support for AWS services, external APIs, and AgentCore services

## Configuration Management

The project uses a hierarchical configuration system:

1. **Environment Variables**: Primary configuration source
2. **`.env` Files**: Local development configuration
3. **Default Values**: Fallback configuration in code

### Configuration Categories

- **AWS Services**: S3, Redshift, Kinesis, SageMaker, Lake Formation
- **External APIs**: Spotify, Ticketmaster, MusicBrainz
- **AgentCore Services**: Runtime, Memory, Code Interpreter, Browser, Gateway
- **Database**: PostgreSQL for local development, Redshift for production
- **Application**: General app settings, logging, API configuration

## Data Models

All data models use Pydantic for:
- **Validation**: Automatic data validation with custom validators
- **Serialization**: JSON serialization with proper datetime handling
- **Documentation**: Auto-generated schema documentation
- **Type Safety**: Full type hints and IDE support

### Model Features

- **Base Entity**: Common fields (created_at, updated_at) for all entities
- **Custom Validators**: Business logic validation (e.g., reasonable date ranges)
- **Relationships**: Foreign key references between entities
- **Examples**: Built-in example data for documentation and testing

## Development Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Validate Models**:
   ```bash
   python -m src.models.validation_examples
   ```

## Next Steps

This foundation supports the implementation of:
- Data ingestion services (Task 2)
- ETL processing pipeline (Task 3)
- AI insights engine (Task 4)
- AgentCore chatbot (Task 5)
- Web interface (Task 6)
- Infrastructure deployment (Task 7)
- Demo data generation (Task 8)