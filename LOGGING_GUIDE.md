# Logging System Guide

## Overview

The backend now includes a comprehensive logging system with structured logging, multiple log files, and API endpoints for log management.

## Log Files

The system creates three separate log files in the `logs/` directory:

1. **`app.log`** - General application logs (all levels)
2. **`error.log`** - Error and critical logs only
3. **`access.log`** - API request/response logs

## Log Format

All log files use JSON format for structured logging:

```json
{
  "timestamp": "2025-01-14T12:30:45.123456",
  "level": "INFO",
  "logger": "app.routes.user_routes",
  "message": "User registered successfully: john_doe (ID: 123)",
  "module": "user_routes",
  "function": "register_user",
  "line": 33,
  "type": "business_event",
  "event_type": "user_registration",
  "user_id": "123",
  "details": {
    "username": "john_doe",
    "email": "john@example.com",
    "user_type": "individual"
  }
}
```

## Using Loggers

### Basic Usage

```python
from app.logger import get_logger

logger = get_logger(__name__)

# Log messages
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")
```

### Specialized Logging Functions

```python
from app.logger import log_api_request, log_error, log_business_event

# Log API requests
log_api_request(
    method="POST",
    path="/api/users",
    user_id="123",
    status_code=200,
    response_time=0.5,
    request_data={"name": "John"},
    response_data={"id": 123}
)

# Log errors with context
try:
    # Some operation
    pass
except Exception as e:
    log_error(e, context={"operation": "user_creation"}, user_id="123")

# Log business events
log_business_event(
    event_type="subscription_upgrade",
    user_id="123",
    details={"plan": "premium", "price": 29.99}
)
```

## API Endpoints

### Get Application Logs
```
GET /logs/app?lines=100&level=INFO&start_time=2025-01-14T00:00:00&end_time=2025-01-14T23:59:59
```

### Get Error Logs
```
GET /logs/errors?lines=100&start_time=2025-01-14T00:00:00&end_time=2025-01-14T23:59:59
```

### Get Access Logs
```
GET /logs/access?lines=100&start_time=2025-01-14T00:00:00&end_time=2025-01-14T23:59:59
```

### Get Log Summary
```
GET /logs/summary?hours=24
```

### Get Log Files Info
```
GET /logs/files
```

### Test Logging
```
POST /logs/test
{
  "message": "Test log message",
  "level": "INFO"
}
```

## Middleware

The system includes two middleware components:

1. **LoggingMiddleware** - Logs all API requests and responses
2. **ErrorHandlingMiddleware** - Catches and logs all unhandled exceptions

## Configuration

### Environment Variables

- `LOG_LEVEL` - Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Default: INFO

### Log Rotation

- Maximum file size: 10MB per log file
- Backup count: 10 files per log type
- Automatic rotation when size limit is reached

## Best Practices

### 1. Use Appropriate Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Something unexpected happened but application continues
- **ERROR**: Error occurred but application can continue
- **CRITICAL**: Serious error that might cause application to stop

### 2. Include Context

Always include relevant context in your logs:

```python
logger.info(f"User {user_id} uploaded document {filename} (size: {file_size} bytes)")
```

### 3. Use Structured Logging

Use the specialized logging functions for better structure:

```python
# Instead of:
logger.info(f"API request: {method} {path} - {status_code}")

# Use:
log_api_request(method, path, user_id, status_code, response_time)
```

### 4. Don't Log Sensitive Information

Never log passwords, API keys, or other sensitive data:

```python
# Bad
logger.info(f"User login: {username} with password {password}")

# Good
logger.info(f"User login attempt: {username}")
```

## Monitoring and Alerting

### Log Analysis

Use the `/logs/summary` endpoint to get insights:

- Total log counts by type
- Error frequency by type
- API endpoint usage
- Slow request detection

### Error Monitoring

Monitor the `error.log` file for:
- Application errors
- Database connection issues
- External API failures
- Authentication failures

### Performance Monitoring

Monitor the `access.log` file for:
- Slow API requests (>5 seconds)
- High error rates
- Unusual traffic patterns

## Testing

Run the test script to verify logging:

```bash
python test_logging.py
```

This will create test log entries in all log files.

## Troubleshooting

### Common Issues

1. **Log files not created**: Check directory permissions
2. **Empty log files**: Verify LOG_LEVEL environment variable
3. **Large log files**: Check log rotation settings
4. **Missing logs**: Ensure logger is imported correctly

### Debug Mode

Set `LOG_LEVEL=DEBUG` to see all log messages including debug level.

## Integration with Monitoring Tools

The JSON format makes it easy to integrate with monitoring tools like:

- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- Datadog
- New Relic
- Grafana Loki

Example logstash configuration:

```ruby
input {
  file {
    path => "/path/to/logs/*.log"
    codec => "json"
  }
}

filter {
  if [type] == "api_request" {
    # Process API request logs
  }
  if [type] == "error" {
    # Process error logs
  }
}
```
