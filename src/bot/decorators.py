"""Decorators for bot handlers"""

from functools import wraps
from typing import Callable
from ..config import WhitelistManager
from ..config.settings import settings

# Create global whitelist manager instance
whitelist_manager = WhitelistManager(cache_ttl=settings.WHITELIST_CACHE_TTL)


def require_authorization(func: Callable) -> Callable:
    """Decorator to ensure user is authorized before executing handler"""
    @wraps(func)
    async def wrapper(self, event):
        user = await event.get_sender()
        
        # Get whitelist from manager (with caching)
        authorized_users = whitelist_manager.get_authorized_users()
        
        print(f"\n=== AUTH CHECK ===")
        print(f"User ID: {user.id}")
        print(f"Whitelist: {authorized_users}")
        
        # Check authorization
        if user.id not in authorized_users:
            print(f"DENIED: User {user.id} not in whitelist")
            await event.reply("Not authorized.")
            return
            
        print(f"ALLOWED: User {user.id} is authorized")
        return await func(self, event)
    
    return wrapper