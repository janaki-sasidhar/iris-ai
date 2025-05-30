"""
Modified version of the /allow and /deny command handlers to support the id::<number> format.
This is a reference implementation that can be integrated into src/bot/commands.py
"""

from telethon import events
import re


@require_superadmin
async def handle_allow(self, event):
    """Handle /allow command - add user to whitelist by username or id::<number>"""
    # Extract identifier from message
    message_text = event.message.message.strip()
    parts = message_text.split(maxsplit=1)
    
    if len(parts) < 2:
        await event.reply(
            "❌ **Usage**:\n"
            "• `/allow @username` - Add user by username\n"
            "• `/allow id::123456789` - Add user by ID",
            parse_mode='markdown'
        )
        return
    
    identifier = parts[1].strip()
    
    # Check if using the id::<number> format
    id_match = re.match(r'id::(\d+)', identifier)
    if id_match:
        # Extract the user ID
        user_id = int(id_match.group(1))
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


@require_superadmin
async def handle_deny(self, event):
    """Handle /deny command - remove user from whitelist by username or id::<number>"""
    # Extract identifier from message
    message_text = event.message.message.strip()
    parts = message_text.split(maxsplit=1)
    
    if len(parts) < 2:
        await event.reply(
            "❌ **Usage**:\n"
            "• `/deny @username` - Remove user by username\n"
            "• `/deny id::123456789` - Remove user by ID",
            parse_mode='markdown'
        )
        return
    
    identifier = parts[1].strip()
    
    # Check if using the id::<number> format
    id_match = re.match(r'id::(\d+)', identifier)
    if id_match:
        # Extract the user ID
        user_id = int(id_match.group(1))
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
    
    # Check if trying to remove superadmin
    if self.whitelist_manager.is_superadmin(target_user.id):
        await event.reply(
            f"❌ **Cannot Remove Superadmin**\n\n"
            f"The superadmin (ID: `{target_user.id}`) cannot be removed from the system.\n"
            f"This is a safety feature to prevent lockout.",
            parse_mode='markdown'
        )
        return
    
    # Check if user is in whitelist
    is_authorized = await self.whitelist_manager.is_authorized(target_user.id)
    
    if not is_authorized:
        await event.reply(
            f"ℹ️ User {f'@{target_user.username}' if target_user.username else f'ID: {target_user.id}'} "
            f"is not in the whitelist.",
            parse_mode='markdown'
        )
        return
    
    # Remove from whitelist
    success = await self.whitelist_manager.remove_user(target_user.id)
    
    if success:
        await event.reply(
            f"✅ **User Removed from Whitelist**\n\n"
            f"**Name**: {target_user.first_name or 'N/A'} {target_user.last_name or ''}".strip() + "\n"
            f"**Username**: {f'@{target_user.username}' if target_user.username else 'No username'}\n"
            f"**User ID**: `{target_user.id}`",
            parse_mode='markdown'
        )
    else:
        await event.reply(
            f"❌ Failed to remove user from whitelist.",
            parse_mode='markdown'
        )