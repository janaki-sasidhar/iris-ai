# Whitelist Database Migration Documentation

## Overview

This document describes the migration from JSON-based whitelist management to a database-based system using SQLite with Alembic for migrations.

## Key Changes

### 1. Database Schema

Added a new `whitelist` table with the following structure:

```sql
CREATE TABLE whitelist (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER NOT NULL UNIQUE,
    username VARCHAR(255),
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER,
    comment VARCHAR(500)
);
CREATE INDEX ix_whitelist_telegram_id ON whitelist(telegram_id);
```

### 2. Hardcoded Superadmin

- **Superadmin ID**: `7276342619` (hardcoded in the codebase)
- The superadmin is always authorized and cannot be removed from the system
- Only the superadmin can add/remove users from the whitelist
- **Safety Feature**: The superadmin cannot blacklist themselves to prevent lockout

### 3. New Commands

#### For Superadmin Only:

- **`/whitelist`** - Show all whitelisted users with details
  - Shows total count and list of all users
  - Includes telegram IDs, usernames, and comments

- **`/allow @username`** - Add a user to the whitelist
  - Example: `/allow @durov`
  - Response: Confirms addition or indicates if user already exists

- **`/deny @username`** - Remove a user from the whitelist
  - Example: `/deny @username`
  - Response: Confirms removal or indicates if user not found
  - Note: Cannot remove the superadmin (safety feature)

### 4. Migration Process

#### Initial Setup

1. **Install Alembic**:
   ```bash
   pip install alembic
   ```

2. **Initialize Alembic** (already done):
   ```bash
   alembic init alembic
   ```

3. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

#### Migrating Existing Data

Run the migration script to transfer data from `whitelist.json` to the database:

```bash
python scripts/migrate_whitelist_to_db.py
```

This script:
- Reads the existing `whitelist.json`
- Transfers all users (except superadmin) to the database
- Renames the JSON file to a backup

### 5. File Changes

#### New Files:
- `src/config/whitelist_db.py` - Database-based whitelist manager
- `scripts/migrate_whitelist_to_db.py` - Migration script
- `alembic/` - Alembic configuration and migrations
- `docs/whitelist_database_migration.md` - This documentation

#### Modified Files:
- `src/database/models.py` - Added `Whitelist` model
- `src/database/manager.py` - Added whitelist management methods
- `src/bot/decorators.py` - Updated to use database whitelist
- `src/bot/commands.py` - Added `.whitelist` and `.blacklist` handlers
- `src/main.py` - Initialize database whitelist manager
- `requirements.txt` - Added alembic and dependencies

#### Deprecated:
- `src/config/whitelist.py` - No longer used (can be removed)
- `whitelist.json` - Renamed to backup after migration

### 6. Database Operations

The new `DatabaseWhitelistManager` provides:
- Caching for performance (60-second TTL by default)
- Async operations for non-blocking database access
- Thread-safe operations with locks

Key methods:
- `get_authorized_users()` - Get all authorized user IDs
- `is_authorized(telegram_id)` - Check if a user is authorized
- `add_user(telegram_id, username, added_by, comment)` - Add user to whitelist
- `remove_user(telegram_id)` - Remove user from whitelist
- `get_whitelist_info()` - Get detailed whitelist information

### 7. Future Database Changes

To add new columns or tables:

1. **Update the model** in `src/database/models.py`
2. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "Description of change"
   ```
3. **Review the generated migration** in `alembic/versions/`
4. **Apply migration**:
   ```bash
   alembic upgrade head
   ```

See `alembic/README.md` for detailed instructions.

## Benefits

1. **Scalability**: Database can handle large numbers of users efficiently
2. **Persistence**: Data survives application restarts without file I/O
3. **Atomic Operations**: Database transactions ensure data consistency
4. **Query Capabilities**: Can add complex queries and filters in the future
5. **Migration Support**: Alembic provides version control for database schema
6. **Audit Trail**: Can track who added users and when

## Security Considerations

- Only the hardcoded superadmin can modify the whitelist
- The superadmin ID is hardcoded and cannot be changed via commands
- The superadmin cannot be removed from the whitelist (prevents accidental lockout)
- All whitelist modifications are logged
- Database file should be properly secured with appropriate permissions

## Rollback Instructions

If you need to rollback to the JSON-based system:

1. Restore the backup: `mv whitelist.json.backup_* whitelist.json`
2. Revert code changes to use the old `WhitelistManager`
3. Remove the whitelist table: `alembic downgrade -1`

## Testing

Test the new system (as superadmin with ID 7276342619):

1. **Check authorization**: Send a message to the bot
2. **View whitelist**: `/whitelist` (superadmin only)
3. **Add user**: `/allow @username`
4. **Verify addition**: Check `/whitelist` again
5. **Remove user**: `/deny @username`
6. **Verify removal**: User should no longer be able to use the bot