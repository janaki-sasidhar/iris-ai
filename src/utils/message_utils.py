"""Utilities for message handling"""

from typing import List, Tuple
from ..config.settings import settings


class MessageSplitter:
    """Handles splitting long messages for Telegram"""
    
    @staticmethod
    async def send_long_message(event, text: str, parse_mode: str = 'markdown'):
        """Send a long message, splitting if necessary
        
        Args:
            event: Telethon event object
            text: Message text to send
            parse_mode: Parse mode for formatting
        """
        max_length = settings.MAX_MESSAGE_LENGTH
        
        if len(text) <= max_length:
            # Message fits in one part
            await event.reply(text, parse_mode=parse_mode)
        else:
            # Split message into parts
            parts = MessageSplitter._split_message(text, max_length)
            
            # Send all parts
            for i, part in enumerate(parts):
                if i == 0:
                    # First part as reply
                    await event.reply(f"{part}\n\n_(Part {i+1}/{len(parts)})_", parse_mode=parse_mode)
                else:
                    # Subsequent parts as regular messages
                    await event.respond(f"{part}\n\n_(Part {i+1}/{len(parts)})_", parse_mode=parse_mode)
    
    @staticmethod
    def _split_message(text: str, max_length: int) -> List[str]:
        """Split a message into parts
        
        Args:
            text: Text to split
            max_length: Maximum length per part
            
        Returns:
            List of message parts
        """
        parts = []
        current_part = ""
        
        # Split by lines to avoid breaking markdown
        lines = text.split('\n')
        
        for line in lines:
            if len(current_part) + len(line) + 1 > max_length:
                # Current part is full, save it and start new
                if current_part:
                    parts.append(current_part)
                current_part = line
            else:
                # Add line to current part
                if current_part:
                    current_part += '\n' + line
                else:
                    current_part = line
        
        # Add the last part
        if current_part:
            parts.append(current_part)
        
        return parts