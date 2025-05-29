#!/usr/bin/env python3
"""
Migration script to add web_search_mode column to users table
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path: str):
    """Add web_search_mode column to users table if it doesn't exist"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'web_search_mode' not in columns:
            print(f"Adding web_search_mode column to {db_path}...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN web_search_mode INTEGER DEFAULT 0
            """)
            conn.commit()
            print("✅ Migration completed successfully!")
        else:
            print("ℹ️  web_search_mode column already exists, skipping migration.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Default database path
    db_path = "bot_database.db"
    
    # Check if custom path provided
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # Check if database exists
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        print("Usage: python add_web_search_column.py [database_path]")
        sys.exit(1)
    
    migrate_database(db_path)