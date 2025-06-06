"""Bot configuration settings"""

import os
import sys
import logging
from typing import List
from dotenv import load_dotenv

from .doppler import load_doppler_secrets, DopplerError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to load environment variables from different sources
# 1. Try Doppler first if token is available
if os.environ.get("DOPPLER_TOKEN") and os.environ.get("ENVIRONMENT"):
    try:
        secrets = load_doppler_secrets()
        logger.info(f"✅ Loaded {len(secrets)} secrets from Doppler")
    except DopplerError as e:
        logger.warning(f"⚠️ Doppler error: {str(e)}")
        logger.warning("Falling back to .env file")
        # Fall back to .env file
        load_dotenv()
        logger.info("✅ Loaded environment variables from .env file")
    except Exception as e:
        logger.warning(f"⚠️ Unexpected error with Doppler: {str(e)}")
        logger.warning("Falling back to .env file")
        # Fall back to .env file
        load_dotenv()
        logger.info("✅ Loaded environment variables from .env file")
else:
    # 2. Try .env file if Doppler is not configured
    logger.info("Doppler not configured, loading from .env file")
    load_dotenv()
    logger.info("✅ Loaded environment variables from .env file")

# 3. Environment variables set directly will override both Doppler and .env


class Settings:
    """Central configuration class for the bot"""
    
    # Telegram Configuration
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Vorren API Configuration (for multiple providers)
    VORREN_API_KEY: str = os.getenv("VORREN_API_KEY", "")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_database.db")
    
    # Bot Settings
    DEFAULT_MODEL: str = "gemini-2.5-flash-preview-05-20"
    DEFAULT_TEMPERATURE: float = 0.7
    
    # Model Options
    AVAILABLE_MODELS = {
        "flash": "gemini-2.5-flash-preview-05-20",
        "pro": "gemini-2.5-pro-preview-05-06",
        "flash-image": "gemini-2.0-flash-preview-image-generation",
        "imagen3": "imagen-3.0-generate-002",
        "claude-sonnet-4": "claude-sonnet-4-20250514",
        "claude-3.7-sonnet": "claude-3-7-sonnet-20250219",
        "claude-3.5-sonnet": "claude-3-5-sonnet-20241022",
        "o4-mini": "o4-mini-2025-04-16",
        "gpt-4.1": "gpt-4.1-2025-04-14",
        "gpt-4o": "gpt-4o-2024-08-06"
    }
    
    # Proxy endpoints
    PROXY_ENDPOINTS = {
        "aws-claude": "https://pepper.eu.loclx.io/proxy/aws/claude",
        "openai": "https://pepper.eu.loclx.io/proxy/openai"
    }
    
    # Message Settings
    MAX_MESSAGE_LENGTH: int = 3000  # Telegram limit is 4096, leave buffer
    
    # Cache Settings
    WHITELIST_CACHE_TTL: int = 60  # seconds
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required settings"""
        if not cls.API_ID or not cls.API_HASH or not cls.BOT_TOKEN:
            print("❌ Missing Telegram API credentials")
            return False
        
        # At least one LLM API key must be present
        if not cls.GEMINI_API_KEY and not cls.VORREN_API_KEY:
            print("❌ Missing API keys: Need either GEMINI_API_KEY or VORREN_API_KEY")
            return False
        
        return True


# Create singleton instance
settings = Settings()