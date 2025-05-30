#!/usr/bin/env python3
"""
Test script to verify graceful handling of missing image files
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.file_handler import file_handler


async def test_missing_file_handling():
    """Test how the system handles missing files"""
    print("Testing Missing File Handling")
    print("=" * 50)
    
    # Test 1: Try to read a non-existent file
    print("\n1. Testing get_image_bytes with missing file...")
    fake_path = "/path/that/does/not/exist.jpg"
    
    result = await file_handler.get_image_bytes(fake_path)
    if result is None:
        print("   ✓ Correctly returned None for missing file")
    else:
        print("   ✗ Should have returned None but got data")
    
    # Test 2: Try to get base64 of non-existent file
    print("\n2. Testing get_image_base64 with missing file...")
    
    result = await file_handler.get_image_base64(fake_path)
    if result is None:
        print("   ✓ Correctly returned None for missing file")
    else:
        print("   ✗ Should have returned None but got data")
    
    # Test 3: Simulate database manager behavior
    print("\n3. Simulating database manager behavior...")
    
    # Simulate a message with missing image
    message = {
        "role": "user",
        "content": "Hello, here was an image"
    }
    
    # Simulate the database manager logic
    image_path = fake_path
    if image_path:
        image_base64 = await file_handler.get_image_base64(image_path)
        if image_base64:
            message["image_data"] = image_base64
            print("   ✗ Image data was added (shouldn't happen)")
        else:
            print("   ✓ Image data was NOT added (correct behavior)")
    
    print(f"\n4. Final message structure:")
    print(f"   Role: {message['role']}")
    print(f"   Content: {message['content']}")
    print(f"   Has image_data: {'image_data' in message}")
    
    if 'image_data' not in message:
        print("\n   ✓ SUCCESS: Message will be sent to LLM without image data")
    else:
        print("\n   ✗ FAILURE: Message incorrectly includes image data")
    
    print("\n" + "=" * 50)
    print("Missing file handling test complete!")
    print("\nConclusion: The system gracefully handles missing files by:")
    print("- Returning None when files don't exist")
    print("- Not including image_data in messages when files are missing")
    print("- Still including the text content of messages in conversations")


if __name__ == "__main__":
    asyncio.run(test_missing_file_handling())