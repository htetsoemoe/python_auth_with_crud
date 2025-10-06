from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.auth.jwt_handler import decode_token
from typing import Dict, Any
from app.database import db_manager
import logging

logger = logging.getLogger(__name__)

"""
    Purpose: To EXTRACT and VALIDATE an access token from incoming requests to protected endpoints.
    When you use it: In any protected route to get the token from the Authorization header and 
    ensure it's present and correctly formatted.

    How it works:
    It's a class you initialize with the URL of your token endpoint (e.g., "/token"). 
    This is mostly for OpenAPI documentation so the interactive docs (Swagger UI) know where to get a token.

    When used as a dependency, it automatically:
    Looks for an Authorization header.
    Checks if it's in the correct format: Bearer <token>.
    If the header is missing or malformed, it automatically raises a 401 Unauthorized error.
    If successful, it returns the token string (as a str). It does not validate the token's signature or expiry—that's your job next.

    Analogy: It's like the scanner inside the club that checks your wristband (access token) to make sure 
    you have one before letting you access the VIP area (protected endpoint).

    Code Example (Protecting Routes - Token Consumer):
"""

oauth2_schema = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    description="JWT token for authentication"
)

async def get_current_user(token: str = Depends(oauth2_schema)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        # Decode and validate token
        payload = decode_token(token)
        logger.info(f"{payload}") # app.auth.dependencies - INFO - {'sub': 'Alice', 'exp': 1759578943, 'iat': 1759575343, 'type': 'access_token'}

        if payload is None:
            logger.warning("Invalid or expired token provided")
            raise credentials_exception
        
        # Extract username from token
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token missing subject (username)")
            raise credentials_exception
        
        # Find user in database
        user = db_manager.db.users.find_one(
            {"username": username},
            {"password": 0} # Exclude password from query result
        )

        if not user:
            logger.warning(f"User not found in database: {username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            logger.warning(f"Inactive user attempt access: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        return {
            "username": user["username"],
            "user_id": str(user["_id"]),
            "is_active": user.get("is_active", True)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating user token: {e}")
        raise credentials_exception
    

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user (additional validation layer)"""
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


# Optional dependency for endpoints that don't require authentication
async def get_current_user_optional(token: str = Depends(oauth2_schema)) -> Dict[str, Any] | None:
    """Get current user if token is provided, otherwise return None"""
    try:
        return await get_current_user(token)
    except HTTPException:
        return None