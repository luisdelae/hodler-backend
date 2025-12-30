from datetime import datetime, timedelta, timezone
import secrets
from typing import Dict, Any
import boto3
from mypy_boto3_ses import SESClient

from shared.python.responses import success_response, error_response, validation_error
from shared.python.validation import parse_request_body
from shared.python.env_config import get_optional_env

dynamodb = boto3.resource('dynamodb')  # type: ignore
ses: SESClient = boto3.client('ses')  # type: ignore

USERS_TABLE = get_optional_env('USERS_TABLE', 'Users')
VERIFICATION_TOKENS_TABLE = get_optional_env('VERIFICATION_TOKENS_TABLE', 'VerificationTokens')
SENDER_EMAIL = get_optional_env('SENDER_EMAIL')
FRONTEND_URL = get_optional_env('FRONTEND_URL', 'http://localhost:3000')

ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://hodlersim.app',
]


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Generates verification token and sends verification email.
    Called by: registerUser (initial), resendVerification (resend)
    """
    print('Event:', event)
    
    if not SENDER_EMAIL:
        print('ERROR: SENDER_EMAIL not configured')
        return error_response('Email service not configured')
    
    body = parse_request_body(event)
    if not body:
        return validation_error('Invalid request body')
    
    user_id = body.get('userId')
    email = body.get('email')
    username = body.get('username')
    
    if not user_id or not email or not username:
        return validation_error('userId, email, and username required')
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    tokens_table = dynamodb.Table(VERIFICATION_TOKENS_TABLE)
    try:
        tokens_table.put_item(
            Item={
                'token': token,
                'userId': user_id,
                'email': email,
                'expiresAt': expires_at.isoformat(),
                'createdAt': datetime.now(timezone.utc).isoformat()
            }
        )
        print(f'Token stored for user: {user_id}')
    except Exception as e:
        print(f'DynamoDB error: {str(e)}')
        return error_response('Failed to generate verification token')
    
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    if origin and origin in ALLOWED_ORIGINS:
        frontend_url = origin
    else:
        frontend_url = FRONTEND_URL
        if origin:
            print(f'WARNING: Untrusted origin blocked: {origin}')
    
    verify_url = f'{frontend_url}/verify?token={token}'
    
    try:
        email_body = f"""
Hello {username},

Thank you for signing up for Hodler!

Please verify your email address by clicking the link below:

{verify_url}

This link will expire in 24 hours.

If you didn't create an account, you can safely ignore this email.

Happy trading!
- The Hodler Team
        """
        
        response = ses.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {
                    'Data': 'Verify your Hodler account',
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': email_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        print(f'SES MessageId: {response["MessageId"]}')
        
        return success_response({
            'message': 'Verification email sent',
            'messageId': response['MessageId']
        })
        
    except Exception as e:
        print(f'SES error: {str(e)}')
        return error_response('Failed to send verification email')