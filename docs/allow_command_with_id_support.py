"""
Modified version of the /allow command handler to support both usernames and user IDs.
This is a reference implementation that can be integrated into src/bot/commands.py
"""

from telethon import events
from ..utils.user_info import get_user_by_username_or_id


@require_superadmin
async def handle_allow(self, event):
    """Handle /allow command - add user to whitelist by username or ID"""
    # Extract username or ID from message
    message_text = event.message.message.strip()
    parts = message_text.split(maxsplit=1)
    
    if len(parts) < 2:
        await event.reply(
            "❌ **Usage**: `/allow @username` or `/allow 123456789`\n"
            "Examples:\n"
            "• `/allow @durov`\n"
            "• `/allow 123456789`",
            parse_mode='markdown'
        )
        return
    
    identifier = parts[1].strip()
    
    # Check if identifier is a user ID (integer)
    if identifier.isdigit():
        user_id = int(identifier)
        try:
            # Get user entity directly by ID
            target_user = await self.client.get_entity(user_id)
        except ValueError:
            await event.reply(
                f"❌ **Error**: User with ID `{user_id}` not found.\n"
                "Make sure the ID is correct.",
                parse_mode='markdown'
            )
            return
        except Exception as e:
            await event.reply(
                f"❌ **Error**: {str(e)}",
                parse_mode='markdown'
            )
            return
    else:
        # Handle as username
        # Remove @ if present
        if identifier.startswith('@'):
            identifier = identifier[1:]
        
        try:
            # Get user entity by username
            target_user = await self.client.get_entity(identifier)
        except ValueError:
            await event.reply(
                f"❌ **Error**: User `@{identifier}` not found.\n"
                "Make sure the username is correct.",
                parse_mode='markdown'
            )
            return
        except Exception as e:
            await event.reply(
                f"❌ **Error**: {str(e)}",
                parse_mode='markdown'
            )
            return
    
    try:
        # Add to whitelist
        success = await self.whitelist_manager.add_user(
            telegram_id=target_user.id,
            username=target_user.username,
            first_name=target_user.first_name,
            last_name=target_user.last_name,
            added_by=event.sender_id,
            comment=f"Added by superadmin"
        )
        
        # Also ensure user is in the users table with updated info
        await self.db_manager.get_or_create_user(
            telegram_id=target_user.id,
            username=target_user.username,
            first_name=target_user.first_name,
            last_name=target_user.last_name
        )
        
        if success:
            await event.reply(
                f"✅ **User Added to Whitelist**\n\n"
                f"**Name**: {target_user.first_name or 'N/A'} {target_user.last_name or ''}".strip() + "\n"
                f"**Username**: {f'@{target_user.username}' if target_user.username else 'No username'}\n"
                f"**User ID**: `{target_user.id}`",
                parse_mode='markdown'
            )
        else:
            await event.reply(
                f"ℹ️ User {f'@{target_user.username}' if target_user.username else f'ID: {target_user.id}'} "
                f"is already in the whitelist.",
                parse_mode='markdown'
            )
            
    except Exception as e:
        await event.reply(
            f"❌ **Error**: {str(e)}",
            parse_mode='markdown'
        )