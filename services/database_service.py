import pyodbc
from cryptography.fernet import Fernet
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import get_settings

class DatabaseService:
    def __init__(self):
        self.settings = get_settings()
        self.db_connection = None
        self.crypt_obj = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection and cryptography object"""
        try:
            # Initialize cryptography
            key = self.settings.fernet_key
            byte_key = key.encode()
            self.crypt_obj = Fernet(byte_key)
            
            # Database connection string
            admin_username = self.settings.db_username
            admin_password = '{' + self.settings.db_password + '}'
            server = self.settings.db_server
            database = self.settings.db_name
            driver = '{ODBC Driver 18 for SQL Server}'
            
            connection_str = f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={admin_username};PWD={admin_password}'
            
            self.db_connection = pyodbc.connect(connection_str)
            
        except Exception as e:
            error_message = str(e).lower()
            if any(keyword in error_message for keyword in ['timeout', 'connection failed', 'login timeout', 'tcp provider']):
                raise Exception("Database connection timeout: The database is slow currently. Please try again in 60 seconds.")
            else:
                error_code = e.args[0] if e.args else "Unknown"
                raise Exception(f"Database connection failed: Error code {error_code}. Please contact support if this persists.")
    
    def verify_user(self, username: str, password: str) -> dict:
        """Verify username and password against database and return user info"""
        if username is None or password is None:
            return None
        
        if self.db_connection is None:
            self._initialize_connection()
        
        try:
            with self.db_connection.cursor() as cursor:
                # Use parameterized query to prevent SQL injection
                # Assuming: user_id (index 0), username (index 1), password (index 2)
                sql_statement = "SELECT USER_ID, USERNAME, PASSWORD FROM dbo.USERS WHERE USERNAME = ?"
                cursor.execute(sql_statement, (username,))
                row = cursor.fetchone()
                
                if row:
                    user_id = row[0]
                    stored_username = row[1]
                    stored_password = row[2]
                    
                    # Verify password
                    decrypted_password = self.crypt_obj.decrypt(stored_password)
                    if str(decrypted_password, "utf8") == password:
                        return {
                            "user_id": user_id,
                            "username": stored_username
                        }
                
                return None
                
        except Exception as e:
            error_message = str(e).lower()
            if any(keyword in error_message for keyword in ['timeout', 'connection failed', 'login timeout', 'tcp provider']):
                raise Exception("Database connection timeout: The database is slow currently. Please try again in 60 seconds.")
            else:
                raise Exception("Authentication error: Database connection failed")
    
    def close_connection(self):
        """Close database connection"""
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None
