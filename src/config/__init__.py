"""
Configuration management package for the concert data platform.

This package provides centralized configuration management for:
- AWS services (S3, Redshift, Kinesis, SageMaker, Lake Formation)
- External APIs (Spotify, Ticketmaster, MusicBrainz)
- AgentCore services (Runtime, Memory, Code Interpreter, Browser, Gateway)
- Database connections
- Application settings
"""

from .settings import Settings, settings
from .environment import load_env_file, get_environment_config, validate_required_env_vars

__all__ = [
    'Settings',
    'settings',
    'load_env_file',
    'get_environment_config', 
    'validate_required_env_vars'
]