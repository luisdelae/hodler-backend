from datetime import datetime, timezone
from typing import Dict, Any, cast
import boto3
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from mypy_boto3_lambda import LambdaClient
import json

from shared.python.responses import (
    success_response,
    error_response,
    not_found_error,
    gone_error,
    validation_error
)
from shared.python.env_config import get_optional_env

dynamodb: DynamoDBServiceResource = boto3.resource('dynamodb')  # type: ignore
lambda_client: LambdaClient = boto3.client('lambda')  # type: ignore

USERS_TABLE = get_optional_env('USERS_TABLE', 'Users')
VERIFICATION_TOKENS_TABLE = get_optional_env('VERIFICATION_TOKENS_TABLE', 'VerificationTokens')
WELCOME_EMAIL_LAMBDA = get_optional_env('WELCOME_EMAIL_LAMBDA_ARN')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Verifies email token and marks user as verified.
    Called when user clicks verification link from email.
    Idempotent: Safe to call multiple times with same token.
    """
    print('Event:', event)
    
    query_params = event.get('queryStringParameters') or {}  # type: ignore
    token: str | None = query_params.get('token')  # type: ignore
    
    if not token:
        return validation_error('Verification token required')
    
    tokens_table: Table = dynamodb.Table(VERIFICATION_TOKENS_TABLE)
    users_table: Table = dynamodb.Table(USERS_TABLE)
    
    user: Dict[str, Any] = {}
    
    try:
        response = tokens_table.get_item(Key={'token': token})  # type: ignore[arg-type]
        
        if 'Item' not in response:
            print(f'Token not found: {token}')
            
            # Token not found - check if this was already verified
            # (Idempotent behavior: don't fail if already successful)
            # We can't reliably determine this without the token, so return generic error
            return not_found_error('Invalid or expired verification token')
        
        token_data = response['Item']
        user_id = cast(str, token_data['userId'])
        email = cast(str, token_data['email'])
        expires_at = cast(str, token_data['expiresAt'])
        
        print(f'Token found for user: {user_id}')
        
    except Exception as e:
        print(f'DynamoDB get error: {str(e)}')
        return error_response('Failed to verify token')
    
    try:
        expires_at_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        if now > expires_at_dt:
            print(f'Token expired: {token}')
            tokens_table.delete_item(Key={'token': token})  # type: ignore[arg-type]
            return gone_error('Verification token expired. Please request a new one.')
            
    except Exception as e:
        print(f'Date parsing error: {str(e)}')
    
    try:
        user_response = users_table.get_item(Key={'userId': user_id})  # type: ignore[arg-type]
        user = user_response.get('Item', {})
        
        if user.get('verified'):
            print(f'User already verified (idempotent): {user_id}')
            
            try:
                tokens_table.delete_item(Key={'token': token})  # type: ignore[arg-type]
                print(f'Token deleted (cleanup): {token}')
            except Exception as e:
                print(f'Token cleanup error: {str(e)}')
            
            return success_response({
                'message': 'Email already verified',
                'userId': user_id
            })
            
    except Exception as e:
        print(f'User lookup error: {str(e)}')
    
    try:
        users_table.update_item(
            Key={'userId': user_id},  # type: ignore[arg-type]
            UpdateExpression='SET verified = :verified, updatedAt = :updatedAt',
            ExpressionAttributeValues={
                ':verified': True,
                ':updatedAt': datetime.now(timezone.utc).isoformat()
            }
        )
        print(f'User verified: {user_id}')
        
    except Exception as e:
        print(f'DynamoDB update error: {str(e)}')
        return error_response('Failed to verify user')
    
    try:
        tokens_table.delete_item(Key={'token': token})  # type: ignore[arg-type]
        print(f'Token deleted: {token}')
    except Exception as e:
        print(f'Token deletion error: {str(e)}')
    
    if WELCOME_EMAIL_LAMBDA:
        try:
            username = user.get('username', 'User')  # Already fetched above
            
            lambda_client.invoke(
                FunctionName=WELCOME_EMAIL_LAMBDA,
                InvocationType='Event',
                Payload=json.dumps({
                    'body': json.dumps({
                        'email': email,
                        'username': username
                    })
                })
            )
            print(f'Welcome email Lambda invoked for: {email}')
        except Exception as e:
            print(f'Welcome email error: {str(e)}')
    
    return success_response({
        'message': 'Email verified successfully',
        'userId': user_id
    })
