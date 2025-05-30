"""Storage configuration for file handling"""

import os
from pathlib import Path

# Base directory for all stored files
# Use home directory for better compatibility with WSL and development environments
STORAGE_BASE_DIR = Path.home() / ".telethon-bot-storage"

# Subdirectories for different file types
STORAGE_DIRS = {
    "user_images": STORAGE_BASE_DIR / "user_images",
    "generated_images": STORAGE_BASE_DIR / "generated_images",
    "temp": STORAGE_BASE_DIR / "temp"
}

# Ensure all directories exist
def ensure_storage_dirs():
    """Create storage directories if they don't exist"""
    for dir_path in STORAGE_DIRS.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        # Set appropriate permissions
        os.chmod(dir_path, 0o755)

# File naming settings
FILE_EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp"
}

DEFAULT_IMAGE_EXTENSION = ".jpg"