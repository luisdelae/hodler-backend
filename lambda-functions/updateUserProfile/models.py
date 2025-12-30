from typing import Optional
from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    """Request body for updating user profile"""

    username: str = Field(..., min_length=1, max_length=50)

    class Config:
        str_strip_whitespace = True


class User(BaseModel):
    """User model matching DynamoDB schema"""

    userId: str
    email: str
    username: str
    createdAt: str
    updatedAt: str
    passwordHash: Optional[str] = None

    class Config:
        extra = "ignore"


class TokenPayload(BaseModel):
    """JWT token payload"""

    userId: str
    email: str
    exp: Optional[int] = None
    