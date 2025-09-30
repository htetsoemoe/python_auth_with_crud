from typing import Dict, Any
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserModel:
    """User model with enhanced functionality"""

    @staticmethod
    def user_helper(user: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB user document to API response"""
        if not user:
            return {}
        
        return {
            "id": str(user.get("_id", "")),
            "username": user.get("username", ""),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at"),
            "is_active": user.get("is_active", True),
            "last_login": user.get("last_login")
        }
    
    @staticmethod
    def create_user_document(username: str, hashed_password: str) -> Dict[str, Any]:
        """Create a new user document for MongoDB insertion"""
        now = datetime.utcnow()
        return {
            "username": username.strip(),
            "password": hashed_password,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "last_login": None,
            "login_count": 0
        }
    
    @staticmethod
    def update_last_login(user_id: str) -> Dict[str, Any]:
        """Create update document for last login"""
        return {
            "$set": {
                "last_login": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            "$inc": {
                "login_count": 1
            }
        }
    
    @staticmethod
    def validate_object_id(user_id: str) -> bool:
        """Validate if string is a valid ObjectId"""
        try:
            ObjectId(user_id)
            return True
        except Exception:
            return False
        
# Backward compatibility
# Convert MongoDB document to API response
def user_helper(user: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy function for backward compatibility"""
    return UserModel.user_helper(user)
        
    