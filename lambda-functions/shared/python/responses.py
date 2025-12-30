"""
Standard HTTP responses for Lambda functions
"""
import json
from typing import Dict, Any, Optional

def success_responses(
        data: Dict[str, Any],
        status_code: int = 200
) -> Dict[str, Any]:
    """
    Standard success response
    
    Args:
        data: Response data to return
        status_code: HTTP status code (default 200)
    
    Returns:
        Formatted Lambda response
    """

    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }

def error_response(
        error_message: str,
        status_code: int = 500,
        details: Optional[str] = None
) -> Dict[str, Any]:
    """
    Standard error response
    
    Args:
        error_message: User-facing error message
        status_code: HTTP status code
        details: Optional technical details (for logging)
    
    Returns:
        Formatted Lambda error response
    """

    body = {'error': error_message}

    if details:
        body['details'] = details

    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }

def validation_error(error_message: str) -> Dict[str, Any]:
    """Bad request (400) response"""
    return error_response(error_message, 400)


def unauthorized_error(error_message: str = 'Unauthorized') -> Dict[str, Any]:
    """Unauthorized (401) response"""
    return error_response(error_message, 401)


def forbidden_error(error_message: str = 'Forbidden') -> Dict[str, Any]:
    """Forbidden (403) response"""
    return error_response(error_message, 403)


def not_found_error(error_message: str = 'Not found') -> Dict[str, Any]:
    """Not found (404) response"""
    return error_response(error_message, 404)


def conflict_error(error_message: str) -> Dict[str, Any]:
    """Conflict (409) response"""
    return error_response(error_message, 409)


def gone_error(error_message: str) -> Dict[str, Any]:
    """Gone (410) response - for expired resources"""
    return error_response(error_message, 410)