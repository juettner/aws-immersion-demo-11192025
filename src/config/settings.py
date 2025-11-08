"""
Configuration management for AWS services and external APIs.
"""
import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field, validator


class AWSConfig(BaseSettings):
    """AWS service configuration."""
    region: str = Field(default="us-east-1", description="AWS region")
    access_key_id: Optional[str] = Field(None, description="AWS access key ID")
    secret_access_key: Optional[str] = Field(None, description="AWS secret access key")
    
    # S3 Configuration
    s3_bucket_raw: str = Field(default="concert-data-raw", description="S3 bucket for raw data")
    s3_bucket_processed: str = Field(default="concert-data-processed", description="S3 bucket for processed data")
    
    # Redshift Configuration
    redshift_cluster_identifier: str = Field(default="concert-data-warehouse", description="Redshift cluster ID")
    redshift_database: str = Field(default="concerts", description="Redshift database name")
    redshift_user: Optional[str] = Field(None, description="Redshift username")
    redshift_password: Optional[str] = Field(None, description="Redshift password")
    redshift_host: Optional[str] = Field(None, description="Redshift cluster endpoint")
    redshift_port: int = Field(default=5439, description="Redshift port")
    
    # Kinesis Configuration
    kinesis_stream_name: str = Field(default="concert-data-stream", description="Kinesis stream name")
    kinesis_shard_count: int = Field(default=1, description="Number of Kinesis shards")
    
    # SageMaker Configuration
    sagemaker_execution_role: Optional[str] = Field(None, description="SageMaker execution role ARN")
    sagemaker_model_bucket: str = Field(default="concert-ml-models", description="S3 bucket for ML models")
    
    # Lake Formation Configuration
    lakeformation_admin_role: Optional[str] = Field(None, description="Lake Formation admin role ARN")
    
    class Config:
        env_prefix = "AWS_"
        case_sensitive = False


class ExternalAPIConfig(BaseSettings):
    """External API configuration."""
    # Spotify API
    spotify_client_id: Optional[str] = Field(None, description="Spotify API client ID")
    spotify_client_secret: Optional[str] = Field(None, description="Spotify API client secret")
    spotify_base_url: str = Field(default="https://api.spotify.com/v1", description="Spotify API base URL")
    
    # Ticketmaster API
    ticketmaster_api_key: Optional[str] = Field(None, description="Ticketmaster API key")
    ticketmaster_base_url: str = Field(
        default="https://app.ticketmaster.com/discovery/v2", 
        description="Ticketmaster API base URL"
    )
    
    # MusicBrainz API
    musicbrainz_base_url: str = Field(
        default="https://musicbrainz.org/ws/2", 
        description="MusicBrainz API base URL"
    )
    musicbrainz_user_agent: str = Field(
        default="ConcertDataPlatform/1.0 (contact@example.com)",
        description="User agent for MusicBrainz API"
    )
    
    # Rate limiting configuration
    api_rate_limit_requests: int = Field(default=100, description="API requests per minute")
    api_rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    api_retry_attempts: int = Field(default=3, description="Number of retry attempts")
    api_retry_backoff: float = Field(default=1.0, description="Retry backoff multiplier")
    
    class Config:
        env_prefix = "API_"
        case_sensitive = False


class AgentCoreConfig(BaseSettings):
    """AgentCore services configuration."""
    runtime_endpoint: Optional[str] = Field(None, description="AgentCore Runtime endpoint")
    memory_endpoint: Optional[str] = Field(None, description="AgentCore Memory endpoint")
    code_interpreter_endpoint: Optional[str] = Field(None, description="AgentCore Code Interpreter endpoint")
    browser_endpoint: Optional[str] = Field(None, description="AgentCore Browser endpoint")
    gateway_endpoint: Optional[str] = Field(None, description="AgentCore Gateway endpoint")
    
    # Authentication
    agentcore_api_key: Optional[str] = Field(None, description="AgentCore API key")
    agentcore_region: str = Field(default="us-east-1", description="AgentCore region")
    
    class Config:
        env_prefix = "AGENTCORE_"
        case_sensitive = False


class DatabaseConfig(BaseSettings):
    """Database configuration for local development and testing."""
    # PostgreSQL for local development
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_database: str = Field(default="concerts_dev", description="PostgreSQL database name")
    postgres_user: str = Field(default="postgres", description="PostgreSQL username")
    postgres_password: str = Field(default="password", description="PostgreSQL password")
    
    # Connection pool settings
    db_pool_size: int = Field(default=10, description="Database connection pool size")
    db_max_overflow: int = Field(default=20, description="Database connection pool overflow")
    
    class Config:
        env_prefix = "DB_"
        case_sensitive = False


class AppConfig(BaseSettings):
    """Main application configuration."""
    app_name: str = Field(default="Concert Data Platform", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=True, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=1, description="Number of API workers")
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed_envs = ['development', 'staging', 'production']
        if v.lower() not in allowed_envs:
            raise ValueError(f'Environment must be one of: {", ".join(allowed_envs)}')
        return v.lower()
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level setting."""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {", ".join(allowed_levels)}')
        return v.upper()
    
    class Config:
        env_prefix = "APP_"
        case_sensitive = False


class Settings:
    """Main settings class that combines all configuration sections."""
    
    def __init__(self):
        self.aws = AWSConfig()
        self.external_apis = ExternalAPIConfig()
        self.agentcore = AgentCoreConfig()
        self.database = DatabaseConfig()
        self.app = AppConfig()
    
    def get_aws_credentials(self) -> Dict[str, Any]:
        """Get AWS credentials for boto3 clients."""
        credentials = {
            'region_name': self.aws.region
        }
        
        if self.aws.access_key_id and self.aws.secret_access_key:
            credentials.update({
                'aws_access_key_id': self.aws.access_key_id,
                'aws_secret_access_key': self.aws.secret_access_key
            })
        
        return credentials
    
    def get_redshift_connection_string(self) -> str:
        """Get Redshift connection string."""
        if not all([self.aws.redshift_host, self.aws.redshift_user, self.aws.redshift_password]):
            raise ValueError("Redshift connection parameters are not fully configured")
        
        return (
            f"postgresql://{self.aws.redshift_user}:{self.aws.redshift_password}"
            f"@{self.aws.redshift_host}:{self.aws.redshift_port}/{self.aws.redshift_database}"
        )
    
    @property
    def aws_region(self) -> str:
        """Get AWS region."""
        return self.aws.region
    
    @property
    def redshift_host(self) -> Optional[str]:
        """Get Redshift host."""
        return self.aws.redshift_host
    
    @property
    def redshift_port(self) -> int:
        """Get Redshift port."""
        return self.aws.redshift_port
    
    @property
    def redshift_database(self) -> str:
        """Get Redshift database."""
        return self.aws.redshift_database
    
    @property
    def redshift_user(self) -> Optional[str]:
        """Get Redshift user."""
        return self.aws.redshift_user
    
    @property
    def redshift_password(self) -> Optional[str]:
        """Get Redshift password."""
        return self.aws.redshift_password
    
    def get_postgres_connection_string(self) -> str:
        """Get PostgreSQL connection string for local development."""
        return (
            f"postgresql://{self.database.postgres_user}:{self.database.postgres_password}"
            f"@{self.database.postgres_host}:{self.database.postgres_port}/{self.database.postgres_database}"
        )


# Global settings instance
_settings = Settings()

def get_settings() -> Settings:
    """Get the global settings instance."""
    return _settings