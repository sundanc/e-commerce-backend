from fastapi import FastAPI, Request, status, Depends, HTTPException  # Add HTTPException here
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid

from app.api.routes import api_router
from app.core.config import settings
from app.core.limiter import limiter, _rate_limit_exceeded_handler  # Add this import
from slowapi.errors import RateLimitExceeded  # Add this import

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create custom middleware classes
class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS in production environments
    """
    async def dispatch(self, request: Request, call_next: Callable):
        if (settings.ENVIRONMENT == "production" and
            request.url.scheme == "http" and
            request.headers.get("x-forwarded-proto") != "https"):
            https_url = str(request.url).replace("http://", "https://", 1)
            return RedirectResponse(https_url, status_code=status.HTTP_301_MOVED_PERMANENTLY)
        return await call_next(request)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to responses
    """
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy - customize based on your needs
        csp_directives = [
            "default-src 'self'",
            "img-src 'self' data: https:",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Add cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
        
        # Add Referrer-Policy header
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests with timing information
    """
    async def dispatch(self, request: Request, call_next: Callable):
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client info
        client_host = request.client.host if request.client else "unknown"
        
        # Start timer
        start_time = time.time()
        
        # Log the request
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path} from {client_host}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add custom header with request ID
            response.headers["X-Request-ID"] = request_id
            
            # Log response info
            logger.info(
                f"Response {request_id}: {response.status_code} completed in {process_time:.3f}s"
            )
            
            return response
        except Exception as e:
            # Log exception
            process_time = time.time() - start_time
            logger.error(
                f"Request {request_id} failed after {process_time:.3f}s: {str(e)}",
                exc_info=True
            )
            # Let the exception handlers deal with it
            raise

app = FastAPI(
    title="E-commerce API",
    description="Backend API for E-commerce Platform",
    version="0.1.0"
)

# Add the limiter state and handler immediately after app creation
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add middlewares
if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggerMiddleware)

# Configure CORS with more restrictive settings
cors_origins = []
if settings.CORS_ORIGINS:
    cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
elif settings.ENVIRONMENT != "production":
    # Allow all origins only in non-production environments if CORS_ORIGINS is not set
    logger.warning("CORS_ORIGINS not set, allowing all origins for development.")
    cors_origins = ["*"]
else:
    # In production, require CORS_ORIGINS to be explicitly set
    logger.error("CORS_ORIGINS must be set in production environment!")
    # Optionally raise an error or default to a very restrictive setting:
    # raise ValueError("CORS_ORIGINS must be set in production environment!")
    cors_origins = [] # Default to no origins allowed if not set in production

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=86400,  # Cache preflight requests for 1 day
)

# Custom Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        f"HTTP {exc.status_code} - {request.method} {request.url.path} - {exc.detail}",
        extra={"request_id": getattr(request.state, "request_id", "unknown")}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log validation errors but sanitize potential sensitive data
    sanitized_errors = []
    for error in exc.errors():
        error_copy = error.copy()
        if error.get("type") == "value_error" and any(
            field in str(error.get("loc", [])).lower()
            for field in ["password", "token", "secret", "key", "auth"]
        ):
            error_copy["input"] = "[REDACTED]"
        sanitized_errors.append(error_copy)
    
    logger.warning(
        f"Validation error: {request.method} {request.url.path}",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "errors": sanitized_errors
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log unhandled exceptions but don't expose details to client
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}: {type(exc).__name__}",
        exc_info=True,
        extra={"request_id": getattr(request.state, "request_id", "unknown")}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )


app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to the E-commerce API",
        "docs": "/docs",
        "version": app.version
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}
