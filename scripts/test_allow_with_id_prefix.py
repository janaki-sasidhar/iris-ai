#!/usr/bin/env python3
"""
Test script to demonstrate adding a user to whitelist using the id::<number> format.
"""

import asyncio
import sys
import re
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import from the project
from src.config.settings import settings
from telethon import TelegramClient, events


async def handle_allow_command(client, whitelist_manager, command_text, added_by=None):
    """
    Handle /allow command with support for id::<number> format
    
    Args:
        client: Telethon client
        whitelist_manager: Whitelist manager instance
        command_text: Full command text (e.g., "/allow @username" or "/allow id::123456789")
        added_by: ID of the user who added this user
    """
    try:
        # Extract identifier from command
        parts = command_text.split(maxsplit=1)
        
        if len(parts) < 2:
            print("❌ Usage:")
            print("• /allow @username - Add user by username")
            print("• /allow id::123456789 - Add user by ID")
            return False
        
        identifier = parts[1].strip()
        
        # Check if using the id::<number> format
        id_match = re.match(r'id::(\d+)', identifier)
        if id_match:
            # Extract the user ID
            user_id = int(id_match.group(1))
            print(f"Detected ID format: {user_id}")
            
            try:
                # Get user entity directly by ID
                target_user = await client.get_entity(user_id)
            except ValueError:
                print(f"❌ Error: User with ID {user_id} not found.")
                print("Make sure the ID is correct.")
                return False
        else:
            # Handle as username
            # Remove @ if present
            if identifier.startswith('@'):
                identifier = identifier[1:]
            
            print(f"Detected username format: {identifier}")
            
            try:
                # Get user entity by username
                target_user = await client.get_entity(identifier)
            except ValueError:
                print(f"❌ Error: User @{identifier} not found.")
                print("Make sure the username is correct.")
                return False
        
        # Print user information
        print("\n===== User Information =====")
        print(f"ID: {target_user.id}")
        print(f"Username: {f'@{target_user.username}' if target_user.username else 'No username'}")
        print(f"Name: {target_user.first_name or ''} {target_user.last_name or ''}")
        print("============================\n")
        
        # Add to whitelist (simulated)
        print(f"✅ User would be added to whitelist: {target_user.id}")
        
        # In a real implementation, you would call:
        # success = await whitelist_manager.add_user(
        #     telegram_id=target_user.id,
        #     username=target_user.username,
        #     first_name=target_user.first_name,
        #     last_name=target_user.last_name,
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
        
        # Test with the provided user ID using id:: format
        test_user_id = 6341595731
        print(f"\nTesting with id:: format: id::{test_user_id}")
        await handle_allow_command(client, None, f"/allow id::{test_user_id}")
        
        # Test with a username (if you want to test)
        test_username = "durov"  # Example: Pavel Durov's username
        print(f"\nTesting with username format: @{test_username}")
        await handle_allow_command(client, None, f"/allow @{test_username}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        print("Disconnecting client...")
        await client.disconnect()
        print("Done.")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())