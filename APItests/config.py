"""
Configuration for API tests
"""
from pathlib import Path

# Backend configuration
BACKEND_URL = "http://localhost:8000"

# Test configuration
TEST_TIMEOUT = 30

# Test Account Credentials
# These accounts must exist in the real database for tests to work
TEST_USERNAME = "apitest_user"
TEST_PASSWORD = "apitest_password_123"

# Test Account Details
TEST_USER_ID = 8  # This should match the actual user_id in the database

# Environment detection
ENVIRONMENT = "development"

from logging_system import info

def print_config():
    """Print current configuration (call this explicitly when needed)"""
    info(f"API Test Configuration:")
    info(f"  Environment: {ENVIRONMENT}")
    info(f"  Backend URL: {BACKEND_URL}")
    info(f"  Test Timeout: {TEST_TIMEOUT}s")
    info(f"  Test Username: {TEST_USERNAME}")
    info(f"  Test Password: {'*' * len(TEST_PASSWORD)}")
    info(f"  Test User ID: {TEST_USER_ID}")
    info("")
