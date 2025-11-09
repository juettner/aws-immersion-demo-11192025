import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ExternalAPISettings(BaseModel):
    """External API configuration."""
    model_config = ConfigDict(extra='forbid')
    
    spotify_client_id: Optional[str] = Field(default=None)
    spotify_client_secret: Optional[str] = Field(default=None)
    spotify_base_url: str = Field(default="https://api.spotify.com/v1")
    ticketmaster_api_key: Optional[str] = Field(default=None)
    ticketmaster_base_url: str = Field(default="https://app.ticketmaster.com/discovery/v2")
    musicbrainz_user_agent: Optional[str] = Field(default="ConcertDataPlatform/1.0")
    api_rate_limit_requests: int = Field(default=100)
    api_retry_attempts: int = Field(default=3)
    api_retry_backoff: float = Field(default=1.0)


class AWSSettings(BaseModel):
    """AWS service configuration."""
    model_config = ConfigDict(extra='forbid')
    
    region: str = Field(default="us-east-1")
    s3_bucket_raw: Optional[str] = Field(default=None)
    s3_bucket_processed: Optional[str] = Field(default=None)
    kinesis_stream_name: Optional[str] = Field(default=None)
    redshift_cluster_id: Optional[str] = Field(default=None)
    redshift_database: Optional[str] = Field(default="concert_data")
    redshift_user: Optional[str] = Field(default=None)
    redshift_password: Optional[str] = Field(default=None)
    glue_database: str = Field(default="concert_catalog")
    sagemaker_role_arn: Optional[str] = Field(default=None)


class AgentCoreSettings(BaseModel):
    """AgentCore service configuration."""
    model_config = ConfigDict(extra='forbid')
    
    runtime_endpoint: Optional[str] = Field(default=None)
    memory_endpoint: Optional[str] = Field(default=None)
    code_interpreter_endpoint: Optional[str] = Field(default=None)
    browser_endpoint: Optional[str] = Field(default=None)
    gateway_endpoint: Optional[str] = Field(default=None)


class DatabaseSettings(BaseModel):
    """Database configuration."""
    model_config = ConfigDict(extra='forbid')
    
    connection_string: Optional[str] = Field(default=None)
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    model_config = ConfigDict(extra='forbid')

    # Application
    app_name: str = Field(default="Concert Data Platform")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # Nested configurations
    external_apis: ExternalAPISettings = Field(default_factory=ExternalAPISettings)
    aws: AWSSettings = Field(default_factory=AWSSettings)
    agentcore: AgentCoreSettings = Field(default_factory=AgentCoreSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the allowed values."""
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'environment must be one of {allowed}')
        return v

    @classmethod
    def from_env(cls) -> 'Settings':
        """Create Settings instance from environment variables."""
        return cls(
            app_name=os.getenv('APP_NAME', 'Concert Data Platform'),
            environment=os.getenv('ENVIRONMENT', 'development'),
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            external_apis=ExternalAPISettings(
                spotify_client_id=os.getenv('API_SPOTIFY_CLIENT_ID'),
                spotify_client_secret=os.getenv('API_SPOTIFY_CLIENT_SECRET'),
                ticketmaster_api_key=os.getenv('API_TICKETMASTER_API_KEY'),
                musicbrainz_user_agent=os.getenv('API_MUSICBRAINZ_USER_AGENT', 'ConcertDataPlatform/1.0'),
            ),
            aws=AWSSettings(
                region=os.getenv('AWS_REGION', 'us-east-1'),
                s3_bucket_raw=os.getenv('AWS_S3_BUCKET_RAW'),
                s3_bucket_processed=os.getenv('AWS_S3_BUCKET_PROCESSED'),
                kinesis_stream_name=os.getenv('AWS_KINESIS_STREAM_NAME'),
                redshift_cluster_id=os.getenv('AWS_REDSHIFT_CLUSTER_ID'),
                redshift_database=os.getenv('AWS_REDSHIFT_DATABASE', 'concert_data'),
                redshift_user=os.getenv('AWS_REDSHIFT_USER'),
                redshift_password=os.getenv('AWS_REDSHIFT_PASSWORD'),
                glue_database=os.getenv('AWS_GLUE_DATABASE', 'concert_catalog'),
                sagemaker_role_arn=os.getenv('AWS_SAGEMAKER_ROLE_ARN'),
            ),
            agentcore=AgentCoreSettings(
                runtime_endpoint=os.getenv('AGENTCORE_RUNTIME_ENDPOINT'),
                memory_endpoint=os.getenv('AGENTCORE_MEMORY_ENDPOINT'),
                code_interpreter_endpoint=os.getenv('AGENTCORE_CODE_INTERPRETER_ENDPOINT'),
                browser_endpoint=os.getenv('AGENTCORE_BROWSER_ENDPOINT'),
                gateway_endpoint=os.getenv('AGENTCORE_GATEWAY_ENDPOINT'),
            ),
            database=DatabaseSettings(
                connection_string=os.getenv('DATABASE_CONNECTION_STRING'),
                pool_size=int(os.getenv('DATABASE_POOL_SIZE', '10')),
                max_overflow=int(os.getenv('DATABASE_MAX_OVERFLOW', '20')),
            )
        )


# Global settings instance
settings = Settings.from_env()