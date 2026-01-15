# PostgreSQL MCP Server Connection Fix

## Problem

The postgres MCP server was failing to connect with the error:
```
Failed to connect to postgres: unhandled errors in a TaskGroup (1 sub-exception)
Please provide a database URL as a command-line argument
```

## Root Cause

The `@modelcontextprotocol/server-postgres` NPX package requires the database URL to be passed as a **command-line argument**, not just as an environment variable. The configuration was attempting to pass it via environment variables, which the server doesn't support.

## Solution

### 1. Updated `mcp-config.json`

Changed the postgres server configuration to pass the connection string as a command-line argument with environment variable substitution:

```json
"postgres": {
  "command": "npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-postgres",
    "${POSTGRESQL_CONNECTION_STRING}"
  ]
}
```

### 2. Enhanced `services/mcp_service.py`

Added environment variable substitution support:
- New `_substitute_env_vars()` method that handles `${VAR_NAME}` format
- Updated `_initialize_servers()` to substitute environment variables in command-line arguments

### 3. Updated `backend/main.py`

Added startup code to load secrets into environment variables:
- Loads `POSTGRESQL_CONNECTION_STRING` from secrets manager
- Falls back to default connection string if not configured
- Also loads `GITHUB_TOKEN` for the GitHub MCP server

### 4. Updated `env.example`

Added documentation about the PostgreSQL connection string format and default values.

## Configuration

### Default Connection (Local Development)

The default connection string matches the Docker Compose PostgreSQL setup:
```
postgresql://deeptempo:deeptempo_secure_password_change_me@localhost:5432/deeptempo_soc
```

### Custom Configuration

To configure a different PostgreSQL connection:

1. **Via Web UI** (Recommended):
   - Go to Settings → MCP Servers → PostgreSQL
   - Enter your connection string
   - Click "Save Configuration"

2. **Via Environment Variable**:
   ```bash
   export POSTGRESQL_CONNECTION_STRING="postgresql://user:password@host:port/database"
   ```

3. **Via Secrets File** (`~/.deeptempo/.env`):
   ```
   POSTGRESQL_CONNECTION_STRING="postgresql://user:password@host:port/database"
   ```

## Testing

After applying this fix, restart the application:

```bash
./shutdown_all.sh
./start_web.sh
```

Check the logs for successful connection:
```
2026-01-14 XX:XX:XX,XXX - services.mcp_client - INFO - Connected to postgres, found X tools
2026-01-14 XX:XX:XX,XXX - main - INFO - Connected to MCP server: postgres
```

## Benefits

1. **Proper Connection**: The postgres MCP server now receives the connection string correctly
2. **Environment Variable Support**: All MCP server configurations can now use `${VAR_NAME}` substitution
3. **Secure Configuration**: Connection strings are stored securely via the secrets manager
4. **Flexible Setup**: Works with local Docker, remote databases, or custom configurations

## Related Files

- `mcp-config.json` - MCP server configuration
- `services/mcp_service.py` - MCP service with environment variable substitution
- `backend/main.py` - Startup code that loads secrets
- `backend/api/config.py` - API endpoints for configuration management
- `env.example` - Example environment variables

