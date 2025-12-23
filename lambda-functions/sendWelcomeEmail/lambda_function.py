import json
import os
from typing import Dict, Any
import boto3
from mypy_boto3_sns import SNSClient
from mypy_boto3_sns.type_defs import PublishResponseTypeDef

sns: SNSClient = boto3.client('sns') # type: ignore[misc]
TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    print('Event: ', json.dumps(event))

    if not TOPIC_ARN:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'SNS_TOPIC_ARN not configured'})
        }
    
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        username = body.get('username')
        
        if not email or not username:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Email and username required'})
            }
    except Exception as e:
        print(f'Parse error: {str(e)}')
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request body'})
        }
    
    try:
        message = f"""
Welcome to Hodler, {username}!

Thank you for joining our crypto trading simulator community.

Get started:
- Practice trading without risking real money
- Compete on the leaderboard
- Build your trading skills

Happy Trading!
- The Hodler Team
"""
        response: PublishResponseTypeDef = sns.publish(
            TopicArn=TOPIC_ARN,
            Subject=f'Welcome to Hodler, {username}!',
            Message=message
        )
        
        print(f'SNS publish response: {response}')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Welcome email sent',
                'messageId': response['MessageId']
            })
        }
        
    except Exception as e:
        print(f'SNS error: {str(e)}')
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to send email'})
        }