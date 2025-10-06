from typing import List, Dict, Any, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError
from datetime import datetime
import logging
from app.database import db_manager
from app.models.user_model import UserModel
from app.schemas.user_schema import UserOut, UserUpdate
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class UserService:
    """Service layer for user-related business logic"""

    @staticmethod
    async def get_user_by_username(username: str) -> Dict[str, Any]:
        """Get user by username"""
        try:
            user = db_manager.db.users.find_one({"username": username})
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return UserModel.user_helper(user)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving user by username: {username}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user information"
            )