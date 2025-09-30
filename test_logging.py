#!/usr/bin/env python3
"""
Test script to verify the logging system is working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.logger import get_logger, log_api_request, log_error, log_business_event
import time

def test_logging_system():
    """Test all logging functionality"""
    print("Testing logging system...")
    
    # Test basic logging
    logger = get_logger("test_module")
    
    print("1. Testing basic log levels...")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    print("2. Testing API request logging...")
    log_api_request(
        method="POST",
        path="/api/test",
        user_id="test_user_123",
        status_code=200,
        response_time=0.5,
        request_data={"test": "data"},
        response_data={"result": "success"}
    )
    
    print("3. Testing error logging...")
    try:
        raise ValueError("This is a test error")
    except Exception as e:
        log_error(e, context={"test": "context"}, user_id="test_user_123")
    
    print("4. Testing business event logging...")
    log_business_event(
        event_type="test_event",
        user_id="test_user_123",
        details={"action": "test", "timestamp": time.time()}
    )
    
    print("5. Testing module-specific loggers...")
    auth_logger = get_logger("app.auth")
    auth_logger.info("Authentication test log")
    
    db_logger = get_logger("app.database")
    db_logger.info("Database test log")
    
    print("\n✅ Logging system test completed!")
    print("Check the following log files:")
    print("- logs/app.log (general application logs)")
    print("- logs/error.log (error logs only)")
    print("- logs/access.log (API request logs)")

if __name__ == "__main__":
    test_logging_system()
