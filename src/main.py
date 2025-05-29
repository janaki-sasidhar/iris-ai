"""Main application entry point"""

import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific loggers to appropriate levels
logging.getLogger('telethon').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

from telethon import TelegramClient
from src.config import settings, WhitelistManager
from src.database import DatabaseManager
from src.bot import CommandHandler, CallbackHandler, MessageHandler

logger = logging.getLogger(__name__)


async def main():
    """Main application function"""
    
    # Validate settings
    if not settings.validate():
        logger.error("Configuration validation failed. Please check your .env file.")
        return
    
    logger.info("🚀 Starting Telethon AI Bot...")
    
    # Initialize database
    db_manager = DatabaseManager()
    await db_manager.init()
    logger.info("✅ Database initialized")
    
    # Initialize Telegram client
    client = TelegramClient(
        'bot_session',
        settings.API_ID,
        settings.API_HASH
    )
    
    # Start the client
    await client.start(bot_token=settings.BOT_TOKEN)
    logger.info("✅ Telegram client connected")
    
    # Get bot info
    me = await client.get_me()
    logger.info(f"✅ Bot started as @{me.username}")
    
    # Initialize whitelist manager
    whitelist_manager = WhitelistManager()
    authorized_users = whitelist_manager.get_authorized_users()
    logger.info(f"✅ Whitelist loaded: {authorized_users}")
    
    # Initialize handlers
    command_handler = CommandHandler(client, db_manager)
    callback_handler = CallbackHandler(client, db_manager)
    message_handler = MessageHandler(client, db_manager)
    
    # Register all handlers
    command_handler.register_handlers()
    callback_handler.register_handlers()
    message_handler.register_handlers()
    
    logger.info("✅ All handlers registered")
    logger.info("\n🤖 Bot is running! Press Ctrl+C to stop.\n")
    
    try:
        # Keep the bot running
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("\n⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        # Cleanup
        await db_manager.close()
        await client.disconnect()
        logger.info("✅ Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())