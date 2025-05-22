from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import argparse
import sys
from app.core.config import settings
from app.api.api import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for the Macro Investment Dashboard",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP error: {exc.detail}")
    return await http_exception_handler(request, exc)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )

# Include routers
app.include_router(api_router, prefix="/api")

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "ok"}

@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "description": "API for the Macro Investment Dashboard",
        "endpoints": {
            "health": "/health",
            "api": "/api",
            "docs": "/docs"
        }
    }

def run_server(host: str = None, port: int = None, reload: bool = None):
    """
    Run the FastAPI server with specified parameters.
    
    Args:
        host: The host to bind to
        port: The port to bind to
        reload: Whether to reload on code changes
    """
    import uvicorn
    
    uvicorn_host = host or settings.API_HOST
    uvicorn_port = port or settings.API_PORT
    uvicorn_reload = reload if reload is not None else True
    
    logger.info(f"Starting server on {uvicorn_host}:{uvicorn_port} (reload={uvicorn_reload})")
    
    uvicorn.run(
        "main:app", 
        host=uvicorn_host, 
        port=uvicorn_port, 
        reload=uvicorn_reload
    )

if __name__ == "__main__":
    # Command line arguments for server configuration
    parser = argparse.ArgumentParser(description="Run the Macro Dashboard API server")
    parser.add_argument("--host", help="Host to bind to", default=None)
    parser.add_argument("--port", help="Port to bind to", type=int, default=None)
    parser.add_argument("--no-reload", help="Disable auto-reload on code changes", action="store_true")
    
    args = parser.parse_args()
    run_server(
        host=args.host, 
        port=args.port, 
        reload=not args.no_reload
    )