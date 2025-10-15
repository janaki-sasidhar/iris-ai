"""Decorators for bot handlers"""

from functools import wraps
from typing import Callable
from ..config.whitelist_db import DatabaseWhitelistManager, SUPERADMIN_ID
from ..config.settings import settings

# Note: The whitelist_manager will be initialized in the main bot setup
# after the database manager is created
whitelist_manager = None


def set_whitelist_manager(manager: DatabaseWhitelistManager):
    """Set the global whitelist manager instance"""
    global whitelist_manager
    whitelist_manager = manager


def require_authorization(func: Callable) -> Callable:
    """Decorator to ensure user is authorized before executing handler"""
    @wraps(func)
    async def wrapper(self, event):
        user = await event.get_sender()
        
        if whitelist_manager is None:
            print("ERROR: Whitelist manager not initialized!")
            await event.reply("Bot initialization error. Please contact administrator.")
            return
        
        # Check authorization
        is_authorized = await whitelist_manager.is_authorized(user.id)
        
        print(f"\n=== AUTH CHECK ===")
        print(f"User ID: {user.id}")
        print(f"Authorized: {is_authorized}")
        
        if not is_authorized:
            print(f"DENIED: User {user.id} not authorized")
            await event.reply("Not authorized.")
            return
            
        print(f"ALLOWED: User {user.id} is authorized")
        return await func(self, event)
    
    return wrapper


def require_superadmin(func: Callable) -> Callable:
    """Decorator to ensure user is superadmin before executing handler"""
    @wraps(func)
    async def wrapper(self, event):
        user = await event.get_sender()
        
        if user.id != SUPERADMIN_ID:
            await event.reply("❌ This command is restricted to the superadmin only.")
            return
            
        return await func(self, event)
    
    return wrapper
