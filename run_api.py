#!/usr/bin/env python3
"""
Startup script for Open Notebook API server.
"""

import os
import sys
import logging
from pathlib import Path

import uvicorn

# Add the current directory to Python path so imports work
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configure Uvicorn logging before importing our app
log_level = os.getenv("LOGLEVEL", "INFO").upper()
log_file = os.getenv("LOG_FILE", "")

# Configure Uvicorn access log format
access_log_format = '%(client_addr)s - "%(request_line)s" %(status_code)s'

if __name__ == "__main__":
    # Default configuration
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "5055"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"

    print(f"Starting Open Notebook API server on {host}:{port}")
    print(f"Reload mode: {reload}")
    print(f"Log level: {log_level}")
    if log_file:
        print(f"Logging to file: {log_file}")

    # Configure Uvicorn with our logging settings
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[str(current_dir)] if reload else None,
        log_level=log_level.lower(),
        access_log=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "access": {
                    "format": '%(asctime)s | %(levelname)-8s | %(client_addr)s - "%(request_line)s" %(status_code)s',
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default"],
                    "level": log_level,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["default"],
                    "level": log_level,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["access"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        },
    )
