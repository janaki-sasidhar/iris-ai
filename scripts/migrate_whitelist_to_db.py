#!/usr/bin/env python3
"""
Migration script to transfer whitelist from JSON to database
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager
from src.database.models import Base, Whitelist
from src.config.settings import settings


async def migrate_whitelist():
    """Migrate whitelist from JSON file to database"""
    print("🔄 Starting whitelist migration...")
    
    # Check if whitelist.json exists
    whitelist_file = Path("whitelist.json")
    if not whitelist_file.exists():
        print("❌ whitelist.json not found. Nothing to migrate.")
        return
    
    # Load existing whitelist
    try:
        with open(whitelist_file, 'r') as f:
            whitelist_data = json.load(f)
        print(f"✅ Loaded whitelist.json: {whitelist_data}")
    except Exception as e:
        print(f"❌ Error loading whitelist.json: {e}")
        return
    
    # Initialize database
    db_manager = DatabaseManager()
    await db_manager.init()
    print("✅ Database initialized")
    
    # Get authorized users and comments
    authorized_users = whitelist_data.get("authorized_users", [])
    comments = whitelist_data.get("comments", {})
    
    # Migrate each user
    migrated_count = 0
    skipped_count = 0
    
    for user_id in authorized_users:
        # Skip the superadmin (hardcoded in the system)
        if user_id == 7276342619:
            print(f"⏭️  Skipping superadmin {user_id} (hardcoded)")
            skipped_count += 1
            continue
        
        # Check if already exists
        is_existing = await db_manager.is_user_whitelisted(user_id)
        if is_existing:
            print(f"⏭️  User {user_id} already in database whitelist")
            skipped_count += 1
            continue
        
        # Add to database
        comment = comments.get(str(user_id), "Migrated from whitelist.json")
        success = await db_manager.add_to_whitelist(
            telegram_id=user_id,
            comment=comment
        )
        
        if success:
            print(f"✅ Migrated user {user_id} with comment: {comment}")
            migrated_count += 1
        else:
            print(f"❌ Failed to migrate user {user_id}")
    
    # Close database
    await db_manager.close()
    
    print(f"\n📊 Migration Summary:")
    print(f"   Total users in JSON: {len(authorized_users)}")
    print(f"   Successfully migrated: {migrated_count}")
    print(f"   Skipped (already exists or superadmin): {skipped_count}")
    
    if migrated_count > 0:
        print(f"\n✅ Migration completed successfully!")
        print(f"ℹ️  You can now safely delete or rename whitelist.json")
        
        # Optionally rename the file
        backup_name = f"whitelist.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            whitelist_file.rename(backup_name)
            print(f"✅ Renamed whitelist.json to {backup_name}")
        except Exception as e:
            print(f"⚠️  Could not rename file: {e}")
            print("   Please manually delete or rename whitelist.json")
    else:
        print(f"\nℹ️  No users were migrated.")


if __name__ == "__main__":
    asyncio.run(migrate_whitelist())