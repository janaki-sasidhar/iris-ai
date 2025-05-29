"""Whitelist management with caching"""

import json
import time
from typing import List, Dict, Any
import os
from pathlib import Path


class WhitelistManager:
    """Manages whitelist with caching"""
    
    def __init__(self, whitelist_file: str = "whitelist.json", cache_ttl: int = 60):
        self.whitelist_file = Path(whitelist_file)
        self.cache_ttl = cache_ttl
        self._last_load_time = 0
        self._cached_data = None
        
        # Ensure whitelist file exists
        if not self.whitelist_file.exists():
            self._create_default_whitelist()
    
    def _create_default_whitelist(self):
        """Create default whitelist file"""
        default_data = {
            "authorized_users": [],
            "comments": {}
        }
        self._save_whitelist(default_data)
    
    def _load_whitelist(self) -> Dict[str, Any]:
        """Load whitelist from JSON file"""
        try:
            with open(self.whitelist_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading whitelist: {e}")
            return {"authorized_users": [], "comments": {}}
    
    def _save_whitelist(self, data: Dict[str, Any]):
        """Save whitelist to JSON file"""
        try:
            with open(self.whitelist_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving whitelist: {e}")
    
    def get_authorized_users(self) -> List[int]:
        """Get list of authorized users with caching"""
        current_time = time.time()
        
        # Check if cache is still valid
        if (self._cached_data is None or 
            current_time - self._last_load_time > self.cache_ttl):
            # Reload from file
            self._cached_data = self._load_whitelist()
            self._last_load_time = current_time
            print(f"Whitelist reloaded from file: {self._cached_data.get('authorized_users', [])}")
        else:
            print(f"Using cached whitelist (age: {int(current_time - self._last_load_time)}s)")
        
        return self._cached_data.get("authorized_users", [])
    
    def add_user(self, user_id: int, comment: str = "") -> bool:
        """Add a user to the whitelist"""
        data = self._load_whitelist()
        
        if user_id not in data["authorized_users"]:
            data["authorized_users"].append(user_id)
            if comment:
                data["comments"][str(user_id)] = comment
            
            self._save_whitelist(data)
            self._cached_data = None  # Clear cache
            print(f"Added user {user_id} to whitelist")
            return True
        return False
    
    def remove_user(self, user_id: int) -> bool:
        """Remove a user from the whitelist"""
        data = self._load_whitelist()
        
        if user_id in data["authorized_users"]:
            data["authorized_users"].remove(user_id)
            data["comments"].pop(str(user_id), None)
            
            self._save_whitelist(data)
            self._cached_data = None  # Clear cache
            print(f"Removed user {user_id} from whitelist")
            return True
        return False
    
    def get_whitelist_info(self) -> Dict[str, Any]:
        """Get full whitelist information"""
        return self._load_whitelist()