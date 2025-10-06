from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.database import db_manager
from app.config import settings
import asyncio 
import logging
import sys
from typing import Dict, Any
from app.api import auth, users

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Auth with CRUD Application...")

    try:
        # Test database connection
        try:
            db_manager.connect()
            if db_manager._db is not None:
                logger.info("Database connection established")
            else:
                logger.warning("Application will continue without database connection")
        except Exception as e:
            logger.warning(f"Failed to connect to database: {e}")
            logger.warning("Application will continue without database connection")
        
        logger.info("Application startup completed")

        yield

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down application...")
        try:
            db_manager.close()
            logger.info("Application shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Create FastAPI application
app = FastAPI(
    title="Auth with CRUD API",
    description="Auth with CRUD REST API With FastAPI",
    version="1.0.0",
    lifespan=lifespan
)     

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check point
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """Health check point"""
    try:
        # Check database connection
        db_manager.db.admin.command('ping')
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "message": "Welcome to Auth with CRUD API",
        "docs": "/docs",
        "health": "/health"
    }

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])

if __name__ == "__main__":
    # ASGI, or Asynchronous Server Gateway Interface, defines a standard interface 
    # between asynchronous-capable Python web servers and web applications.
    import uvicorn
    uvicorn.run(    
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
