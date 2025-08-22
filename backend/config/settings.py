import os
import toml
from pathlib import Path
from typing import Optional

class Settings:
    def __init__(self):
        # Load secrets from backend/secrets.toml
        secrets_path = Path(__file__).parent.parent / "secrets.toml"
        if secrets_path.exists():
            self.secrets = toml.load(secrets_path)
        else:
            self.secrets = {}
        
        # Database settings
        self.db_username: str = os.getenv("DB_USERNAME", self.secrets.get("DB_USERNAME", ""))
        self.db_password: str = os.getenv("DB_PASSWORD", self.secrets.get("DB_PASSWORD", ""))
        self.fernet_key: str = os.getenv("FERNET_KEY", self.secrets.get("FERNET_KEY", ""))
        self.db_server: str = "geog495db.database.windows.net"
        self.db_name: str = "EllipsoidLabs"
        
        # API keys
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", self.secrets.get("OPENAI_API_KEY", ""))
        self.aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", self.secrets.get("AWS_ACCESS_KEY_ID", ""))
        self.aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", self.secrets.get("AWS_SECRET_ACCESS_KEY", ""))
        self.esri_api_key: str = os.getenv("ESRI_API_KEY", self.secrets.get("ESRI_API_KEY", ""))
        self.shipengine_api_key: str = os.getenv("SHIPENGINE_API_KEY", self.secrets.get("SHIPENGINE_API_KEY", ""))
        
        # MongoDB
        self.mongo_connection_string: str = os.getenv("MONGO_CONNECTION_STRING", self.secrets.get("MONGO_CONNECTION_STRING", ""))

        # JWT settings
        self.jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", self.secrets.get("JWT_SECRET_KEY", "your-secret-key-change-in-production"))
        self.jwt_algorithm: str = "HS256"
        self.access_token_expire_minutes: int = 30
        
        # AWS settings
        self.aws_region: str = "us-west-2"
        self.bedrock_knowledge_base_id: str = "7XICFRMU5Y"
        self.bedrock_rerank_model_arn: str = "arn:aws:bedrock:us-west-2::foundation-model/amazon.rerank-v1:0"
        
        # Model IDs
        self.amazon_nova_lite_model_id: str = "arn:aws:bedrock:us-west-2:854669816847:inference-profile/us.amazon.nova-lite-v1:0"
        self.anthropic_claude_model_id: str = "arn:aws:bedrock:us-west-2:854669816847:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        
        # System prompts
        self.DEFAULT_SYSTEM_PROMPT: str = "You are a Geographic Information Systems (GIS) expert. Please help the user with their GIS questions and problems."

def get_settings() -> Settings:
    return Settings()