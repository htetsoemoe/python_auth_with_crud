from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.auth.dependencies import get_current_user
from app.schemas.user_schema import UserOut, UserUpdate
from app.services.user_service import UserService
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/me", response_model=UserOut)
async def get_my_account(current_user: dict = Depends(get_current_user)) -> UserOut:
    """Get current user's account information"""
    user_data = await UserService.get_user_by_username(current_user["username"])
    return UserOut(**user_data)