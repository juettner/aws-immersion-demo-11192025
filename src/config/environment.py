"""
Environment-specific configuration management.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional


def load_env_file(env_file: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_file: Path to the .env file. If None, looks for .env in project root.
    
    Returns:
        Dictionary of environment variables loaded from the file.
    """
    if env_file is None:
        # Look for .env file in project root
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
    
    env_vars = {}
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value
                    # Set in os.environ if not already set
                    if key not in os.environ:
                        os.environ[key] = value
    
    return env_vars


def get_environment_config() -> Dict[str, Any]:
    """
    Get environment-specific configuration based on APP_ENVIRONMENT.
    
    Returns:
        Dictionary containing environment-specific settings.
    """
    environment = os.getenv('APP_ENVIRONMENT', 'development').lower()
    
    base_config = {
        'environment': environment,
        'debug': environment == 'development',
        'testing': environment == 'testing',
    }
    
    if environment == 'development':
        return {
            **base_config,
            'log_level': 'DEBUG',
            'api_workers': 1,
            'db_pool_size': 5,
            'aws_region': 'us-east-1',
        }
    
    elif environment == 'staging':
        return {
            **base_config,
            'log_level': 'INFO',
            'api_workers': 2,
            'db_pool_size': 10,
            'aws_region': 'us-east-1',
        }
    
    elif environment == 'production':
        return {
            **base_config,
            'log_level': 'WARNING',
            'api_workers': 4,
            'db_pool_size': 20,
            'aws_region': 'us-east-1',
        }
    
    else:
        # Default to development settings for unknown environments
        return {
            **base_config,
            'log_level': 'INFO',
            'api_workers': 1,
            'db_pool_size': 5,
            'aws_region': 'us-east-1',
        }


def validate_required_env_vars() -> None:
    """
    Validate that all required environment variables are set.
    
    Raises:
        ValueError: If required environment variables are missing.
    """
    required_vars = []
    missing_vars = []
    
    environment = os.getenv('APP_ENVIRONMENT', 'development').lower()
    
    # Always required
    # (None for development environment to allow easy setup)
    
    # Required for staging and production
    if environment in ['staging', 'production']:
        required_vars.extend([
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_REDSHIFT_HOST',
            'AWS_REDSHIFT_USER',
            'AWS_REDSHIFT_PASSWORD',
        ])
    
    # Check for missing variables
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables for {environment} environment: "
            f"{', '.join(missing_vars)}"
        )


# Load environment variables from .env file on import
load_env_file()