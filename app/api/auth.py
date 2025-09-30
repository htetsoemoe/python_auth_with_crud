from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.database import db_manager
from app.auth.password import verify_password, hash_password
from app.auth.jwt_handler import create_token
from app.schemas.user_schema import UserRegister, UserOut
from app.models.user_model import UserModel
from app.config import settings
from pymongo.errors import DuplicateKeyError
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegister):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db_manager.db.users.find_one({"username": user.username})
        if existing_user:
            logger.warning(f"Registration attempt with existing username: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Hash the password
        hashed_password = hash_password(user.password)

        # Create user document
        user_doc = UserModel.create_user_document(
            username=user.username,
            hashed_password=hashed_password
        )

        # Insert user into database
        result = db_manager.db.users.insert_one(user_doc)

        # Retrieve created user
        created_user = db_manager.db.users.find_one({"_id": result.inserted_id})

        logger.info(f"User registered successfully: {user.username}")
        return UserOut(**UserModel.user_helper(created_user)) # ** is Unpacked operator
    
    except DuplicateKeyError:
        logger.warning(f"Duplicate key error for username: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    except Exception as e:
        logger.error(f"Error registering user: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

