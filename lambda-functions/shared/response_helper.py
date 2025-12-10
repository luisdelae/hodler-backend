import json
from typing import Any, Dict, Optional

def api_response(
    status_code: int,
    body: Any,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create standardized API Gateway response"""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }
    
    # Merge custom headers if provided
    if headers:
        default_headers.update(headers)
    
    # Serialize body if it's a Pydantic model
    if hasattr(body, 'dict'):
        body = body.dict(exclude_none=True)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body)
    }

# Convenience functions
def success_response(body: Any, status_code: int = 200) -> Dict[str, Any]:
    return api_response(status_code, body)

def error_response(message: str, status_code: int = 400) -> Dict[str, Any]:
    return api_response(status_code, {'error': message})