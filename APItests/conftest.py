"""
Pytest configuration and fixtures for API tests
"""
import pytest
import asyncio
import httpx
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

# Import configuration
from config import BACKEND_URL, TEST_TIMEOUT, TEST_USERNAME, TEST_PASSWORD, TEST_USER_ID, print_config
from logging_system import info

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Create an HTTP client that connects to the actual running backend."""
    # Print configuration when client fixture is created
    print_config()
    info(f"Creating HTTP client for backend at: {BACKEND_URL}")
    info(f"Using timeout: {TEST_TIMEOUT}s")
    
    return httpx.Client(
        base_url=BACKEND_URL, 
        timeout=TEST_TIMEOUT,
        # Add transport options to prevent hanging
        transport=httpx.HTTPTransport(retries=1)
    )

# Test data fixtures for real API testing
@pytest.fixture
def valid_user_credentials():
    """Valid user credentials for testing."""
    return {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }

@pytest.fixture
def chat_request_data():
    """Chat request data for testing."""
    return {
        "message": "Hello, how are you?",
        "chat_history": [
            {"role": "user", "content": "Hello"}
        ]
    }

@pytest.fixture
def saved_chat_data():
    """Saved chat data for testing."""
    return {
        "chatname": "Test Chat",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    }
