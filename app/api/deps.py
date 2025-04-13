from typing import Generator, Optional, Tuple
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
import time
import logging

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.token import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
logger = logging.getLogger(__name__)

# Consider implementing token blacklisting with Redis if needed
# from app.core.redis import redis_client
# def is_token_blacklisted(jti: str) -> bool:
#     """Check if a token has been blacklisted"""
#     return redis_client.exists(f"blacklist:{jti}")

def decode_token(token: str) -> Tuple[TokenPayload, str]:
    """
    Decode and validate JWT token
    
    Returns a tuple of (token_data, raw_token)
    """
    try:
        # Explicitly specify algorithms to prevent algorithm confusion attacks
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        # Check if token is the right type (access vs refresh)
        if payload.get('type') != 'access':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return token_data, payload
        
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValidationError as e:
        logger.warning(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
        

def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme),
    request: Request = None
) -> User:
    """
    Get the current authenticated user.
    
    Validates JWT token and returns the corresponding user.
    """
    token_data, raw_payload = decode_token(token)
    
    # Check token expiration explicitly
    if token_data.exp < time.time():
        client_info = f" from IP: {request.client.host}" if request else ""
        logger.warning(f"Expired token used (sub: {token_data.sub}){client_info}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # If using token blacklisting, check if token is blacklisted
    # jti = raw_payload.get("jti")
    # if jti and is_token_blacklisted(jti):
    #     client_info = f" from IP: {request.client.host}" if request else ""
    #     logger.warning(f"Blacklisted token used (sub: {token_data.sub}){client_info}")
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Token has been revoked",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    
    # Get user from database
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        client_info = f" from IP: {request.client.host}" if request else ""
        logger.warning(f"Auth attempt with valid token but non-existent user ID: {token_data.sub}{client_info}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is active
    if not user.is_active:
        client_info = f" from IP: {request.client.host}" if request else ""
        logger.warning(f"Auth attempt by inactive user: {user.email} (ID: {user.id}){client_info}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
        
    return user


def get_current_active_admin(
    current_user: User = Depends(get_current_user), 
    request: Request = None
) -> User:
    """
    Get current user and verify they are an admin.
    """
    if not current_user.is_admin:
        client_info = f" from IP: {request.client.host}" if request else ""
        logger.warning(f"Admin access attempt by non-admin user: {current_user.email} (ID: {current_user.id}){client_info}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# Add this utility function for query protection against DoS
def limit_query_factory(max_limit: int = 100, default_limit: int = 20):
    """
    Factory function to create a dependency that limits query parameters
    to prevent DoS attacks through large queries
    """
    def limit_query(skip: int = 0, limit: int = default_limit):
        """Limits query parameters to reasonable ranges"""
        return max(0, skip), min(max_limit, limit)
    return limit_query
