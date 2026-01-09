import json
from io import BytesIO
from typing import Dict, Any
import boto3
from PIL import Image
from mypy_boto3_s3 import S3Client
from mypy_boto3_sqs import SQSClient

from shared.python.responses import success_response, error_response
from shared.python.env_config import get_optional_env

s3: S3Client = boto3.client('s3')  # type: ignore
sqs: SQSClient = boto3.client('sqs')  # type: ignore

UPLOAD_BUCKET = get_optional_env('UPLOAD_BUCKET')
PROCESSED_BUCKET = get_optional_env('PROCESSED_BUCKET')
QUEUE_URL = get_optional_env('QUEUE_URL')

MAX_SIZE = (512, 512)
QUALITY = 85


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Processes images from SQS queue triggered by S3 uploads.
    Resizes, optimizes, and saves to processed bucket.
    """
    print('Event:', json.dumps(event))
    
    if not UPLOAD_BUCKET or not PROCESSED_BUCKET:
        print('ERROR: Buckets not configured')
        return error_response('Image processing not configured')
    
    records = event.get('Records', [])
    
    if not records:
        print('No records to process')
        return success_response({'message': 'No records'})
    
    processed_count = 0
    failed_count = 0
    
    for record in records:
        try:
            message_body = json.loads(record['body'])
            
            s3_records = message_body.get('Records', [])
            
            for s3_record in s3_records:
                s3_info = s3_record['s3']
                bucket_name = s3_info['bucket']['name']
                object_key = s3_info['object']['key']
                
                print(f'Processing: s3://{bucket_name}/{object_key}')
                
                process_image(bucket_name, object_key)
                
                processed_count += 1
                
        except Exception as e:
            print(f'Error processing record: {str(e)}')
            failed_count += 1
    
    return success_response({
        'message': f'Processed {processed_count} images, {failed_count} failed'
    })


def process_image(source_bucket: str, source_key: str) -> None:
    """
    Downloads, processes, and uploads an image.
    
    Steps:
    1. Download from S3 raw bucket
    2. Resize to max dimensions (maintaining aspect ratio)
    3. Optimize quality
    4. Convert to WebP (smaller file size)
    5. Upload to processed bucket
    """
    print(f'Downloading: {source_key}')
    
    response = s3.get_object(Bucket=source_bucket, Key=source_key)
    image_data = response['Body'].read()
    
    img = Image.open(BytesIO(image_data))
    
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
    
    print(f'Resized to: {img.size}')
    
    buffer = BytesIO()
    img.save(buffer, format='WebP', quality=QUALITY, method=6)
    buffer.seek(0)
    
    # Generate destination key (replace extension with .webp)
    # uploads/user-123/20260108-235731.png → profiles/user-123.webp
    user_id = source_key.split('/')[1]  # Extract user-123 from path
    dest_key = f'profiles/{user_id}.webp'
    
    print(f'Uploading to: {dest_key}')
    
    s3.put_object(
        Bucket=PROCESSED_BUCKET, # type: ignore
        Key=dest_key,
        Body=buffer.getvalue(),
        ContentType='image/webp',
        CacheControl='max-age=31536000',  # Cache for 1 year
    )
    
    print(f'Successfully processed: {source_key} → {dest_key}')
