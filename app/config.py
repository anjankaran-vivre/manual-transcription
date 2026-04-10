import os
import warnings
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration loaded from environment variables."""
    
    # Base directories
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    DATA_DIR = os.path.join(BASE_DIR, "data")
    
    # Create directories
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Zoho OAuth
    ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
    ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
    ZOHO_REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI")
    TOKEN_FILE = os.path.join(DATA_DIR, "zoho_tokens.json")
    
    # Audio download credentials
    AUDIO_USERNAME = os.getenv("AUDIO_USERNAME")
    AUDIO_PASSWORD = os.getenv("AUDIO_PASSWORD")
    
    # Groq API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Processing settings
    PROCESS_DELAY = int(os.getenv("PROCESS_DELAY"))
    MAX_DOWNLOAD_RETRIES = int(os.getenv("MAX_DOWNLOAD_RETRIES"))
    RETRY_INTERVAL = int(os.getenv("RETRY_INTERVAL"))
    NUM_WORKERS = int(os.getenv("NUM_WORKERS"))
    
    # PID file for process management
    PID_FILE = os.path.join(DATA_DIR, "server.pid")
    
    # Email settings for alerts (optional - will warn if not configured)
    _email_enabled = os.getenv("EMAIL_ENABLED")
    if _email_enabled is None:
        EMAIL_ENABLED = False
        warnings.warn("⚠️  EMAIL_ENABLED not set in .env - email notifications disabled", UserWarning)
    else:
        EMAIL_ENABLED = _email_enabled.lower() == "true"
    
    SMTP_SERVER = os.getenv("SMTP_SERVER", "")
    if not SMTP_SERVER:
        warnings.warn("⚠️  SMTP_SERVER not configured - email service unavailable", UserWarning)
    
    _smtp_port = os.getenv("SMTP_PORT")
    SMTP_PORT = int(_smtp_port) if _smtp_port else 587
    
    EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS", "").split(",") if os.getenv("EMAIL_RECIPIENTS") else []
    
    # Groq limits
    GROQ_DAILY_LIMIT = int(os.getenv("GROQ_DAILY_LIMIT"))
    GROQ_MINUTE_LIMIT = int(os.getenv("GROQ_MINUTE_LIMIT"))
    
    # Server settings
    HOST = os.getenv("HOST")
    PORT = int(os.getenv("PORT"))
    DEBUG = os.getenv("DEBUG").lower() == "true"
    
    # Database settings
    DB_HOST = os.getenv("DB_HOST")
    DB_SERVER = os.getenv("DB_SERVER")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")


# Global config instance for backward compatibility
settings = Config()