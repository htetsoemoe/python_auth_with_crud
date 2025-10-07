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
        
    @staticmethod
    async def get_user_by_id(user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        try:
            # Validate Object
            if not UserModel.validate_object_id(user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user ID format"
                )
            
            # Find user by ID
            user = db_manager.db.users.find_one(
                {"_id": ObjectId(user_id)},
                {"password": 0}, # Exclude password field
            )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Convert ObjectId to string
            user["id"] = str(user["_id"])
            # UserOut Pydantic model expects a field named id, but your MongoDB document has _id instead.
            # str(user["_id"]) = MongoDB ObjectId (change from ObjectId to string)
            # user["id"] = UserOut Pydantic model field

            logger.info(f"Retrieved user: {user_id}")
            return user
        
        except HTTPException:
            raise
        except PyMongoError as e:
            logger.error(f"Database error retrieving user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occured"
            )
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
    @staticmethod
    async def get_users_with_pagination(skip: int = 0, limit: int = 10):
        """Get users with pagination"""
        try:
            users_cursor = db_manager.db.users.find(
                {},
                {"password": 0}, # Exclude password
            ).skip(skip).limit(limit)

            users = list(users_cursor) # Change to iterable type

            # Convert ObjectId to string for each user
            for user in users:
                user["id"] = str(user["_id"]) 
            # UserOut Pydantic model expects a field named id, but your MongoDB document has _id instead.
            # str(user["_id"]) = MongoDB ObjectId (change from ObjectId to string)
            # user["id"] = UserOut Pydantic model field
            
            logger.info(f"Retrieved {len(users)} users (skip={skip}, limit={limit})")
            return users
        
        except PyMongoError as e:
            logger.error(f"Database error retrieving users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            logger.error(f"Error retrieving users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
    @staticmethod
    async def get_users_count() -> Dict[str, int]:
        """Get total count of users"""
        try:
            total_count = db_manager.db.users.count_documents({})
            active_count = db_manager.db.users.count_documents({"is_active": True})

            logger.info(f"User count request - Total: {total_count}, Active: {active_count}")
            return {
                "total_users": total_count,
                "active_users": active_count
            }
        except PyMongoError as e:
            logger.error(f"Database error counting users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
    @staticmethod
    async def update_user_by_id(user_id: str, user_update: UserUpdate) -> Dict[str, Any]:
        """Update user by ID (admin function)"""
        try:
            # Validate ObjectId
            if not UserModel.validate_object_id(user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user ID format"
                )
            
            # Check if user exists
            existing_user = db_manager.db.users.find_one({"_id": ObjectId(user_id)})
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Prepare user update data
            update_data = {}
            if user_update.username is not None:
                update_data["username"] = user_update.username
            if user_update.is_active is not None:
                update_data["is_active"] = user_update.is_active

            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow()

            # Update user 
            result = db_manager.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )

            # Get updated user with user_id
            updated_user = db_manager.db.users.find_one(
                {"_id": ObjectId(user_id)},
                {"password": 0}
            )

            # Convert ObjectId to string
            updated_user["id"] = str(updated_user["_id"])
            logger.info(f"User updated: {user_id}")
            return updated_user
        
        except HTTPException:
            raise
        except PyMongoError as e:
            logger.error(f"Database error updating user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
    @staticmethod
    async def deactivate_user_by_id(user_id: str) -> None:
        """Deactivate user by ID"""
        try:
            # Validate ObjectId
            if not UserModel.validate_object_id(user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user ID"
                )
            
            # Check if user exists
            existing_user = db_manager.db.users.find_one({"_id": ObjectId(user_id)})
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Deactivate User by ID
            result = db_manager.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already deactivated"
                )
            
            logger.info(f"User deactivated: {user_id}")
        except HTTPException:
            raise
        except PyMongoError as e:
            logger.error(f"Database error deleting user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )