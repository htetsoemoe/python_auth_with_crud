from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    """Application settings with validation"""

    def __init__(self):
        self.mongodb_uri: str = self._get_required_env("MONGODB_URI")
        self.database_name: str = os.getenv("DATABASE_NAME", "auth_crud")
        self.api_timeout: str = os.getenv("API_TIMEOUT", "30")

    @staticmethod
    def _get_required_env(key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value

settings = Settings()

# Backward compatibility
MONGODB_URI = settings.mongodb_uri