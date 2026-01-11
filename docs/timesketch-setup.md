# Timesketch Setup Guide

## Overview

Timesketch is an **external service** that must be deployed separately. The DeepTempo AI SOC application connects to a Timesketch server via its REST API.

## Quick Start

### Option 1: Local Development (Default)

If you're running Timesketch locally for development:

1. **Default Configuration**: The Settings Console pre-fills `http://localhost:5000` as the default server URL
2. **Start Timesketch**: Make sure your Timesketch server is running on `http://localhost:5000`
3. **Configure Authentication**: 
   - Use "Username/Password" method for local development
   - Default credentials are typically `admin` / `admin` for local setups
4. **Test Connection**: Click "Test Connection" in the Settings Console

### Option 2: Production Deployment

For production use:

1. **Server URL**: Enter your Timesketch server URL (e.g., `https://timesketch.example.com`)
2. **Authentication**: 
   - Use "API Token" method for production (recommended)
   - Or use "Username/Password" with your credentials
3. **SSL Verification**: Keep enabled for production servers
4. **Test Connection**: Verify connectivity before saving

## Timesketch Server Requirements

Timesketch must be deployed separately. Common deployment methods:

- **Docker**: `docker run -p 5000:5000 timesketch/timesketch`
- **Kubernetes**: Deploy using Timesketch Helm charts
- **Cloud**: Deploy to AWS, GCP, or Azure
- **Local**: Run from source or use Docker Compose

## Configuration Steps

1. **Open Settings Console**: File → Settings Console... (or Ctrl+,)
2. **Navigate to Timesketch Tab**
3. **Enter Server URL**: 
   - Local: `http://localhost:5000`
   - Production: Your Timesketch server URL
4. **Configure Authentication**:
   - Select "Username/Password" or "API Token"
   - Enter credentials
5. **Configure Auto-Sync** (optional):
   - Enable auto-sync if you want automatic case synchronization
   - Set sync interval (default: 300 seconds)
6. **Test Connection**: Click "Test Connection" to verify
7. **Save**: Click "Save All" to persist settings

## Troubleshooting

### Connection Failed

- **Check Server**: Ensure Timesketch server is running and accessible
- **Check URL**: Verify the server URL is correct
- **Check Credentials**: Verify username/password or API token
- **Check Network**: Ensure network connectivity to Timesketch server
- **Check SSL**: If using HTTPS, ensure SSL certificate is valid

### Localhost Not Working

- **Port Check**: Verify Timesketch is running on port 5000
- **Firewall**: Check if firewall is blocking connections
- **Docker**: If using Docker, ensure port mapping is correct

### Authentication Issues

- **API Token**: Generate a new API token in Timesketch web UI
- **Username/Password**: Verify credentials in Timesketch
- **Permissions**: Ensure user has appropriate permissions

## Auto-Sync Behavior

When auto-sync is enabled:

- **Startup**: Auto-sync service starts automatically when the application launches
- **Interval**: Syncs cases to Timesketch at the configured interval (default: 5 minutes)
- **Triggers**: Syncs when:
  - Cases are updated
  - New findings are added to cases
  - Manual sync is triggered

## Notes

- Timesketch is **not** started by `main.py` - it's an external service
- The application only **connects** to an existing Timesketch server
- Default configuration assumes local development setup
- Production deployments require proper server URL and authentication

