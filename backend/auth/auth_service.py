from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from models.user_models import User, TokenData
from config.settings import get_settings
from logging_system import error

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handling
security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.settings = get_settings()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user against SQL Server database"""
        try:
            # Import here to avoid circular imports
            from services.database_service import DatabaseService
            
            db_service = DatabaseService()
            user_info = db_service.verify_user(username, password)
            if user_info:
                return User(user_id=user_info["user_id"], username=user_info["username"])
            return None
        except Exception as e:
            error(f"Authentication error: {e}")
            # Re-raise the exception so it can be handled by the calling endpoint
            raise
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.settings.jwt_secret_key, algorithm=self.settings.jwt_algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(token, self.settings.jwt_secret_key, algorithms=[self.settings.jwt_algorithm])
            user_id_str: str = payload.get("sub")
            username: str = payload.get("username")
            if user_id_str is None:
                return None
            # Convert string user_id back to integer
            user_id: int = int(user_id_str)
            token_data = TokenData(user_id=user_id, username=username)
            return token_data
        except JWTError:
            return None
        except ValueError:
            # Handle case where user_id cannot be converted to int
            error(f"Error: user_id '{user_id_str}' cannot be converted to integer")
            return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        auth_service = AuthService()
        token_data = auth_service.verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception
        return User(user_id=token_data.user_id, username=token_data.username)
    except Exception:
        raise credentials_exception
