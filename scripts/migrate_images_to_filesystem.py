#!/usr/bin/env python3
"""
Migration script to convert base64 image data to filesystem storage
This script will:
1. Read all messages with image_data from the database
2. Save the images to the filesystem
3. Update the database to use image_path instead
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.config.settings import settings
from src.config.storage import ensure_storage_dirs
from src.utils.file_handler import file_handler


async def migrate_images():
    """Migrate images from database to filesystem"""
    print("Starting image migration...")
    
    # Ensure storage directories exist
    ensure_storage_dirs()
    
    # Create database connection
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # First, check if the old column exists
            result = await session.execute(
                text("PRAGMA table_info(messages)")
            )
            columns = [row[1] for row in result.fetchall()]
            
            if 'image_data' not in columns:
                print("No image_data column found. Migration may have already been completed.")
                return
            
            # Add new column if it doesn't exist
            if 'image_path' not in columns:
                print("Adding image_path column...")
                await session.execute(
                    text("ALTER TABLE messages ADD COLUMN image_path VARCHAR(500)")
                )
                await session.commit()
            
            # Get all messages with image data
            result = await session.execute(
                text("SELECT id, image_data FROM messages WHERE image_data IS NOT NULL")
            )
            messages_with_images = result.fetchall()
            
            print(f"Found {len(messages_with_images)} messages with images to migrate")
            
            # Migrate each image
            migrated_count = 0
            for message_id, image_data_base64 in messages_with_images:
                try:
                    # Decode base64 image
                    image_bytes = base64.b64decode(image_data_base64)
                    
                    # Save to filesystem
                    image_path = await file_handler.save_user_image(
                        image_bytes, 
                        mime_type="image/jpeg"  # Default to JPEG
                    )
                    
                    # Update database with new path
                    await session.execute(
                        text("UPDATE messages SET image_path = :path WHERE id = :id"),
                        {"path": image_path, "id": message_id}
                    )
                    
                    migrated_count += 1
                    if migrated_count % 10 == 0:
                        print(f"Migrated {migrated_count} images...")
                        await session.commit()
                    
                except Exception as e:
                    print(f"Error migrating image for message {message_id}: {e}")
                    continue
            
            # Final commit
            await session.commit()
            print(f"Successfully migrated {migrated_count} images")
            
            # Optional: Drop the old column after successful migration
            print("\nMigration complete!")
            print("To remove the old image_data column, run:")
            print("  ALTER TABLE messages DROP COLUMN image_data;")
            print("\nNote: Only do this after verifying all images were migrated successfully!")
            
    finally:
        await engine.dispose()


async def verify_migration():
    """Verify that migration was successful"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Count messages with image_path
            result = await session.execute(
                text("SELECT COUNT(*) FROM messages WHERE image_path IS NOT NULL")
            )
            path_count = result.scalar()
            
            # Count messages with image_data (if column still exists)
            try:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM messages WHERE image_data IS NOT NULL")
                )
                data_count = result.scalar()
                print(f"\nVerification:")
                print(f"Messages with image_path: {path_count}")
                print(f"Messages with image_data: {data_count}")
                
                if data_count > 0 and path_count == data_count:
                    print("✓ All images appear to have been migrated successfully!")
                elif data_count > path_count:
                    print(f"⚠ Warning: {data_count - path_count} images may not have been migrated")
            except:
                print(f"\nMessages with image_path: {path_count}")
                print("image_data column has been removed")
                
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("Image Migration Script")
    print("=" * 50)
    print("This script will migrate base64 image data from the database")
    print("to the local filesystem.")
    print()
    
    response = input("Do you want to proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        sys.exit(0)
    
    # Run migration
    asyncio.run(migrate_images())
    
    # Verify migration
    asyncio.run(verify_migration())