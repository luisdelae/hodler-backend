import json
from typing import Dict, Any
from datetime import datetime, timezone
from mypy_boto3_s3 import S3Client
import boto3

from shared.python.responses import (
    success_response,
    error_response,
    unauthorized_error,
    validation_error
)
from shared.python.env_config import get_optional_env

s3: S3Client = boto3.client('s3') # type: ignore

UPLOAD_BUCKET = get_optional_env('UPLOAD_BUCKET')
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'gif', 'png', 'webp']
MAX_FILE_SIZE = 10 * 1024 * 1024

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Generates pre-signed URL for secure S3 upload.
    User uploads directly to S3 using this temporary URL.
    """
    print('Event:', event)

    if not UPLOAD_BUCKET:
        print('ERROR: UPLOAD_BUCKET not configured')
        return error_response('Upload service not configured')
    
    # Add token check here after testing S3 #

    try:
        body = json.loads(event.get('body', '{}'))
        filename: str = body.get('filename', '')
        content_type: str = body.get('contentType', '')
        user_id: str = body.get('userId', '')

        if not filename or not content_type or not user_id:
            return validation_error('filename, contentType, and userId required')
        
    except Exception as e:
        print(f'Parse error: {str(e)}')
        return validation_error('Invalid request body')
    
    extension = filename.lower().split('.')[-1]
    if extension not in ALLOWED_EXTENSIONS:
        return validation_error(
            f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        )
    
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    s3_key = f'uploads/{user_id}/{timestamp}.{extension}'

    try:
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': UPLOAD_BUCKET,
                'Key': s3_key,
                'ContentType': content_type,
                'ContentLength': MAX_FILE_SIZE
            },
            ExpiresIn=300
        )
        print(f'Generated pre-signed URL for: {s3_key}')
        
        return success_response({
            'uploadUrl': presigned_url,
            's3Key': s3_key,
            'expiresIn': 300
        })
        
    except Exception as e:
        print(f'S3 error: {str(e)}')
        return error_response('Failed to generate upload URL')
