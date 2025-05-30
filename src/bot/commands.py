"""Command handlers for the bot"""

from telethon import events
import base64
import re

from .decorators import require_authorization, require_superadmin
from ..database import DatabaseManager
from ..config.settings import settings
from ..utils import MessageSplitter


class CommandHandler:
    """Handles bot commands"""
    
    def __init__(self, client, db_manager: DatabaseManager, whitelist_manager=None):
        self.client = client
        self.db_manager = db_manager
        self.whitelist_manager = whitelist_manager
    
    @require_authorization
    async def handle_start(self, event):
        """Handle /start command"""
        user = await event.get_sender()
        
        # Get or create user in database
        db_user = await self.db_manager.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Create new conversation (same as /newchat)
        await self.db_manager.create_conversation(db_user.id)
        
        welcome_message = (
            "👋 Welcome to the AI Assistant Bot!\n\n"
            "🆕 A fresh conversation has been started!\n\n"
            "Available commands:\n"
            "• /newchat - Start a new conversation\n"
            "• /settings - Configure bot settings\n"
            "• /userinfo @username - Get user information\n"
            "• /help - Show available commands\n\n"
            "You can send me text messages or images with questions, "
            "and I'll respond using the context of our conversation."
        )
        
        await event.reply(welcome_message)
    
    @require_authorization
    async def handle_newchat(self, event):
        """Handle /newchat command"""
        user = await event.get_sender()
        
        # Get user from database
        db_user = await self.db_manager.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Create new conversation
        new_conversation = await self.db_manager.create_conversation(db_user.id)
        
        await event.reply(
            f"🆕 **New conversation started!**\n\n"
            f"**Conversation ID: {new_conversation.id}**\n\n"
            "Previous context has been cleared. "
            "Feel free to ask me anything!",
            parse_mode='markdown'
        )
    
    @require_authorization
    async def handle_help(self, event):
        """Handle /help command"""
        user = await event.get_sender()
        is_superadmin = self.whitelist_manager.is_superadmin(user.id) if self.whitelist_manager else False
        
        help_message = (
            "📚 **Bot Commands:**\n\n"
            "• `/start` - Initialize the bot\n"
            "• `/newchat` - Start a new conversation\n"
            "• `/settings` - Configure AI settings\n"
            "• `/userinfo @username` - Get user information\n"
            "• `/help` - Show this help message\n\n"
        )
        
        # Add superadmin commands if applicable
        if is_superadmin:
            help_message += (
                "**Superadmin Commands:**\n"
                "• `/whitelist` - Show all whitelisted users\n"
                "• `/allow @username` or `/allow id::123456789` - Add user to whitelist\n"
                "• `/deny @username` or `/deny id::123456789` - Remove user from whitelist\n\n"
            )
        
        help_message += (
            "**Other Features:**\n"
            "• Send text messages for AI responses\n"
            "• Attach images with your questions\n"
            "• `!ping` - Test bot connectivity\n\n"
            "**Current Settings:**\n"
            "• Model: Gemini Flash/Pro (configurable)\n"
            "• Context is maintained across messages\n"
            "• Only whitelisted users can interact"
        )
        
        await event.reply(help_message, parse_mode='markdown')
    
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
        
        try:
            
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
                
        except Exception as e:
            await event.reply(
                f"❌ **Error**: {str(e)}",
                parse_mode='markdown'
            )
    
    @require_superadmin
    async def handle_whitelist_info(self, event):
        """Handle /whitelist command - shows current whitelist info (superadmin only)"""
        user = await event.get_sender()
        
        # Get whitelist info
        whitelist_info = await self.whitelist_manager.get_whitelist_info()
        authorized_users = whitelist_info['authorized_users']
        
        message = (
            f"🔍 **Whitelist Info**\n\n"
            f"Total whitelisted users: {len(authorized_users)}\n\n"
            f"**Whitelisted Users:**\n"
        )
        
        for entry in whitelist_info['details']:
            user_line = f"• `{entry['telegram_id']}`"
            
            # Add name if available
            name_parts = []
            if entry.get('first_name'):
                name_parts.append(entry['first_name'])
            if entry.get('last_name'):
                name_parts.append(entry['last_name'])
            if name_parts:
                user_line += f" - {' '.join(name_parts)}"
            
            if entry['username']:
                user_line += f" (@{entry['username']})"
            if entry['comment']:
                user_line += f" - {entry['comment']}"
            message += user_line + "\n"
        
        await event.reply(message, parse_mode='markdown')
    
    @require_authorization
    async def handle_userinfo(self, event):
        """Handle /userinfo command - get info about a user"""
        # Extract username from message
        message_text = event.message.message.strip()
        parts = message_text.split(maxsplit=1)
        
        if len(parts) < 2:
            await event.reply(
                "❌ **Usage**: `/userinfo @username`\n"
                "Example: `/userinfo @durov`",
                parse_mode='markdown'
            )
            return
        
        username = parts[1].strip()
        # Remove @ if present
        if username.startswith('@'):
            username = username[1:]
        
        try:
            # Get user entity
            user = await self.client.get_entity(username)
            
            # Build user info message
            info_lines = [
                f"👤 **User Information**\n",
                f"**Name**: {user.first_name or 'N/A'} {user.last_name or ''}".strip(),
                f"**Username**: @{user.username}" if user.username else "**Username**: Not set",
                f"**User ID**: `{user.id}`",
                f"**Bot**: {'Yes 🤖' if user.bot else 'No 👤'}",
            ]
            
            # Add additional info if available
            if hasattr(user, 'verified') and user.verified:
                info_lines.append(f"**Verified**: ✅ Yes")
            
            if hasattr(user, 'restricted') and user.restricted:
                info_lines.append(f"**Restricted**: ⚠️ Yes")
            
            if hasattr(user, 'scam') and user.scam:
                info_lines.append(f"**Scam**: 🚫 Yes")
            
            if hasattr(user, 'fake') and user.fake:
                info_lines.append(f"**Fake**: ⚠️ Yes")
            
            # Check if user is in our database
            try:
                db_user = await self.db_manager.get_or_create_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                info_lines.append(f"\n**In Bot Database**: ✅ Yes")
                
                # Get user settings if they exist
                settings = await self.db_manager.get_user_settings(db_user.id)
                info_lines.append(f"**Bot Settings**:")
                info_lines.append(f"  • Model: {settings['model']}")
                info_lines.append(f"  • Max Tokens: {settings['max_tokens']}")
                info_lines.append(f"  • Temperature: {settings['temperature']}")
            except:
                info_lines.append(f"\n**In Bot Database**: ❌ No")
            
            # Check authorization
            authorized_users = whitelist_manager.get_authorized_users()
            is_authorized = user.id in authorized_users
            info_lines.append(f"\n**Bot Access**: {'✅ Authorized' if is_authorized else '❌ Not Authorized'}")
            
            await event.reply('\n'.join(info_lines), parse_mode='markdown')
            
        except ValueError:
            await event.reply(
                f"❌ **Error**: User `@{username}` not found.\n"
                "Make sure the username is correct.",
                parse_mode='markdown'
            )
        except Exception as e:
            await event.reply(
                f"❌ **Error**: {str(e)}",
                parse_mode='markdown'
            )
    
    def register_handlers(self):
        """Register all command handlers"""
        self.client.add_event_handler(
            self.handle_start,
            events.NewMessage(pattern='/start')
        )
        
        self.client.add_event_handler(
            self.handle_newchat,
            events.NewMessage(pattern='/newchat')
        )
        
        self.client.add_event_handler(
            self.handle_help,
            events.NewMessage(pattern='/help')
        )
        
        self.client.add_event_handler(
            self.handle_whitelist_info,
            events.NewMessage(pattern='/whitelist')
        )
        
        self.client.add_event_handler(
            self.handle_userinfo,
            events.NewMessage(pattern='/userinfo')
        )
        
        # Add new handlers for /allow and /deny commands
        self.client.add_event_handler(
            self.handle_allow,
            events.NewMessage(pattern='/allow')
        )
        
        self.client.add_event_handler(
            self.handle_deny,
            events.NewMessage(pattern='/deny')
        )