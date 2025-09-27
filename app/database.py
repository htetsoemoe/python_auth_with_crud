from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection manager with error handling"""
    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db = None
        self.connect()
    
    def connect(self):
        """Establish database connection with error handling"""
        try:
            self._client = MongoClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS = 5000, # 5 seconds timeout
                connectTimeoutMS=10000, # 10 seconds connection timeout
                maxPoolSize=50, # Maximum number of connections
                minPoolSize=5, # Minimum number of connections
                maxIdleTimeMS=30000, # Close connections after 30 seconds
            )
            # Test the connection
            self._client.admin.command("ping")
            self._db = self._client[settings.database_name]
            logger.info("Successfully connected to MongoDB")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning(f"Failed to connect to MongoDB: {e}")
            logger.warning("Application will continue without database connectivity")
            self._client = None
            self._db = None

    @property
    def db(self):
        """Get database instance"""
        if self._db is None:
            self.connect()
        return self._db
    
    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            logger.info("Database connection closed")

# Global database manager instance
db_manager = DatabaseManager()
db = db_manager            