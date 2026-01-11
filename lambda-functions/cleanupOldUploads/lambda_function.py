import json
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import boto3
from mypy_boto3_s3 import S3Client

from shared.python.responses import success_response
from shared.python.env_config import get_optional_env

s3: S3Client = boto3.client('s3')  # type: ignore

UPLOAD_BUCKET = get_optional_env('UPLOAD_BUCKET')
DAYS_TO_KEEP = 7

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Deletes old uploads from raw bucket (cleanup job).
    Triggered daily by EventBridge cron.
    """
    print('Event:', json.dumps(event))
    
    if not UPLOAD_BUCKET:
        print('ERROR: UPLOAD_BUCKET not configured')
        return success_response({'message': 'Bucket not configured'})
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=DAYS_TO_KEEP)
    print(f'Deleting files older than: {cutoff_date.isoformat()}')
    
    deleted_count = 0
    error_count = 0
    
    try:
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=UPLOAD_BUCKET, Prefix='uploads/')
        
        for page in pages:
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                key: str | None = obj.get('Key')
                last_modified = obj.get('LastModified')

                if not key or not last_modified:
                    continue
                
                # Check if file is old enough to delete
                if last_modified < cutoff_date:
                    try:
                        s3.delete_object(Bucket=UPLOAD_BUCKET, Key=key)
                        print(f'Deleted: {key} (age: {(datetime.now(timezone.utc) - last_modified).days} days)')
                        deleted_count += 1
                    except Exception as e:
                        print(f'Error deleting {key}: {str(e)}')
                        error_count += 1
        
        return success_response({
            'message': f'Cleanup complete: {deleted_count} deleted, {error_count} errors',
            'deleted': deleted_count,
            'errors': error_count
        })
        
    except Exception as e:
        print(f'Cleanup error: {str(e)}')
        return success_response({
            'message': 'Cleanup failed',
            'error': str(e)
        })
