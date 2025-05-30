#!/usr/bin/env python3
"""
Test script to get Telegram user information by ID using Telethon.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import from the project
from src.config.settings import settings
from telethon import TelegramClient


async def get_user_info_by_id(client, user_id):
    """Get user information by ID"""
    try:
        # Get the user entity from their ID
        user = await client.get_entity(user_id)
        
        # Print user information
        print("\n===== User Information =====")
        print(f"ID: {user.id}")
        print(f"Username: {f'@{user.username}' if user.username else 'No username'}")
        print(f"First Name: {user.first_name or 'Not set'}")
        print(f"Last Name: {user.last_name or 'Not set'}")
        print(f"Phone: {user.phone if hasattr(user, 'phone') else 'Not available'}")
        print(f"Bot: {'Yes' if user.bot else 'No'}")
        print(f"Verified: {'Yes' if hasattr(user, 'verified') and user.verified else 'No'}")
        print(f"Restricted: {'Yes' if hasattr(user, 'restricted') and user.restricted else 'No'}")
        print(f"Scam: {'Yes' if hasattr(user, 'scam') and user.scam else 'No'}")
        print(f"Fake: {'Yes' if hasattr(user, 'fake') and user.fake else 'No'}")
        print("============================\n")
        
        return user
    except ValueError as e:
        print(f"Error: User with ID {user_id} not found")
        print(f"Details: {str(e)}")
        return None
    except Exception as e:
        print(f"Error retrieving user information: {str(e)}")
        return None


async def main():
    # Get API credentials from settings
    api_id = settings.API_ID
    api_hash = settings.API_HASH
    bot_token = settings.BOT_TOKEN
    
    print(f"Initializing Telethon client...")
    client = TelegramClient('test_session', api_id, api_hash)
    
    try:
        print(f"Starting client session...")
        await client.start(bot_token=bot_token)
        
        # Test with the provided user ID
        test_user_id = 6341595731
        print(f"Fetching information for user ID: {test_user_id}")
        
        user = await get_user_info_by_id(client, test_user_id)
        
        # You can add more test IDs here
        # For example:
        # await get_user_info_by_id(client, 123456789)
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        print("Disconnecting client...")
        await client.disconnect()
        print("Done.")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())