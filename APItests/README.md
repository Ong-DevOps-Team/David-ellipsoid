# Running API Tests

## Quick Start

### Prerequisites
- Python 3.8+ with virtual environment activated
- Backend server running (default: `http://localhost:8000`)
- Required packages installed: `pip install -r requirements.txt`
- Test accounts created in the database (see Configuration section)

### Basic Test Execution

1. **Navigate to the test directory:**
   ```bash
   cd backend/APItests
   ```

2. **Run all tests:**
   ```bash
   python -m pytest -v
   ```

3. **Run specific test file:**
   ```bash
   python -m pytest test_auth.py -v
   ```

4. **Run specific test function:**
   ```bash
   python -m pytest test_auth.py::TestAuthEndpoints::test_login_invalid_credentials -v
   ```

## Test Output

- **`-v`** flag provides verbose output showing each test
- Tests will show configuration information when starting
- Green dots (`.`) indicate passed tests
- Red `F` indicates failed tests
- `E` indicates errors

## Configuration

**⚠️ Important:** The tests connect to a real backend server and require real test accounts in the database.

### Test Account Requirements

The tests require the following test account to exist in your database:

- **Username**: `apitest_user`
- **Password**: `apitest_password_123`
- **User ID**: `8`

### Backend Configuration

By default, tests connect to `http://localhost:8000`. To change this, edit `config.py`:

```python
# Backend configuration
BACKEND_URL = "http://your-backend-url:port"
```

## Troubleshooting

- **Tests hanging?** Check that the backend URL is correct and accessible
- **Connection refused?** Ensure the backend server is running
- **Authentication failures?** Verify test accounts exist in the database
- **Timeout issues?** Increase `TEST_TIMEOUT` in `config.py`

## What Gets Tested

- **System endpoints** (`/`, `/health`)
- **Authentication endpoints** (`/auth/login`, `/auth/me`)
- **Chat endpoints** (`/chat/gis`, `/chat/rag`)
- **Saved chat management** (CRUD operations)
- **System endpoints** (`/about`, `/system-prompts`)
- **Error handling and validation**
- **Authentication and authorization**

## Test Results

**✅ All 36 tests are currently passing** - The API is functioning correctly with:
- Proper authentication and authorization
- All endpoints responding as expected
- Correct error handling for invalid requests
- Proper data validation and response formatting

## For More Information

- **Complete configuration guide**: [CONFIGURATION.md](CONFIGURATION.md)
- **API reference**: [../docs/backend/API_REFERENCE.md](../docs/backend/API_REFERENCE.md)
- **Universal user ID access**: [../docs/backend/UNIVERSAL_USER_ID_ACCESS.md](../docs/backend/UNIVERSAL_USER_ID_ACCESS.md)
