import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    API_PORT: int = int(os.getenv("API_PORT", 8000))
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PROJECT_NAME: str = "Macro Dashboard API"
    
    # External API keys
    FRED_API_KEY: str = os.getenv("FRED_API_KEY", "")
    
    # Database settings can be added later
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]  # For development
    
    class Config:
        env_file = ".env"

settings = Settings()