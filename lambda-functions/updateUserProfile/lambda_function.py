from datetime import datetime, timezone
from typing import Dict, Any
import boto3
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from botocore.exceptions import ClientError
from pydantic import ValidationError
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table

from shared.python.responses import (
    success_response,
    error_response,
    unauthorized_error,
    forbidden_error,
    validation_error
)
from shared.python.validation import parse_request_body
from shared.python.env_config import get_optional_env

from models import (
    UpdateProfileRequest,
    User,
    TokenPayload,
)

dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb") # type: ignore
table: Table = dynamodb.Table("Users")

JWT_SECRET = get_optional_env("JWT_SECRET", "dev-secret-change-in-production")


def extract_token(event: Dict[str, Any]) -> str:
    """Extract JWT token from Authorization header"""
    auth_header = event.get("headers", {}).get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise ValueError("Missing or invalid Authorization header")
    
    return auth_header.replace("Bearer ", "")


def verify_token(token: str) -> TokenPayload:
    """Verify JWT token and return decoded payload"""
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"]) # type: ignore
        return TokenPayload(**decoded)
    except ExpiredSignatureError:
        raise ValueError("Token expired")
    except InvalidTokenError:
        raise ValueError("Invalid token")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    print("Event:", event)
    
    try:
        token = extract_token(event)
        token_payload = verify_token(token)
    except ValueError as e:
        return unauthorized_error(str(e))
    except Exception as e:
        print(f"Auth error: {str(e)}")
        return unauthorized_error("Authentication failed")
    
    path_params = event.get("pathParameters", {})
    user_id = path_params.get("id")
    
    if not user_id:
        return validation_error("userId is required")
    
    if token_payload.userId != user_id:
        return forbidden_error("Not authorized to update this profile")
    
    body = parse_request_body(event)
    if not body:
        return validation_error("Invalid JSON")
    
    try:
        update_request = UpdateProfileRequest(**body)
    except ValidationError as e:
        return error_response("Validation failed", 400, str(e.errors()))
    
    # Update user profile in DynamoDB
    try:
        response = table.update_item(
            Key={"userId": user_id},
            UpdateExpression="SET username = :username, updatedAt = :updatedAt",
            ExpressionAttributeValues={
                ":username": update_request.username,
                ":updatedAt": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        
        updated_user_data = response.get("Attributes", {})
        updated_user = User(**updated_user_data)  # type: ignore[arg-type]
        
        user_dict = updated_user.model_dump(exclude={"passwordHash"})
        user_response = User(**user_dict)
        
        return success_response({
            "message": "Profile updated successfully",
            "user": user_response.model_dump()
        })
        
    except ClientError as e:
        print(f"DynamoDB error: {str(e)}")
        return error_response("Failed to update profile")
    except ValidationError as e:
        print(f"User model validation error: {str(e)}")
        return error_response("Invalid user data from database")
    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response("Internal server error")