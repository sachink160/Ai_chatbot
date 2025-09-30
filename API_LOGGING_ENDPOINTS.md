# Logging API Endpoints Documentation

## Overview

The logging API provides endpoints to retrieve, analyze, and manage application logs. All endpoints require authentication.

## Base URL
```
/logs
```

## Authentication
All endpoints require a valid Bearer token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

## Endpoints

### 1. Get Application Logs
**GET** `/logs/app`

Retrieve general application logs with optional filtering.

#### Query Parameters
- `lines` (int, optional): Number of recent lines to retrieve (default: 100)
- `level` (string, optional): Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `start_time` (string, optional): Start time filter in ISO format (e.g., "2025-01-14T00:00:00")
- `end_time` (string, optional): End time filter in ISO format (e.g., "2025-01-14T23:59:59")

#### Example Request
```
GET /logs/app?lines=50&level=ERROR&start_time=2025-01-14T00:00:00
```

#### Example Response
```json
{
  "success": true,
  "file": "app.log",
  "total_entries": 25,
  "filters": {
    "lines": 50,
    "level": "ERROR",
    "start_time": "2025-01-14T00:00:00",
    "end_time": null
  },
  "logs": [
    {
      "timestamp": "2025-01-14T12:30:45.123456",
      "level": "ERROR",
      "logger": "app.routes.user_routes",
      "message": "Registration failed for john_doe: Database connection error",
      "module": "user_routes",
      "function": "register_user",
      "line": 43,
      "type": "error",
      "error_type": "DatabaseError",
      "user_id": "123",
      "context": {
        "username": "john_doe",
        "operation": "registration"
      }
    }
  ]
}
```

### 2. Get Error Logs
**GET** `/logs/errors`

Retrieve error and critical logs only.

#### Query Parameters
- `lines` (int, optional): Number of recent lines to retrieve (default: 100)
- `start_time` (string, optional): Start time filter in ISO format
- `end_time` (string, optional): End time filter in ISO format

#### Example Request
```
GET /logs/errors?lines=20
```

#### Example Response
```json
{
  "success": true,
  "file": "error.log",
  "total_entries": 15,
  "filters": {
    "lines": 20,
    "start_time": null,
    "end_time": null
  },
  "logs": [
    {
      "timestamp": "2025-01-14T12:30:45.123456",
      "level": "ERROR",
      "logger": "app.database",
      "message": "Database connection failed",
      "module": "database",
      "function": "get_db",
      "line": 19,
      "type": "error",
      "error_type": "ConnectionError",
      "context": {
        "database_url": "postgresql://...",
        "operation": "connection"
      }
    }
  ]
}
```

### 3. Get Access Logs
**GET** `/logs/access`

Retrieve API request/response logs.

#### Query Parameters
- `lines` (int, optional): Number of recent lines to retrieve (default: 100)
- `start_time` (string, optional): Start time filter in ISO format
- `end_time` (string, optional): End time filter in ISO format

#### Example Request
```
GET /logs/access?lines=100
```

#### Example Response
```json
{
  "success": true,
  "file": "access.log",
  "total_entries": 100,
  "filters": {
    "lines": 100,
    "start_time": null,
    "end_time": null
  },
  "logs": [
    {
      "timestamp": "2025-01-14T12:30:45.123456",
      "level": "INFO",
      "logger": "access",
      "message": "API Request",
      "type": "api_request",
      "method": "POST",
      "path": "/api/users",
      "user_id": "123",
      "status_code": 200,
      "response_time_ms": 150.5,
      "request_data": {
        "username": "john_doe",
        "email": "john@example.com"
      }
    }
  ]
}
```

### 4. Get Log Summary
**GET** `/logs/summary`

Get statistical summary of logs for a specified time period.

#### Query Parameters
- `hours` (int, optional): Number of hours to analyze (default: 24)

#### Example Request
```
GET /logs/summary?hours=48
```

#### Example Response
```json
{
  "success": true,
  "summary": {
    "time_range": {
      "start": "2025-01-13T12:30:45.123456",
      "end": "2025-01-14T12:30:45.123456",
      "hours": 48
    },
    "total_logs": {
      "app": 1250,
      "errors": 15,
      "access": 850
    },
    "log_levels": {
      "INFO": 1000,
      "WARNING": 200,
      "ERROR": 15,
      "DEBUG": 35
    },
    "error_types": {
      "ValidationError": 5,
      "DatabaseError": 3,
      "AuthenticationError": 4,
      "FileNotFoundError": 3
    },
    "api_endpoints": {
      "/api/users": 150,
      "/api/documents": 200,
      "/api/chat": 300,
      "/api/auth/login": 100
    },
    "slow_requests": 5
  }
}
```

### 5. Get Log Files Info
**GET** `/logs/files`

Get information about log files (size, modification time, etc.).

#### Example Request
```
GET /logs/files
```

#### Example Response
```json
{
  "success": true,
  "log_directory": "/path/to/logs",
  "files": [
    {
      "name": "app.log",
      "path": "/path/to/logs/app.log",
      "size_bytes": 1048576,
      "size_mb": 1.0,
      "modified": "2025-01-14T12:30:45.123456",
      "exists": true
    },
    {
      "name": "error.log",
      "path": "/path/to/logs/error.log",
      "size_bytes": 51200,
      "size_mb": 0.05,
      "modified": "2025-01-14T12:25:30.123456",
      "exists": true
    },
    {
      "name": "access.log",
      "path": "/path/to/logs/access.log",
      "size_bytes": 2097152,
      "size_mb": 2.0,
      "modified": "2025-01-14T12:30:45.123456",
      "exists": true
    }
  ]
}
```

### 6. Test Logging
**POST** `/logs/test`

Create a test log entry to verify logging functionality.

#### Request Body
```json
{
  "message": "Test log message",
  "level": "INFO"
}
```

#### Example Request
```
POST /logs/test
Content-Type: application/json

{
  "message": "This is a test log entry",
  "level": "WARNING"
}
```

#### Example Response
```json
{
  "success": true,
  "message": "Test warning log created successfully",
  "user_id": "123",
  "timestamp": "2025-01-14T12:30:45.123456"
}
```

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: User doesn't have permission
- `500 Internal Server Error`: Server error

#### Example Error Response
```json
{
  "detail": "Error retrieving logs: Permission denied"
}
```

## Rate Limiting

The logging endpoints are subject to rate limiting to prevent abuse:
- Maximum 100 requests per minute per user
- Maximum 1000 log entries per request

## Security Considerations

1. **Authentication Required**: All endpoints require valid authentication
2. **User Isolation**: Users can only access logs they have permission to view
3. **Sensitive Data**: Logs may contain sensitive information - handle with care
4. **Access Control**: Consider implementing role-based access control for log access

## Usage Examples

### Monitor Error Rates
```bash
# Get errors from last hour
curl -H "Authorization: Bearer <token>" \
  "https://api.example.com/logs/errors?start_time=2025-01-14T11:30:00&end_time=2025-01-14T12:30:00"
```

### Check API Performance
```bash
# Get access logs and check for slow requests
curl -H "Authorization: Bearer <token>" \
  "https://api.example.com/logs/access?lines=1000"
```

### Generate Daily Report
```bash
# Get summary for last 24 hours
curl -H "Authorization: Bearer <token>" \
  "https://api.example.com/logs/summary?hours=24"
```

## Integration with Monitoring Tools

The JSON format makes it easy to integrate with monitoring tools:

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Application Logs",
    "panels": [
      {
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(logs{level=\"ERROR\"}[5m]))"
          }
        ]
      }
    ]
  }
}
```

### ELK Stack Query
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"level": "ERROR"}},
        {"range": {"timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}
```
