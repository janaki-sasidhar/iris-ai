"""Utility functions for retrieving Telegram user information"""

from telethon import TelegramClient
from typing import Optional, Dict, Any, Union


async def get_user_by_id(client: TelegramClient, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get user information by Telegram user ID
    
    Args:
        client: Initialized Telethon client
        user_id: Telegram user ID
        
    Returns:
        Dictionary with user information or None if user not found
    """
    try:
        # Get the user entity from their ID
        user = await client.get_entity(user_id)
        
        # Create a dictionary with user information
        user_info = {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': getattr(user, 'phone', None),
            'bot': getattr(user, 'bot', False),
            'verified': getattr(user, 'verified', False),
            'restricted': getattr(user, 'restricted', False),
            'scam': getattr(user, 'scam', False),
            'fake': getattr(user, 'fake', False),
        }
        
        return user_info
    except ValueError:
        # User not found
        return None
    except Exception as e:
        print(f"Error retrieving user information: {str(e)}")
        return None


async def get_user_by_username_or_id(client: TelegramClient, 
                                    identifier: Union[str, int]) -> Optional[Dict[str, Any]]:
    """
    Get user information by username or ID
    
    Args:
        client: Initialized Telethon client
        identifier: Username (with or without @) or user ID
        
    Returns:
        Dictionary with user information or None if user not found
    """
    try:
        # Handle username format
        if isinstance(identifier, str):
            # Remove @ if present
            if identifier.startswith('@'):
                identifier = identifier[1:]
        
        # Get the user entity
        user = await client.get_entity(identifier)
        
        # Create a dictionary with user information
        user_info = {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': getattr(user, 'phone', None),
            'bot': getattr(user, 'bot', False),
            'verified': getattr(user, 'verified', False),
            'restricted': getattr(user, 'restricted', False),
            'scam': getattr(user, 'scam', False),
            'fake': getattr(user, 'fake', False),
        }
        
        return user_info
    except ValueError:
        # User not found
        return None
    except Exception as e:
        print(f"Error retrieving user information: {str(e)}")
        return None