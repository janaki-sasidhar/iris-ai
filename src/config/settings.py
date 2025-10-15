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
    
    # Google Cloud / Vertex AI Configuration
    # We use ADC via gcloud; API keys are not required.
    GCP_PROJECT: str = os.getenv("GCP_PROJECT", "play-hoa")
    GCP_LOCATION: str = os.getenv("GCP_LOCATION", "global")

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_database.db")
    
    # Bot Settings
    DEFAULT_MODEL: str = "gemini-2.5-flash"
    DEFAULT_TEMPERATURE: float = 0.7
    
    # Model Options
    # Supported Models (post-migration)
    AVAILABLE_MODELS = {
        # Vertex Gemini GA
        "gemini-flash": "gemini-2.5-flash",
        "gemini-pro": "gemini-2.5-pro",
        # Vertex Anthropic (publisher models)
        "claude-sonnet-4-5": "claude-sonnet-4-5@20250929",
        "claude-opus-4-1": "claude-opus-4-1@20250805",
        # OpenAI GPT-5
        "gpt-5": "gpt-5",
        "gpt-5-chat": "gpt-5-chat-latest",
    }
    
    # Legacy proxy endpoints removed; all calls go direct.
    
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
        
        # Require OpenAI key if using OpenAI; Vertex uses ADC via gcloud
        if not cls.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set. OpenAI provider will be unavailable.")
        
        return True


# Create singleton instance
settings = Settings()
