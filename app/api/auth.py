from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.database import db_manager
from app.auth.password import verify_password, hash_password
from app.auth.jwt_handler import create_token
from app.schemas.user_schema import UserRegister, UserOut, UserLogin, TokenResponse
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

"""
    OAuth2PasswordRequestForm

    Purpose: To RECEIVE login credentials (username and password) from a client.
    When you use it: In your login endpoint to parse the incoming data from a form submission.

    How it works:
    It's a dependency (a class you use with Depends()) that tells FastAPI to parse the incoming request body as form data.
    It expects the standard OAuth2 grant type fields: username and password (and optionally scope and grant_type).
    It is used once, when the user initially logs in, to exchange their credentials for an access token.

    Analogy: It's like the bouncer at the door who checks your ID (username and password) to give you a wristband (access token).

    Code Example (The Login Route - Token Producer):
"""
@router.post("/login", response_model=TokenResponse)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:

    """Login user with OAuth2 password form"""
    try:
        # Find user by username
        user = db_manager.db.users.find_one({"username": form_data.username})
        if not user:
            logger.warning(f"Login attempt with non-existent username: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username and password"
            )
        
        # Verify password
        if not verify_password(form_data.password, user["password"]):
            logger.warning(f"Failed login attempt for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Update last login
        update_operation = UserModel.update_last_login(user["_id"])
        db_manager.db.users.update_one({"_id": user["_id"]}, update_operation)

        # Create access token
        token = create_token({"sub": user["username"]})

        logger.info(f"User logged in successfully: {form_data.username}")
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60
        )
    
    except HTTPException:
        raise # Re-raise HTTP exceptions as they're already properly formatted
    except Exception as e:
        logger.error(f"Error during login for {form_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
"""
    JSON Input: Expects application/json data with structured payload
    Custom Schema: Uses UserLogin Pydantic model for validation
    Enhanced Security: Includes additional checks (user active status)
    Flexible Structure: Can be extended with additional fields easily
"""
@router.post("/login-json", response_model=TokenResponse)
async def login_user_json(user_login: UserLogin) -> TokenResponse:
    """Login user with JSON payload (alternative to form-base login)"""
    try:
        # Find user by username
        user = db_manager.db.users.find_one({"username": user_login.username})
        if not user:
            logger.warning(f"JSON login attempt with non-existent username: {user_login.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not verify_password(user_login.password, user["password"]):
            logger.warning(f"Invalid password attempt for user: {user_login.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            logger.warning(f"JSON login attempt by inactive user: {user_login.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Update user last login
        update_operation = UserModel.update_last_login(user["_id"])
        db_manager.db.users.update_one({"_id": user["_id"]}, update_operation)

        # Create access token
        token = create_token({"sub": user["username"]})

        logger.info(f"User logged in successfully via JSON: {user_login.username}")
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during JSON user login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )