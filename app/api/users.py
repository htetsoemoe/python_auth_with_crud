from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.auth.dependencies import get_current_user
from app.schemas.user_schema import UserOut, UserUpdate
from app.services.user_service import UserService
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Protected routes
# Get routes
@router.get("/me", response_model=UserOut)
async def get_my_account(current_user: dict = Depends(get_current_user)) -> UserOut:
    """Get current user's account information"""
    user_data = await UserService.get_user_by_username(current_user["username"])
    return UserOut(**user_data)

@router.get("/", response_model=List[UserOut])
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of users to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get all users with pagination"""
    users = await UserService.get_users_with_pagination(skip, limit)
    return [UserOut(**user) for user in users] # Using list comprehension

@router.get("/count", response_model=Dict[str, int])
async def get_users_count(current_user: dict = Depends(get_current_user)):
    """Get total count of users"""
    return await UserService.get_users_count()

@router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id(
    user_id: str,
    current_user: dict = Depends(get_current_user)
) -> UserOut:
    """Get user by ID"""
    user_data = await UserService.get_user_by_id(user_id)
    return UserOut(**user_data)

@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a user"""
    user_data = await UserService.update_user_by_id(user_id, user_update)
    return UserOut(**user_data)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Deactivate user by id"""
    await UserService.deactivate_user_by_id(user_id)