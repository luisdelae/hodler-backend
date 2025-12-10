import json
import os
from datetime import datetime, timezone
from typing import Dict, Any
import boto3
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from botocore.exceptions import ClientError
from pydantic import ValidationError
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table

from models import (
    UpdateProfileRequest,
    User,
    TokenPayload,
    ErrorResponse,
    SuccessResponse,
)

dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
table: Table = dynamodb.Table("Users")

JWT_SECRET: str = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")


def create_response(status_code: int, body: Any) -> Dict[str, Any]:
    """Helper to create consistent API Gateway responses"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body.dict() if (hasattr(body, "model_dump")) else body),
    }


def extract_token(event: Dict[str, Any]) -> str:
    """Extract JWT token from Authorization header"""
    auth_header = event.get("headers", {}).get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise ValueError("Missing or invalid Authorization header")

    return auth_header.replace("Bearer ", "")


def verify_token(token: str) -> TokenPayload:
    """Verify JWT token and return decoded payload"""
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return TokenPayload(**decoded)
    except ExpiredSignatureError:
        raise ValueError("Token expired")
    except InvalidTokenError:
        raise ValueError("Invalid token")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    print("Event: ", json.dumps(event))

    try:
        token = extract_token(event)
        token_payload = verify_token(token)
    except ValueError as e:
        return create_response(401, ErrorResponse(error=str(e)))
    except Exception as e:
        print(f"Auth error: {str(e)}")
        return create_response(401, ErrorResponse(error="Authentication failed"))

    path_params = event.get("pathParameters", {})
    user_id = path_params.get("id")

    if not user_id:
        return create_response(400, ErrorResponse(error="userId is required"))

    if token_payload.userId != user_id:
        return create_response(
            403, ErrorResponse(error="Not authorized to update this profile")
        )

    try:
        body_data = json.loads(event.get("body", {}))
        update_request = UpdateProfileRequest(**body_data)
    except json.JSONDecodeError:
        return create_response(400, ErrorResponse(error="Invalid JSON"))
    except ValidationError as e:
        return create_response(
            400, {"error": "Validation failed", "details": e.errors()}
        )

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
        updated_user = User(**updated_user_data) # type: ignore[arg-type]

        user_dict = updated_user.model_dump(exclude={"passwordHash"})
        user_response = User(**user_dict)

        return create_response(
            200,
            SuccessResponse(message="Profile updated successfully", user=user_response),
        )

    except ClientError as e:
        print(f"DynamoDB error: {str(e)}")
        return create_response(500, ErrorResponse(error="Failed to update profile"))
    except ValidationError as e:
        print(f"User model validation error: {str(e)}")
        return create_response(
            500, ErrorResponse(error="Invalid user data from database")
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(500, ErrorResponse(error="Internal server error"))
