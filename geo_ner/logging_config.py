#!/usr/bin/env python3
"""
Centralized logging configuration for the NER application.

This module provides consistent logging setup across all modules.
"""

import logging
import sys
from typing import Optional


def setup_logging(level: str = "WARNING", format_string: Optional[str] = None) -> logging.Logger:
    """
    Setup centralized logging configuration for the application.
    
    Args:
        level (str): Logging level - "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        format_string (str, optional): Custom format string for log messages
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Default format for log messages
    if format_string is None:
        format_string = "%(levelname)s:%(name)s:%(message)s"
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    
    # Configure logging (only if not already configured)
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=numeric_level,
            format=format_string,
            stream=sys.stderr
        )
    
    # Return a logger for the calling module
    return logging.getLogger()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name (str): Name of the module (typically __name__)
        
    Returns:
        logging.Logger: Logger instance for the module
    """
    return logging.getLogger(name)


def set_logging_level(level: str) -> None:
    """
    Change the logging level for all loggers.
    
    Args:
        level (str): New logging level - "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    """
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    logging.getLogger().setLevel(numeric_level)
    
    # Also update all existing handlers
    for handler in logging.getLogger().handlers:
        handler.setLevel(numeric_level)


# Default logging levels for different environments
PRODUCTION_LEVEL = "WARNING"  # Only warnings and errors
DEVELOPMENT_LEVEL = "INFO"    # Informational messages and above
DEBUG_LEVEL = "DEBUG"         # All messages including debug

# Initialize logging with production settings by default
setup_logging(PRODUCTION_LEVEL)
