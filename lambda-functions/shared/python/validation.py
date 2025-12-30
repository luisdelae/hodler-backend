"""
Common validation utilities
"""
import json
import re
from typing import Dict, Any, Optional


def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid email format
    """
    if not email:
        return False
    
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return bool(re.match(email_regex, email))


def validate_password(password: str) -> Optional[str]:
    """
    Validate password strength
    
    Args:
        password: Password to validate
    
    Returns:
        Error message if invalid, None if valid
    """
    if not password:
        return 'Password is required'
    
    if len(password) < 8:
        return 'Password must be at least 8 characters long'
    
    if not re.search(r'[A-Z]', password):
        return 'Password must contain at least one uppercase letter'
    
    if not re.search(r'[a-z]', password):
        return 'Password must contain at least one lowercase letter'
    
    if not re.search(r'\d', password):
        return 'Password must contain at least one number'
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return 'Password must contain at least one special character'
    
    return None


def parse_request_body(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON body from Lambda event
    
    Args:
        event: Lambda event object
    
    Returns:
        Parsed body dict, or None if parsing fails
    """
    try:
        body: Any = event.get('body', '{}')
        parsed: Dict[str, Any] = json.loads(body) if isinstance(body, str) else body
        return parsed
    except Exception:
        return None