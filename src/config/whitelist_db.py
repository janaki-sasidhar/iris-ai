"""Database-based whitelist management with caching"""

import time
from typing import List, Dict, Any, Optional
import asyncio
from functools import wraps


# Hardcoded superadmin ID
SUPERADMIN_ID = 7276342619


class DatabaseWhitelistManager:
    """Manages whitelist using database with caching"""
    
    def __init__(self, db_manager, cache_ttl: int = 60):
        self.db_manager = db_manager
        self.cache_ttl = cache_ttl
        self._last_load_time = 0
        self._cached_users = None
        self._lock = asyncio.Lock()
    
    async def get_authorized_users(self) -> List[int]:
        """Get list of authorized users with caching"""
        current_time = time.time()
        
        async with self._lock:
            # Check if cache is still valid
            if (self._cached_users is None or 
                current_time - self._last_load_time > self.cache_ttl):
                # Reload from database
                self._cached_users = await self.db_manager.get_whitelist_users()
                self._last_load_time = current_time
                
                # Always include superadmin
                if SUPERADMIN_ID not in self._cached_users:
                    self._cached_users.append(SUPERADMIN_ID)
                
                print(f"Whitelist reloaded from database: {self._cached_users}")
            else:
                print(f"Using cached whitelist (age: {int(current_time - self._last_load_time)}s)")
        
        return self._cached_users.copy()
    
    async def is_authorized(self, telegram_id: int) -> bool:
        """Check if a user is authorized"""
        # Superadmin is always authorized
        if telegram_id == SUPERADMIN_ID:
            return True
        
        authorized_users = await self.get_authorized_users()
        return telegram_id in authorized_users
    
    async def add_user(self, telegram_id: int, username: Optional[str] = None,
                      first_name: Optional[str] = None, last_name: Optional[str] = None,
                      added_by: Optional[int] = None, comment: Optional[str] = None) -> bool:
        """Add a user to the whitelist"""
        success = await self.db_manager.add_to_whitelist(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            added_by=added_by,
            comment=comment
        )
        
        if success:
            # Clear cache
            async with self._lock:
                self._cached_users = None
            print(f"Added user {telegram_id} to whitelist")
        
        return success
    
    async def remove_user(self, telegram_id: int) -> bool:
        """Remove a user from the whitelist"""
        # Cannot remove superadmin
        if telegram_id == SUPERADMIN_ID:
            return False
        
        success = await self.db_manager.remove_from_whitelist(telegram_id)
        
        if success:
            # Clear cache
            async with self._lock:
                self._cached_users = None
            print(f"Removed user {telegram_id} from whitelist")
        
        return success
    
    async def get_whitelist_info(self) -> Dict[str, Any]:
        """Get full whitelist information"""
        whitelist_entries = await self.db_manager.get_whitelist_info()
        
        # Add superadmin if not in database
        superadmin_exists = any(entry['telegram_id'] == SUPERADMIN_ID for entry in whitelist_entries)
        if not superadmin_exists:
            whitelist_entries.insert(0, {
                'telegram_id': SUPERADMIN_ID,
                'username': None,
                'added_at': None,
                'added_by': None,
                'comment': 'Hardcoded Superadmin'
            })
        
        return {
            'authorized_users': [entry['telegram_id'] for entry in whitelist_entries],
            'details': whitelist_entries
        }
    
    def is_superadmin(self, telegram_id: int) -> bool:
        """Check if user is the superadmin"""
        return telegram_id == SUPERADMIN_ID


def require_superadmin(func):
    """Decorator to ensure user is superadmin before executing handler"""
    @wraps(func)
    async def wrapper(self, event):
        user = await event.get_sender()
        
        if user.id != SUPERADMIN_ID:
            await event.reply("❌ This command is restricted to the superadmin only.")
            return
            
        return await func(self, event)
    
    return wrapper