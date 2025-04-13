from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Enhanced password context with better defaults
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Higher work factor for better security
)


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT token with specified subject and expiration.
    
    Args:
        subject: The subject of the token (typically user ID)
        expires_delta: Optional expiration time override
        additional_claims: Optional additional claims to include in the token
        
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Base claims with expiration and subject
    to_encode = {"exp": expire, "sub": str(subject)}
    
    # Add issued at time for better security
    to_encode.update({"iat": datetime.utcnow()})
    
    # Add token type to prevent token confusion attacks
    to_encode.update({"type": "access"})
    
    # Add any additional claims provided
    if additional_claims:
        to_encode.update(additional_claims)
        
    # Use settings for algorithm and key
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash"""
    return pwd_context.hash(password)
