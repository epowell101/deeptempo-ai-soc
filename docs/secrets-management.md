# Secrets Management Guide

DeepTempo AI SOC uses a flexible secrets management system that supports multiple storage backends. This guide explains how to configure and use secrets for different deployment scenarios.

## Overview

The secrets manager provides three storage backends with automatic fallback:

1. **Environment Variables** (Highest priority) - Best for containers and server deployments
2. **.env File** (Default) - Good for local development and simple server deployments  
3. **OS Keyring** (Opt-in only) - For desktop development (macOS Keychain, Windows Credential Manager)

**Important:** By default, the OS keyring is **disabled** to prevent macOS keychain permission prompts. You must explicitly enable it with `ENABLE_KEYRING=true` if you want to use it.

When reading secrets, the system tries each enabled backend in order until it finds the value. When writing secrets, you can configure which backend to use.

## Quick Start

### For Server Deployments (Recommended)

1. **Copy the example file:**
   ```bash
   cp env.example ~/.deeptempo/.env
   ```

2. **Edit the file with your actual secrets:**
   ```bash
   nano ~/.deeptempo/.env
   ```

3. **Set file permissions (important for security):**
   ```bash
   chmod 600 ~/.deeptempo/.env
   ```

4. **Start the application:**
   ```bash
   ./start_web.sh
   ```

The application will automatically read secrets from `~/.deeptempo/.env` and also save any secrets configured through the web UI to this file.

### For Docker/Container Deployments

You can pass secrets as environment variables directly to the container:

```bash
docker run -e CLAUDE_API_KEY="sk-ant-..." \
           -e SECRETS_BACKEND="env" \
           deeptempo-ai-soc
```

Or use a Docker secrets file:

```bash
docker run --env-file ~/.deeptempo/.env deeptempo-ai-soc
```

### For Systemd Service Deployments

Create a systemd service with environment variables:

```ini
[Unit]
Description=DeepTempo AI SOC
After=network.target

[Service]
Type=simple
User=deeptempo
WorkingDirectory=/opt/deeptempo-ai-soc
EnvironmentFile=/etc/deeptempo/.env
ExecStart=/opt/deeptempo-ai-soc/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 6987
Restart=always

[Install]
WantedBy=multi-user.target
```

## Supported Secrets

### Core Secrets

| Secret Name | Description | Required |
|------------|-------------|----------|
| `CLAUDE_API_KEY` | Anthropic Claude API key | Yes |
| `ANTHROPIC_API_KEY` | Alternative name for Claude API key | Yes (either one) |

### Optional Integration Secrets

| Secret Name | Description | Service |
|------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 storage | S3 |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 storage | S3 |
| `TIMESKETCH_PASSWORD` | Timesketch user password | Timesketch |
| `SPLUNK_PASSWORD` | Splunk user password | Splunk |
| `GITHUB_TOKEN` | GitHub personal access token | MCP GitHub |
| `POSTGRESQL_CONNECTION_STRING` | PostgreSQL connection string | MCP PostgreSQL |

## Configuration Options

### Choosing a Secrets Backend

Set the `SECRETS_BACKEND` environment variable to control where secrets are written:

- **`dotenv`** (default): Writes to `~/.deeptempo/.env`
- **`env`**: Writes to process environment (not persistent across restarts)
- **`keyring`**: Writes to OS keyring (macOS Keychain, Windows Credential Manager)

Set the `ENABLE_KEYRING` environment variable to control whether keyring is used for reading:

- **`false`** (default): Keyring is not checked (prevents macOS keychain prompts)
- **`true`**: Keyring is checked when reading secrets

Example:
```bash
# Server deployment (default - no keyring)
export SECRETS_BACKEND=dotenv
export ENABLE_KEYRING=false
./start_web.sh

# Desktop deployment with keyring
export SECRETS_BACKEND=keyring
export ENABLE_KEYRING=true
./start_web.sh
```

### Backend Priority

When **reading** secrets, the system tries backends in this order:

1. Process environment variables (set via `export`, Docker, systemd, etc.)
2. `~/.deeptempo/.env` file
3. OS keyring (only if `ENABLE_KEYRING=true`)

**Note:** By default, keyring is **not checked** to prevent macOS keychain permission prompts. You must explicitly enable it.

This means you can override any .env file value by setting an environment variable.

## Security Best Practices

### File Permissions

Always restrict permissions on your .env file:

```bash
chmod 600 ~/.deeptempo/.env
chown your_user:your_group ~/.deeptempo/.env
```

### Never Commit Secrets

The `.gitignore` file is configured to exclude:
- `.env`
- `.env.local`
- `*_config.json`

Never commit actual secrets to version control.

### Separate Secrets by Environment

Use different secrets for development, staging, and production:

```bash
# Development
~/.deeptempo/.env

# Staging
/etc/deeptempo/staging/.env

# Production
/etc/deeptempo/production/.env
```

### Rotate Secrets Regularly

Periodically rotate your API keys and passwords:

1. Generate new credentials in the service (Anthropic, AWS, etc.)
2. Update your `.env` file or environment variables
3. Restart the application
4. Revoke old credentials after confirming the new ones work

## Deployment Examples

### Simple Server Deployment

```bash
# 1. Set up secrets
mkdir -p ~/.deeptempo
cp env.example ~/.deeptempo/.env
nano ~/.deeptempo/.env  # Edit with actual values
chmod 600 ~/.deeptempo/.env

# 2. Start the application
./start_web.sh
```

### Docker Compose Deployment

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  deeptempo:
    image: deeptempo-ai-soc
    ports:
      - "6987:6987"
      - "6988:6988"
    env_file:
      - /etc/deeptempo/.env
    environment:
      - SECRETS_BACKEND=env
    volumes:
      - /var/lib/deeptempo:/root/.deeptempo
    restart: unless-stopped
```

### Kubernetes Deployment

Create a Kubernetes secret:

```bash
kubectl create secret generic deeptempo-secrets \
  --from-literal=CLAUDE_API_KEY="sk-ant-..." \
  --from-literal=AWS_ACCESS_KEY_ID="AKIA..." \
  --from-literal=AWS_SECRET_ACCESS_KEY="..."
```

Reference in your deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deeptempo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: deeptempo
  template:
    metadata:
      labels:
        app: deeptempo
    spec:
      containers:
      - name: deeptempo
        image: deeptempo-ai-soc:latest
        ports:
        - containerPort: 6987
        - containerPort: 6988
        env:
        - name: SECRETS_BACKEND
          value: "env"
        envFrom:
        - secretRef:
            name: deeptempo-secrets
```

### AWS ECS/Fargate Deployment

Use AWS Secrets Manager or Systems Manager Parameter Store:

```json
{
  "family": "deeptempo",
  "containerDefinitions": [
    {
      "name": "deeptempo",
      "image": "deeptempo-ai-soc:latest",
      "secrets": [
        {
          "name": "CLAUDE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:deeptempo/claude-key"
        },
        {
          "name": "AWS_ACCESS_KEY_ID",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:deeptempo/aws-access-key"
        }
      ],
      "environment": [
        {
          "name": "SECRETS_BACKEND",
          "value": "env"
        }
      ]
    }
  ]
}
```

## Troubleshooting

### Secrets Not Found

If the application can't find your secrets:

1. **Check the file location:**
   ```bash
   ls -la ~/.deeptempo/.env
   ```

2. **Verify environment variables:**
   ```bash
   printenv | grep -E "CLAUDE|AWS|TIMESKETCH|SPLUNK|GITHUB|POSTGRESQL"
   ```

3. **Check logs:**
   ```bash
   tail -f ~/.deeptempo/api.log | grep -i secret
   ```

4. **Test the secrets manager:**
   ```python
   from backend.secrets_manager import get_secrets_manager
   
   sm = get_secrets_manager()
   print(sm.get_backend_status())
   ```

### Permission Denied on .env File

```bash
# Fix permissions
chmod 600 ~/.deeptempo/.env
chown $USER:$USER ~/.deeptempo/.env
```

### Keyring Prompts on macOS

Keyring is now **disabled by default**, so you should not see prompts. If you're still getting them:

1. **Explicitly disable keyring:**
   ```bash
   export ENABLE_KEYRING=false
   export SECRETS_BACKEND=dotenv
   ```

2. **Verify the settings:**
   ```bash
   echo $ENABLE_KEYRING  # Should be empty or "false"
   echo $SECRETS_BACKEND  # Should be "dotenv"
   ```

3. **Restart the application**

4. **Clear old keyring entries (optional):**
   ```bash
   security delete-generic-password -s "deeptempo-ai-soc"
   ```

## Migration from Keyring

If you were previously using keyring (macOS Keychain) and want to migrate to .env:

1. **Export current secrets from keyring:**
   ```bash
   security find-generic-password -s "deeptempo-ai-soc" -a "claude_api_key" -w
   ```

2. **Create .env file with exported values:**
   ```bash
   cat > ~/.deeptempo/.env <<EOF
   CLAUDE_API_KEY="sk-ant-..."
   EOF
   chmod 600 ~/.deeptempo/.env
   ```

3. **Disable keyring and set backend preference:**
   ```bash
   export ENABLE_KEYRING=false
   export SECRETS_BACKEND=dotenv
   ```

4. **Restart the application**

5. **Optionally delete keyring entries:**
   ```bash
   security delete-generic-password -s "deeptempo-ai-soc" -a "claude_api_key"
   ```

**Note:** As of the latest version, keyring is disabled by default, so step 3 is technically optional but recommended for clarity.

## API Reference

For programmatic access to secrets:

```python
from backend.secrets_manager import get_secret, set_secret, get_secrets_manager

# Get a secret (tries all backends)
api_key = get_secret("CLAUDE_API_KEY")

# Set a secret (uses configured backend)
set_secret("CLAUDE_API_KEY", "sk-ant-...")

# Get backend status
sm = get_secrets_manager()
status = sm.get_backend_status()
print(status)
# {
#   "environment": {"available": True, ...},
#   "dotenv": {"available": True, "path": "/home/user/.deeptempo/.env", ...},
#   "keyring": {"available": False, ...},
#   "write_backend": "dotenv"
# }
```

## Support

For issues related to secrets management:

1. Check this documentation
2. Review the logs in `~/.deeptempo/api.log`
3. Open an issue on GitHub with relevant log excerpts (redact any secrets!)

