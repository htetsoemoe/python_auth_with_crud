from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
from app.config import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def create_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    """Create JWT token with proper expiration handling"""
    if expires_minutes is None:
        expires_minutes = settings.jwt_expire_minutes

    to_encode = data.copy() # Shallow copy
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc), # Issued at
        "type": "access_token"
    })

    try: 
        token = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        logger.debug(f"Token created for user: {data.get('sub', 'unknown')}")
        return token
    except Exception as e:
        logger.error(f"Error creating token: {e}")
        raise

def decode_token(token: str) -> Optional[Dict[Any, Any]]:
    """Decode JWT token with detailed error handling"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

        # Validate token type
        if payload.get("type") != "access_token":
            logger.warning("Invalid token type")
            return None
        
        return payload
        
    except ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error decoding token")
        return None