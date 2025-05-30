"""File handling utilities for storing and retrieving images"""

import os
import uuid
import base64
import shutil
from pathlib import Path
from typing import Optional, Tuple
import aiofiles
import mimetypes
from PIL import Image
import io

from ..config.storage import (
    STORAGE_DIRS,
    FILE_EXTENSION_MAP,
    DEFAULT_IMAGE_EXTENSION,
    ensure_storage_dirs
)


class FileHandler:
    """Handles file storage operations"""
    
    def __init__(self):
        # Ensure storage directories exist
        ensure_storage_dirs()
    
    async def save_user_image(self, image_bytes: bytes, mime_type: Optional[str] = None) -> str:
        """
        Save user uploaded image to disk
        
        Args:
            image_bytes: Raw image bytes
            mime_type: MIME type of the image
            
        Returns:
            Path to the saved file
        """
        # Generate unique filename
        file_id = str(uuid.uuid4())
        extension = FILE_EXTENSION_MAP.get(mime_type, DEFAULT_IMAGE_EXTENSION)
        filename = f"{file_id}{extension}"
        
        # Full path for the file
        file_path = STORAGE_DIRS["user_images"] / filename
        
        # Save file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(image_bytes)
        
        return str(file_path)
    
    async def save_generated_image(self, source_path: str) -> str:
        """
        Move generated image from temp location to permanent storage
        
        Args:
            source_path: Current path of the generated image
            
        Returns:
            New path in permanent storage
        """
        # Generate unique filename
        file_id = str(uuid.uuid4())
        extension = Path(source_path).suffix or DEFAULT_IMAGE_EXTENSION
        filename = f"{file_id}{extension}"
        
        # Destination path
        dest_path = STORAGE_DIRS["generated_images"] / filename
        
        # Move file to permanent storage
        # Use shutil.move instead of os.rename to handle cross-device moves
        shutil.move(source_path, str(dest_path))
        
        return str(dest_path)
    
    async def get_image_bytes(self, file_path: str) -> Optional[bytes]:
        """
        Read image bytes from file path
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Image bytes or None if file doesn't exist
        """
        if not os.path.exists(file_path):
            return None
        
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    async def get_image_base64(self, file_path: str) -> Optional[str]:
        """
        Read image and return as base64 string
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Base64 encoded image or None if file doesn't exist
        """
        image_bytes = await self.get_image_bytes(file_path)
        if image_bytes:
            return base64.b64encode(image_bytes).decode('utf-8')
        return None
    
    def delete_image(self, file_path: str) -> bool:
        """
        Delete an image file
        
        Args:
            file_path: Path to the image file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
        return False
    
    def get_mime_type(self, file_path: str) -> str:
        """
        Get MIME type of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"


# Global instance
file_handler = FileHandler()