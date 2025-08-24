"""
Middleware for Intel Virtual Assistant Backend
Handles cross-cutting concerns like logging, error handling, and request processing.
"""

import time
import logging
import traceback
import uuid
from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app, log_body: bool = False):
        super().__init__(app)
        self.log_body = log_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log information."""
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Client: {client_ip} - User-Agent: {request.headers.get('user-agent', 'unknown')}"
        )
        
        # Log request body if enabled (be careful with sensitive data)
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body and len(body) < 1000:  # Only log small bodies
                    logger.debug(f"[{request_id}] Request body: {body.decode()[:500]}")
            except Exception as e:
                logger.warning(f"[{request_id}] Could not read request body: {e}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"[{request_id}] {response.status_code} - "
                f"Processing time: {process_time:.3f}s"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] Error processing request: {str(e)} - "
                f"Processing time: {process_time:.3f}s"
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors and exceptions."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with error handling."""
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # FastAPI HTTPExceptions should be handled normally
            raise
            
        except ValueError as e:
            # Handle validation errors
            logger.warning(f"Validation error: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Validation Error",
                    "message": str(e),
                    "type": "validation_error"
                }
            )
            
        except PermissionError as e:
            # Handle permission errors
            logger.warning(f"Permission error: {str(e)}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Permission Denied",
                    "message": str(e),
                    "type": "permission_error"
                }
            )
            
        except FileNotFoundError as e:
            # Handle file not found errors
            logger.warning(f"File not found: {str(e)}")
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Resource Not Found",
                    "message": str(e),
                    "type": "not_found_error"
                }
            )
            
        except Exception as e:
            # Handle all other exceptions
            request_id = getattr(request.state, 'request_id', 'unknown')
            logger.error(
                f"[{request_id}] Unhandled exception: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "type": "server_error",
                    "request_id": request_id
                }
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting based on client IP."""
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Initialize tracking for new IPs
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Clean old requests (older than 1 minute)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute.",
                    "type": "rate_limit_error"
                }
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - len(self.requests[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring API performance."""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "slow_requests": 0,
            "average_response_time": 0.0,
            "response_times": []
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate metrics
            process_time = time.time() - start_time
            self.metrics["total_requests"] += 1
            self.metrics["response_times"].append(process_time)
            
            # Keep only last 1000 response times
            if len(self.metrics["response_times"]) > 1000:
                self.metrics["response_times"] = self.metrics["response_times"][-1000:]
            
            # Calculate average
            self.metrics["average_response_time"] = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
            
            # Check for slow requests
            if process_time > self.slow_request_threshold:
                self.metrics["slow_requests"] += 1
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} - "
                    f"Processing time: {process_time:.3f}s"
                )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            self.metrics["total_errors"] += 1
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.metrics.copy()


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware that provides basic health check endpoint."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle health check requests."""
        if request.url.path == "/healthz" and request.method == "GET":
            return JSONResponse(
                status_code=200,
                content={
                    "status": "healthy",
                    "timestamp": time.time(),
                    "service": "Intel Virtual Assistant Backend"
                }
            )
        
        return await call_next(request)


# Middleware configuration function
def setup_middleware(app, config) -> None:
    """Set up all middleware for the FastAPI application."""
    
    # CORS middleware (should be first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Rate limiting
    if hasattr(config.server, 'rate_limit_per_minute'):
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=config.server.rate_limit_per_minute
        )
    else:
        app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
    
    # Performance monitoring
    app.add_middleware(
        PerformanceMonitoringMiddleware,
        slow_request_threshold=1.0
    )
    
    # Error handling
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Request logging (should be last to catch everything)
    app.add_middleware(
        RequestLoggingMiddleware,
        log_body=config.logging.level.lower() == "debug"
    )
    
    # Health check
    app.add_middleware(HealthCheckMiddleware)
    
    logger.info("Middleware setup completed")


# Logging configuration
def setup_logging(config) -> None:
    """Set up logging configuration."""
    import logging.config
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": config.logging.format,
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
            } if config.logging.enable_json_logs else {
                "format": config.logging.format,
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": config.logging.level.upper(),
                "formatter": "json" if config.logging.enable_json_logs else "detailed",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": config.logging.level.upper(),
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "WARNING",  # Reduce noise from uvicorn access logs
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # Add file handler if file path is specified
    if config.logging.file_path:
        from logging.handlers import RotatingFileHandler
        
        logging_config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": config.logging.level.upper(),
            "formatter": "json" if config.logging.enable_json_logs else "detailed",
            "filename": config.logging.file_path,
            "maxBytes": _parse_file_size(config.logging.max_file_size),
            "backupCount": config.logging.backup_count
        }
        
        # Add file handler to all loggers
        for logger_config in logging_config["loggers"].values():
            logger_config["handlers"].append("file")
    
    logging.config.dictConfig(logging_config)
    logger.info(f"Logging configured with level: {config.logging.level}")


def _parse_file_size(size_str: str) -> int:
    """Parse file size string (e.g., '10MB') to bytes."""
    size_str = size_str.upper()
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


# Context manager for request context
@asynccontextmanager
async def request_context(request: Request):
    """Provide request context for logging and tracing."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # Set context in logger
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    try:
        yield {"request_id": request_id}
    finally:
        logging.setLogRecordFactory(old_factory)