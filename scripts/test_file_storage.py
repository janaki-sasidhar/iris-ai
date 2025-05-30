#!/usr/bin/env python3
"""
Test script to verify the file storage system is working correctly
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.storage import ensure_storage_dirs, STORAGE_DIRS
from src.utils.file_handler import file_handler


async def test_file_storage():
    """Test the file storage system"""
    print("Testing File Storage System")
    print("=" * 50)
    
    # Test 1: Ensure directories exist
    print("\n1. Testing directory creation...")
    ensure_storage_dirs()
    
    for name, path in STORAGE_DIRS.items():
        if path.exists():
            print(f"   ✓ {name}: {path}")
        else:
            print(f"   ✗ {name}: {path} (MISSING)")
    
    # Test 2: Test saving a user image
    print("\n2. Testing user image save...")
    test_image_data = b"Test image data"
    
    try:
        image_path = await file_handler.save_user_image(test_image_data, "image/jpeg")
        print(f"   ✓ Saved user image to: {image_path}")
        
        # Verify file exists
        if os.path.exists(image_path):
            print(f"   ✓ File exists at path")
        else:
            print(f"   ✗ File not found at path")
    except Exception as e:
        print(f"   ✗ Error saving user image: {e}")
    
    # Test 3: Test reading image
    print("\n3. Testing image read...")
    try:
        read_data = await file_handler.get_image_bytes(image_path)
        if read_data == test_image_data:
            print(f"   ✓ Image data matches")
        else:
            print(f"   ✗ Image data mismatch")
    except Exception as e:
        print(f"   ✗ Error reading image: {e}")
    
    # Test 4: Test base64 conversion
    print("\n4. Testing base64 conversion...")
    try:
        base64_data = await file_handler.get_image_base64(image_path)
        if base64_data:
            print(f"   ✓ Base64 conversion successful")
            print(f"   Base64 preview: {base64_data[:50]}...")
        else:
            print(f"   ✗ Base64 conversion failed")
    except Exception as e:
        print(f"   ✗ Error converting to base64: {e}")
    
    # Test 5: Test generated image save (cross-device move)
    print("\n5. Testing generated image save (cross-device move)...")
    # Create a temp file in /tmp to simulate cross-device scenario
    import tempfile
    temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg', prefix='test_generated_')
    with os.fdopen(temp_fd, 'wb') as f:
        f.write(b"Generated image data")
    print(f"   Created temp file at: {temp_path}")
    
    try:
        perm_path = await file_handler.save_generated_image(temp_path)
        print(f"   ✓ Moved generated image to: {perm_path}")
        
        if os.path.exists(perm_path):
            print(f"   ✓ File exists at permanent location")
        else:
            print(f"   ✗ File not found at permanent location")
            
        if not os.path.exists(temp_path):
            print(f"   ✓ Temp file was moved (not copied)")
        else:
            print(f"   ✗ Temp file still exists")
    except Exception as e:
        print(f"   ✗ Error saving generated image: {e}")
    
    # Test 6: Test file deletion
    print("\n6. Testing file deletion...")
    try:
        # Clean up test files
        if file_handler.delete_image(image_path):
            print(f"   ✓ Deleted user image")
        else:
            print(f"   ✗ Failed to delete user image")
            
        if 'perm_path' in locals() and file_handler.delete_image(perm_path):
            print(f"   ✓ Deleted generated image")
        else:
            print(f"   ✗ Failed to delete generated image")
    except Exception as e:
        print(f"   ✗ Error deleting files: {e}")
    
    print("\n" + "=" * 50)
    print("File storage system test complete!")


if __name__ == "__main__":
    asyncio.run(test_file_storage())
