#!/usr/bin/env python3
"""
Test script to demonstrate adding a user to whitelist by ID.
This shows how the /allow command could be modified to accept IDs.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import from the project
from src.config.settings import settings
from telethon import TelegramClient, events
from src.utils.user_info import get_user_by_username_or_id


async def handle_allow_command(client, whitelist_manager, identifier, added_by=None):
    """
    Handle /allow command with support for both username and ID
    
    Args:
        client: Telethon client
        whitelist_manager: Whitelist manager instance
        identifier: Username or user ID
        added_by: ID of the user who added this user
    """
    try:
        # Check if identifier is a user ID (integer)
        if isinstance(identifier, str) and identifier.isdigit():
            identifier = int(identifier)
        
        # Get user information
        print(f"Getting user info for: {identifier}")
        user_info = await get_user_by_username_or_id(client, identifier)
        
        if not user_info:
            print(f"❌ User not found: {identifier}")
            return False
        
        # Print user information
        print("\n===== User Information =====")
        print(f"ID: {user_info['id']}")
        print(f"Username: {f'@{user_info['username']}' if user_info['username'] else 'No username'}")
        print(f"Name: {user_info['first_name'] or ''} {user_info['last_name'] or ''}")
        print("============================\n")
        
        # Add to whitelist (simulated)
        print(f"✅ User would be added to whitelist: {user_info['id']}")
        
        # In a real implementation, you would call:
        # success = await whitelist_manager.add_user(
        #     telegram_id=user_info['id'],
        #     username=user_info['username'],
        #     first_name=user_info['first_name'],
        #     last_name=user_info['last_name'],
        #     added_by=added_by,
        #     comment=f"Added by superadmin"
        # )
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


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
        print(f"\nTesting with user ID: {test_user_id}")
        await handle_allow_command(client, None, test_user_id)
        
        # Test with a username (if you want to test)
        # test_username = "example_user"
        # print(f"\nTesting with username: {test_username}")
        # await handle_allow_command(client, None, test_username)
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        print("Disconnecting client...")
        await client.disconnect()
        print("Done.")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())