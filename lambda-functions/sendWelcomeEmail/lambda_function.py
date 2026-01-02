from typing import Dict, Any
import boto3
from mypy_boto3_ses import SESClient

from shared.python.responses import success_response, error_response, validation_error
from shared.python.validation import parse_request_body
from shared.python.env_config import get_optional_env

ses: SESClient = boto3.client('ses')  # type: ignore

SENDER_EMAIL = get_optional_env('SENDER_EMAIL')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Sends welcome email after user verifies their account.
    Called by: verifyEmail Lambda after successful verification
    """
    print('Event:', event)
    
    if not SENDER_EMAIL:
        print('ERROR: SENDER_EMAIL not configured')
        return error_response('Email service not configured')
    
    body = parse_request_body(event)
    if not body:
        return validation_error('Invalid request body')
    
    email: str | None = body.get('email')
    username: str | None = body.get('username')
    
    if not email or not username:
        return validation_error('Email and username required')
    
    try:
        email_body = f"""
Hello {username},

Welcome to Hodler!

Your email has been successfully verified and your account is now active.

Get started:
- Practice trading without risking real money
- Compete on the global leaderboard
- Build your trading skills and confidence

Ready to start trading? Log in at https://hodlersim.app

Happy trading!
- The Hodler Team
        """
        
        response = ses.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {
                    'Data': 'Welcome to Hodler!',
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
            'message': 'Welcome email sent',
            'messageId': response['MessageId']
        })
        
    except Exception as e:
        print(f'SES error: {str(e)}')
        return error_response('Failed to send welcome email')