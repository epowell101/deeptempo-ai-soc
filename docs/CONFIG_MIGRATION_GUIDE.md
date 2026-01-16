# Configuration Migration Guide

## Overview

DeepTempo AI SOC has migrated from file-based configuration storage to **PostgreSQL database** storage. This provides:

✅ **Centralized Management** - Single source of truth  
✅ **ACID Compliance** - No file corruption, atomic updates  
✅ **Multi-User Support** - Concurrent access without locking  
✅ **Audit Trail** - Full history of configuration changes  
✅ **Scalability** - Easier deployment in containers/cloud  
✅ **Query Capabilities** - Search and analyze configurations  

## What Changed?

### Before (File-Based)
```
~/.deeptempo/
├── general_config.json
├── theme_config.json
├── integrations_config.json
├── s3_config.json
└── .env (secrets)
```

### After (Database-Backed)
```
PostgreSQL Database:
├── system_config          (general, theme, approval settings)
├── user_preferences       (per-user settings)
├── integration_configs    (integration settings)
└── config_audit_log       (change history)

Still File-Based:
└── ~/.deeptempo/.env      (secrets/credentials)
```

## Migration Steps

### Step 1: Backup Your Configuration

**Before starting, backup your existing configs:**

```bash
# Option 1: Use the migration script (recommended)
python database/migrate_configs_to_db.py --backup-only

# Option 2: Manual backup
cd ~/.deeptempo
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz *.json .env
```

### Step 2: Apply Database Schema

The new configuration tables will be created automatically when you start the database.

**If database is already running:**

```bash
# Connect to PostgreSQL
psql -U deeptempo -d deeptempo_soc -h localhost

# Run the schema update
\i database/init/04_config_tables.sql
```

**If starting fresh:**

```bash
# Just start the database - tables will be created automatically
./start_database.sh
```

### Step 3: Run Migration Script

```bash
# Dry run (see what will happen without making changes)
python database/migrate_configs_to_db.py --dry-run

# Actual migration (creates backup automatically)
python database/migrate_configs_to_db.py
```

**Expected output:**
```
🚀 Starting configuration migration
   Config directory: /Users/username/.deeptempo
   Dry run: False

✅ Backed up: general_config.json
✅ Backed up: theme_config.json
✅ Backed up: integrations_config.json
✅ Backed up: approval_config.json
✅ Backed up: .env
📦 Backup completed to: /Users/username/.deeptempo/backups/pre_migration_20260116_120000

📊 Migrating configurations to database...
✅ Migrated general settings
✅ Migrated theme settings
✅ Migrated approval settings
✅ Migrated 5 integration(s)

✅ Migration completed successfully!
```

### Step 4: Verify Migration

1. **Start the application:**
   ```bash
   ./start_web.sh
   ```

2. **Check Settings UI:**
   - Open http://localhost:3000
   - Navigate to Settings
   - Verify all settings are present

3. **Check database:**
   ```sql
   -- Connect to database
   psql -U deeptempo -d deeptempo_soc -h localhost
   
   -- View system configs
   SELECT key, value, config_type FROM system_config;
   
   -- View integrations
   SELECT integration_id, enabled FROM integration_configs;
   
   -- View recent changes
   SELECT * FROM recent_config_changes;
   ```

### Step 5: Test Configuration Changes

1. **Change a setting in the UI:**
   - Go to Settings → General
   - Toggle a setting
   - Save

2. **Verify it persists:**
   - Refresh the page
   - Setting should still be changed

3. **Check audit log:**
   ```sql
   SELECT * FROM config_audit_log ORDER BY timestamp DESC LIMIT 10;
   ```

## Backward Compatibility

### Dual Write Strategy

During the transition period, the system **writes to both** database and files:

```python
# Example: Setting general config
1. Save to database (primary)
2. Save to file (fallback/compatibility)
```

### Reading Priority

When reading configurations, the system tries:

```
1. PostgreSQL database (primary)
   ↓ (if not found)
2. JSON files (fallback)
   ↓ (if not found)
3. Default values
```

### When to Remove JSON Files

**After successful migration and verification:**

1. ✅ Verify all settings work in UI
2. ✅ Test all integrations
3. ✅ Run for at least 1 week without issues
4. ✅ Confirm backups are working

Then you can **optionally** remove old JSON files:

```bash
cd ~/.deeptempo
mkdir deprecated
mv *.json deprecated/
# Keep .env file - it's still used for secrets!
```

## What's Not Changed

These still use file-based storage (by design):

### 1. Secrets/Credentials
**Location:** `~/.deeptempo/.env`

**Still file-based because:**
- Industry best practice for secrets
- Environment variable compatibility
- Security isolation
- No need for database storage

**Examples:**
- `CLAUDE_API_KEY`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `GITHUB_TOKEN`

### 2. MCP Server Config
**Location:** `mcp-config.json` (project root)

**Still file-based because:**
- Required by MCP runtime
- Expected format for Model Context Protocol
- Not user-configurable settings

### 3. Operational Data Files
**Location:** `data/` directory

**Still file-based (for now):**
- `pending_actions.json` - Pending approval actions
- `workflow_status.json` - Workflow states

**Note:** These may be migrated to database in a future update.

## Database Schema

### system_config Table

Stores system-wide configuration settings.

```sql
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,      -- e.g., 'general.settings'
    value JSONB NOT NULL,               -- Configuration as JSON
    description TEXT,
    config_type VARCHAR(50),            -- 'general', 'approval', 'theme'
    updated_by VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Example records:**
```sql
key: 'general.settings'
value: {"auto_start_sync": false, "show_notifications": true, "theme": "dark"}

key: 'approval.force_manual_approval'
value: {"enabled": false}
```

### user_preferences Table

Stores per-user preferences (multi-user support).

```sql
CREATE TABLE user_preferences (
    user_id VARCHAR(100) PRIMARY KEY,
    preferences JSONB NOT NULL,
    display_name VARCHAR(200),
    email VARCHAR(200),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_login TIMESTAMP
);
```

### integration_configs Table

Stores integration configurations (non-sensitive data only).

```sql
CREATE TABLE integration_configs (
    integration_id VARCHAR(100) PRIMARY KEY,
    enabled BOOLEAN NOT NULL,
    config JSONB NOT NULL,
    integration_name VARCHAR(200),
    integration_type VARCHAR(50),
    description TEXT,
    last_test_at TIMESTAMP,
    last_test_success BOOLEAN,
    last_error TEXT,
    updated_by VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### config_audit_log Table

Tracks all configuration changes for compliance.

```sql
CREATE TABLE config_audit_log (
    id SERIAL PRIMARY KEY,
    config_type VARCHAR(50),
    config_key VARCHAR(200),
    action VARCHAR(20),                 -- 'create', 'update', 'delete'
    old_value JSONB,
    new_value JSONB,
    changed_by VARCHAR(100),
    change_reason TEXT,
    timestamp TIMESTAMP
);
```

## API Changes

### Endpoints (No Breaking Changes)

All existing API endpoints work the same:

- `GET /api/config/general` - Get general settings
- `POST /api/config/general` - Save general settings
- `GET /api/config/integrations` - Get integrations
- `POST /api/config/integrations` - Save integrations

### Internal Behavior

**Before:**
```python
# Read from file
with open('~/.deeptempo/general_config.json') as f:
    config = json.load(f)
```

**After:**
```python
# Read from database with file fallback
config_service = get_config_service()
config = config_service.get_system_config('general.settings')
if not config:
    # Fallback to file...
```

## Usage Examples

### Python Code

```python
from database.config_service import get_config_service

# Initialize service
config_service = get_config_service(user_id='admin')

# Get system config
general_settings = config_service.get_system_config('general.settings')
# Returns: {"auto_start_sync": false, "show_notifications": true, ...}

# Set system config
config_service.set_system_config(
    key='approval.force_manual_approval',
    value={'enabled': True},
    config_type='approval',
    change_reason='Enabling during incident response'
)

# Get user preferences
user_prefs = config_service.get_user_preferences(user_id='alice')

# List integrations
integrations = config_service.list_integrations(enabled_only=True)

# Get audit log
audit_log = config_service.get_audit_log(
    config_type='approval',
    limit=50
)
```

### SQL Queries

```sql
-- View all system configs
SELECT * FROM system_config ORDER BY config_type, key;

-- View enabled integrations
SELECT * FROM enabled_integrations;

-- View recent config changes
SELECT * FROM recent_config_changes;

-- Find who changed approval settings
SELECT 
    changed_by,
    old_value,
    new_value,
    change_reason,
    timestamp
FROM config_audit_log
WHERE config_type = 'approval'
ORDER BY timestamp DESC;

-- Count integrations by type
SELECT 
    integration_type,
    COUNT(*) as total,
    SUM(CASE WHEN enabled THEN 1 ELSE 0 END) as enabled_count
FROM integration_configs
GROUP BY integration_type;
```

## Troubleshooting

### Issue: Migration Script Fails

**Error:** `ModuleNotFoundError: No module named 'database'`

**Solution:**
```bash
# Make sure you're in the project root
cd /path/to/deeptempo-ai-soc

# Run with python3
python3 database/migrate_configs_to_db.py
```

### Issue: Database Connection Failed

**Error:** `Connection refused: postgresql://localhost:5432`

**Solution:**
```bash
# Start the database
./start_database.sh

# Wait for it to be ready
sleep 5

# Verify it's running
docker ps | grep postgres

# Try migration again
python3 database/migrate_configs_to_db.py
```

### Issue: Settings Not Persisting

**Problem:** Changes in UI don't persist after refresh

**Debug steps:**

1. **Check database connection:**
   ```bash
   psql -U deeptempo -d deeptempo_soc -h localhost -c "SELECT COUNT(*) FROM system_config;"
   ```

2. **Check logs:**
   ```bash
   tail -f logs/backend.log | grep config
   ```

3. **Verify write permissions:**
   ```sql
   -- Connect as deeptempo user
   INSERT INTO system_config (key, value, config_type)
   VALUES ('test.key', '{"test": true}', 'test');
   
   SELECT * FROM system_config WHERE key = 'test.key';
   ```

### Issue: Audit Log Not Recording

**Problem:** No entries in `config_audit_log`

**Solution:**

```sql
-- Check table exists
\dt config_audit_log

-- Check permissions
SELECT grantee, privilege_type 
FROM information_schema.role_table_grants 
WHERE table_name='config_audit_log';

-- Grant permissions if needed
GRANT SELECT, INSERT ON config_audit_log TO deeptempo;
GRANT USAGE, SELECT ON SEQUENCE config_audit_log_id_seq TO deeptempo;
```

## Rollback Procedure

If you need to rollback to file-based configs:

### Step 1: Restore from Backup

```bash
cd ~/.deeptempo
# Find your backup
ls -lt backups/

# Restore files
cd backups/pre_migration_YYYYMMDD_HHMMSS/
cp *.json ../..
cp .env ../..
```

### Step 2: Disable Database Config

**Temporary workaround:** Comment out database imports:

```python
# In backend/api/config.py
# sys.path.insert(0, str(Path(__file__).parent.parent.parent))
# from database.config_service import get_config_service
```

### Step 3: Restart Application

```bash
./shutdown_all.sh
./start_web.sh
```

## Benefits Summary

### For Single-User Deployments

- ✅ Automatic backups (part of database backups)
- ✅ Configuration history/audit trail
- ✅ No risk of file corruption
- ✅ Better integration with Docker/containers

### For Multi-User Deployments

- ✅ Per-user preferences
- ✅ Concurrent access without locking
- ✅ User-specific audit trails
- ✅ Role-based configuration management (future)

### For Developers

- ✅ Easy to query configurations
- ✅ Type-safe JSONB storage
- ✅ Built-in validation via database constraints
- ✅ Easy to add new config types

## Future Enhancements

Planned improvements:

1. **Configuration Versioning** - Rollback to previous configs
2. **Configuration Templates** - Predefined config sets
3. **Role-Based Access** - Different users, different permissions
4. **Configuration Import/Export** - Share configs between instances
5. **Configuration Validation** - JSON schema validation
6. **Configuration Search** - Full-text search across configs

## Support

If you encounter issues:

1. Check this guide's Troubleshooting section
2. Check application logs: `logs/backend.log`
3. Check database logs: `docker logs deeptempo-postgres`
4. File an issue on GitHub with:
   - Migration script output
   - Error messages
   - Database version
   - Operating system

## Summary

✅ **Migration is safe** - Automatic backups created  
✅ **Backward compatible** - Falls back to files if database unavailable  
✅ **Non-breaking** - All APIs work the same  
✅ **Reversible** - Can rollback if needed  
✅ **Well-tested** - Includes dry-run mode  

**Recommended approach:**

1. Backup your configs (automatic with migration script)
2. Run migration script with `--dry-run` first
3. Run actual migration
4. Verify in UI
5. Keep old files for 1-2 weeks as safety net
6. Remove old files after confidence built

**Questions?** Check the troubleshooting section or open an issue!

