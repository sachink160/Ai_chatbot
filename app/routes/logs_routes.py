from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import json
from datetime import datetime, timedelta
from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/logs", tags=["Logs Management"])

# Log file paths
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
APP_LOG_FILE = os.path.join(LOG_DIR, 'app.log')
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'error.log')
ACCESS_LOG_FILE = os.path.join(LOG_DIR, 'access.log')

def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a JSON log line into a dictionary"""
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError:
        return None

def read_log_file(file_path: str, lines: int = 100, level: str = None, 
                 start_time: str = None, end_time: str = None) -> List[Dict[str, Any]]:
    """Read and filter log file"""
    if not os.path.exists(file_path):
        return []
    
    logs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read last N lines
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if lines > 0 else all_lines
            
            for line in recent_lines:
                log_entry = parse_log_line(line)
                if not log_entry:
                    continue
                
                # Filter by level
                if level and log_entry.get('level', '').upper() != level.upper():
                    continue
                
                # Filter by time range
                if start_time or end_time:
                    log_time_str = log_entry.get('timestamp', '')
                    if log_time_str:
                        try:
                            log_time = datetime.fromisoformat(log_time_str.replace('Z', '+00:00'))
                            
                            if start_time:
                                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                if log_time < start_dt:
                                    continue
                            
                            if end_time:
                                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                                if log_time > end_dt:
                                    continue
                        except ValueError:
                            continue
                
                logs.append(log_entry)
    
    except Exception as e:
        logger.error(f"Error reading log file {file_path}: {e}")
    
    return logs

@router.get("/app")
async def get_app_logs(
    lines: int = Query(100, description="Number of recent lines to retrieve"),
    level: Optional[str] = Query(None, description="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    start_time: Optional[str] = Query(None, description="Start time filter (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time filter (ISO format)"),
    current_user: User = Depends(get_current_user)
):
    """Get application logs"""
    try:
        logs = read_log_file(APP_LOG_FILE, lines, level, start_time, end_time)
        
        logger.info(f"User {current_user.id} requested app logs: {len(logs)} entries")
        
        return {
            "success": True,
            "file": "app.log",
            "total_entries": len(logs),
            "filters": {
                "lines": lines,
                "level": level,
                "start_time": start_time,
                "end_time": end_time
            },
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Error retrieving app logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")

@router.get("/errors")
async def get_error_logs(
    lines: int = Query(100, description="Number of recent lines to retrieve"),
    start_time: Optional[str] = Query(None, description="Start time filter (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time filter (ISO format)"),
    current_user: User = Depends(get_current_user)
):
    """Get error logs"""
    try:
        logs = read_log_file(ERROR_LOG_FILE, lines, "ERROR", start_time, end_time)
        
        logger.info(f"User {current_user.id} requested error logs: {len(logs)} entries")
        
        return {
            "success": True,
            "file": "error.log",
            "total_entries": len(logs),
            "filters": {
                "lines": lines,
                "start_time": start_time,
                "end_time": end_time
            },
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Error retrieving error logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")

@router.get("/access")
async def get_access_logs(
    lines: int = Query(100, description="Number of recent lines to retrieve"),
    start_time: Optional[str] = Query(None, description="Start time filter (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time filter (ISO format)"),
    current_user: User = Depends(get_current_user)
):
    """Get access logs (API requests/responses)"""
    try:
        logs = read_log_file(ACCESS_LOG_FILE, lines, None, start_time, end_time)
        
        logger.info(f"User {current_user.id} requested access logs: {len(logs)} entries")
        
        return {
            "success": True,
            "file": "access.log",
            "total_entries": len(logs),
            "filters": {
                "lines": lines,
                "start_time": start_time,
                "end_time": end_time
            },
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Error retrieving access logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")

@router.get("/summary")
async def get_log_summary(
    hours: int = Query(24, description="Number of hours to analyze"),
    current_user: User = Depends(get_current_user)
):
    """Get log summary statistics"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Get logs from all files
        app_logs = read_log_file(APP_LOG_FILE, 0, None, start_time.isoformat(), end_time.isoformat())
        error_logs = read_log_file(ERROR_LOG_FILE, 0, None, start_time.isoformat(), end_time.isoformat())
        access_logs = read_log_file(ACCESS_LOG_FILE, 0, None, start_time.isoformat(), end_time.isoformat())
        
        # Analyze logs
        summary = {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "total_logs": {
                "app": len(app_logs),
                "errors": len(error_logs),
                "access": len(access_logs)
            },
            "log_levels": {},
            "error_types": {},
            "api_endpoints": {},
            "slow_requests": 0
        }
        
        # Analyze app logs by level
        for log in app_logs:
            level = log.get('level', 'UNKNOWN')
            summary["log_levels"][level] = summary["log_levels"].get(level, 0) + 1
        
        # Analyze error logs
        for log in error_logs:
            error_type = log.get('error_type', 'Unknown')
            summary["error_types"][error_type] = summary["error_types"].get(error_type, 0) + 1
        
        # Analyze access logs
        for log in access_logs:
            if log.get('type') == 'api_request':
                endpoint = log.get('path', 'unknown')
                summary["api_endpoints"][endpoint] = summary["api_endpoints"].get(endpoint, 0) + 1
                
                # Count slow requests
                response_time = log.get('response_time_ms', 0)
                if response_time and response_time > 5000:  # > 5 seconds
                    summary["slow_requests"] += 1
        
        logger.info(f"User {current_user.id} requested log summary for {hours} hours")
        
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error generating log summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@router.get("/files")
async def get_log_files_info(current_user: User = Depends(get_current_user)):
    """Get information about log files"""
    try:
        files_info = []
        
        for file_name, file_path in [
            ("app.log", APP_LOG_FILE),
            ("error.log", ERROR_LOG_FILE),
            ("access.log", ACCESS_LOG_FILE)
        ]:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                files_info.append({
                    "name": file_name,
                    "path": file_path,
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "exists": True
                })
            else:
                files_info.append({
                    "name": file_name,
                    "path": file_path,
                    "size_bytes": 0,
                    "size_mb": 0,
                    "modified": None,
                    "exists": False
                })
        
        logger.info(f"User {current_user.id} requested log files info")
        
        return {
            "success": True,
            "log_directory": LOG_DIR,
            "files": files_info
        }
    except Exception as e:
        logger.error(f"Error getting log files info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting files info: {str(e)}")

@router.post("/test")
async def test_logging(
    message: str = "Test log message",
    level: str = "INFO",
    current_user: User = Depends(get_current_user)
):
    """Test logging functionality"""
    try:
        test_logger = get_logger("test")
        
        if level.upper() == "DEBUG":
            test_logger.debug(f"Test debug message from user {current_user.id}: {message}")
        elif level.upper() == "INFO":
            test_logger.info(f"Test info message from user {current_user.id}: {message}")
        elif level.upper() == "WARNING":
            test_logger.warning(f"Test warning message from user {current_user.id}: {message}")
        elif level.upper() == "ERROR":
            test_logger.error(f"Test error message from user {current_user.id}: {message}")
        elif level.upper() == "CRITICAL":
            test_logger.critical(f"Test critical message from user {current_user.id}: {message}")
        else:
            raise HTTPException(status_code=400, detail="Invalid log level")
        
        return {
            "success": True,
            "message": f"Test {level.lower()} log created successfully",
            "user_id": current_user.id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error testing logging: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing logging: {str(e)}")
