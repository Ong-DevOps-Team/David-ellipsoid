# API Test Configuration

## Overview

The API tests are designed to test the real backend system and require real test accounts in the database. All configuration is managed through the `config.py` file.

## Configuration File

All test configuration is centralized in `backend/APItests/config.py`:

```python
# Backend configuration
BACKEND_URL = "http://localhost:8000"

# Test configuration
TEST_TIMEOUT = 30

# Test Account Credentials
# These accounts must exist in the real database for tests to work
TEST_USERNAME = "apitest_user"
TEST_PASSWORD = "apitest_password_123"

# Test Account Details
TEST_USER_ID = 999  # This should match the actual user_id in the database

# Environment detection
ENVIRONMENT = "development"
```

## Test Account Requirements

**⚠️ CRITICAL:** The following test account must exist in your database for tests to work:

- **Username**: `apitest_user`
- **Password**: `apitest_password_123`
- **User ID**: `999`

### Creating Test Accounts

You must create this test account in your database before running tests. The tests will fail if the account doesn't exist.

## Configuration Options

### Backend URL

Change the backend server URL by editing `config.py`:

```python
# Local development
BACKEND_URL = "http://localhost:8000"

# Staging environment
BACKEND_URL = "http://staging.example.com:8000"

# Production environment
BACKEND_URL = "https://api.ellipsoidlabs.com"
```

### Test Timeout

Adjust the request timeout for slower environments:

```python
# Increase timeout for slower environments
TEST_TIMEOUT = 60
```

### Test Account Credentials

If you need different test credentials, update them in `config.py`:

```python
# Custom test account
TEST_USERNAME = "my_test_user"
TEST_PASSWORD = "my_test_password"
TEST_USER_ID = 1000  # Must match actual user_id in database
```

## Usage Examples

### Running Tests Against Local Backend
```bash
# Default behavior (localhost:8000)
cd backend/APItests
python -m pytest -v
```

### Running Tests Against Staging Backend
1. Edit `config.py`:
   ```python
   BACKEND_URL = "http://staging.example.com:8000"
   ENVIRONMENT = "staging"
   ```

2. Run tests:
   ```bash
   cd backend/APItests
   python -m pytest -v
   ```

### Running Tests Against Production Backend
1. Edit `config.py`:
   ```python
   BACKEND_URL = "https://api.ellipsoidlabs.com"
   ENVIRONMENT = "production"
   TEST_TIMEOUT = 60
   ```

2. Run tests:
   ```bash
   cd backend/APItests
   python -m pytest -v
   ```

## Security Notes

- **Test accounts are safe** - they use non-production credentials
- **No environment variables** - all configuration is in the config file
- **Test against staging** before running against production
- **Verify the backend URL** before running tests

## Troubleshooting

### Connection Refused
If you get connection errors, check:
1. The backend is running
2. The `BACKEND_URL` in `config.py` is correct
3. No firewall is blocking the connection
4. The backend is accessible from your test machine

### Authentication Failures
If authentication fails:
1. Verify the test account exists in the database
2. Check that `TEST_USERNAME` and `TEST_PASSWORD` in `config.py` match the database
3. Ensure the backend authentication service is working
4. Verify the `TEST_USER_ID` matches the actual user_id in the database

### Timeout Issues
If tests timeout:
1. Increase `TEST_TIMEOUT` in `config.py` for slower environments
2. Check network latency to the backend
3. Verify the backend is not overloaded

## Why No Environment Variables?

The API test suite uses a configuration file approach instead of environment variables because:

1. **Simplicity** - No need to remember environment variable names
2. **Consistency** - All developers use the same configuration
3. **Version Control** - Configuration changes are tracked
4. **No Confusion** - Single source of truth for all settings
5. **Easy Override** - Simply edit the config file for different environments
