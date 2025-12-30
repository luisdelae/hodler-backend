"""
Environment variable configuration helpers
"""
import os
from typing import Optional


def get_required_env(key: str) -> str:
    """
    Get required environment variable or raise error
    
    Args:
        key: Environment variable name
    
    Returns:
        Environment variable value
    
    Raises:
        ValueError: If environment variable not set
    """
    value = os.environ.get(key)
    if not value:
        raise ValueError(f'Required environment variable not set: {key}')
    return value


def get_optional_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get optional environment variable with default
    
    Args:
        key: Environment variable name
        default: Default value if not set
    
    Returns:
        Environment variable value or default
    """
    return os.environ.get(key, default)