import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration for Streamlit - loaded from environment variables."""
    
    # Base directories
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    
    # Create data directory
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
    
    # Download settings
    MAX_DOWNLOAD_RETRIES = int(os.getenv("MAX_DOWNLOAD_RETRIES", "3"))
    RETRY_INTERVAL = int(os.getenv("RETRY_INTERVAL", "5"))


# Global config instance
settings = Config()