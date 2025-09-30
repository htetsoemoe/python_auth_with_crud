from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re

class UserRegister(BaseModel): 
    """User registration schema with validation"""
    username: str = Field(
        ...,    # Required field
        min_length=3,
        max_length=50,
        description="Username must be between 3 and 50 characters"
    )
    password: str = Field(
        ...,    # Required field
        min_length=8,
        max_length=20,
        description="Password must be at least 8 characters"
    )

    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        
        # Check for valid characters (alphanumeric and underscore)
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Username can only contain letters, numbers, and underscores")

        return v.strip()
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password length"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        return v

    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePass_123"
            }
        }

class UserOut(BaseModel):
    """User output schema for API responses"""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    is_active: bool = Field(True, description="Whether the user account is active")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "username": "john_doe",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "is_active": True,
                "last_login": "2024-01-01T12:00:00Z"
            }
        }        