import time
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.logger import log_api_request, get_logger

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        
        # Get user info if available (from token)
        user_id = None
        try:
            # Try to extract user info from request state if available
            if hasattr(request.state, 'user_id'):
                user_id = request.state.user_id
        except Exception:
            pass
        
        # Read request body for POST/PUT requests (be careful with large bodies)
        request_data = None
        if method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body and len(body) < 10000:  # Only log small bodies
                    try:
                        request_data = json.loads(body.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        request_data = f"<binary data: {len(body)} bytes>"
            except Exception as e:
                logger.warning(f"Could not read request body: {e}")
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            status_code = 500
            raise
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log the request
        log_api_request(
            method=method,
            path=path,
            user_id=user_id,
            status_code=status_code,
            response_time=response_time,
            request_data=request_data,
            response_data=None  # We don't log response data to avoid sensitive info
        )
        
        # Log slow requests
        if response_time > 5.0:  # Log requests taking more than 5 seconds
            logger.warning(f"Slow request detected: {method} {path} took {response_time:.2f}s")
        
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle and log errors globally"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the error with context
            from app.logger import log_error
            
            error_context = {
                'method': request.method,
                'path': request.url.path,
                'query_params': str(request.query_params) if request.query_params else None,
                'headers': dict(request.headers),
                'client_ip': request.client.host if request.client else None
            }
            
            # Try to get user ID
            user_id = None
            try:
                if hasattr(request.state, 'user_id'):
                    user_id = request.state.user_id
            except Exception:
                pass
            
            log_error(e, context=error_context, user_id=user_id)
            
            # Re-raise the exception to let FastAPI handle it
            raise
