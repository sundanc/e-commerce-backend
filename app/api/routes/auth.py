from datetime import timedelta
from typing import Any
import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.database import get_db
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, User as UserSchema
from app.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

# Function to create JTI (JWT ID) for token tracking
def generate_jti() -> str:
    """Generate a unique JWT ID"""
    return secrets.token_urlsafe(16)

@router.post("/login", response_model=Token)
@limiter.limit("5/minute") # Stricter rate limit (5 attempts per minute per IP)
async def login_access_token(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Normalize email to lowercase to prevent case-sensitivity bypass
    email = form_data.username.lower() if '@' in form_data.username else form_data.username
    
    # Get user by email
    user = db.query(User).filter(User.email == email).first()
    
    # If no user found or wrong password - don't distinguish between these cases
    # to prevent user enumeration
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Audit log: Failed login attempt
        logger.warning(
            f"Failed login attempt for: {email} from IP: {request.client.host}",
            extra={"client_ip": request.client.host, "user_agent": request.headers.get("user-agent", "Unknown")}
        )
        # Use a consistent error message that doesn't leak information
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        # Audit log: Inactive user login attempt
        logger.warning(
            f"Inactive user login attempt: {user.email} (ID: {user.id}) from IP: {request.client.host}",
            extra={"client_ip": request.client.host, "user_id": user.id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Generate unique token ID for potential revocation
    jti = generate_jti()
    
    # Create additional claims for token
    additional_claims = {
        "jti": jti,  # JWT ID for tracking/revocation
        "type": "access",  # Token type
        "email": user.email,  # Add email for audit trail
        "admin": user.is_admin,  # Include role in token
    }

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user.id, 
        expires_delta=access_token_expires,
        additional_claims=additional_claims
    )

    # Audit log: Successful login
    logger.info(
        f"Successful login for user: {user.email} (ID: {user.id}) from IP: {request.client.host}",
        extra={
            "client_ip": request.client.host, 
            "user_id": user.id,
            "user_agent": request.headers.get("user-agent", "Unknown"),
            "jti": jti
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post("/register", response_model=UserSchema)
@limiter.limit("10/hour") # Strict rate limit for registration
async def register_user(
    request: Request,
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user
    """
    # Check for existing user by email (case-insensitive)
    user = db.query(User).filter(User.email.ilike(user_in.email)).first()
    if user:
        # Log registration attempt for existing email
        logger.warning(
            f"Registration attempt with existing email: {user_in.email} from IP: {request.client.host}",
            extra={"client_ip": request.client.host}
        )
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
        
    # Check for existing username (case-insensitive)
    user = db.query(User).filter(User.username.ilike(user_in.username)).first()
    if user:
        # Log registration attempt for existing username
        logger.warning(
            f"Registration attempt with existing username: {user_in.username} from IP: {request.client.host}",
            extra={"client_ip": request.client.host}
        )
        raise HTTPException(
            status_code=400,
            detail="A user with this username already exists.",
        )
    
    # Create user with email normalized to lowercase
    user = User(
        email=user_in.email.lower(),  # Normalize email
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Audit log: User registration
    logger.info(
        f"New user registered: {user.email} (ID: {user.id}) from IP: {request.client.host}",
        extra={
            "client_ip": request.client.host,
            "user_id": user.id,
            "username": user.username,
            "user_agent": request.headers.get("user-agent", "Unknown")
        }
    )
    
    # Return without password
    return user
