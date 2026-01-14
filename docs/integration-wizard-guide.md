# Integration Wizard Guide

## Overview

The DeepTempo AI SOC platform now features a **Configuration Wizard** for all security integrations directly in the Settings page. This makes it easy to set up and manage connections to external security tools without manually editing configuration files.

## Features

### ✨ What's New

- **Visual Integration Cards**: Browse all available integrations organized by category
- **Step-by-Step Wizards**: Guided configuration process with validation
- **Pre-configured Templates**: Smart defaults for common services
- **Configuration Management**: Easily enable, disable, and reconfigure integrations
- **Real-time Status**: See which integrations are active at a glance
- **Documentation Links**: Quick access to vendor documentation for API setup

### 📦 Supported Integration Categories

1. **Threat Intelligence** (6 integrations)
   - VirusTotal
   - AlienVault OTX
   - Shodan
   - MISP
   - URL Analysis
   - IP Geolocation

2. **EDR/XDR Platforms** (4 integrations)
   - CrowdStrike Falcon
   - SentinelOne
   - Carbon Black
   - Microsoft Defender for Endpoint

3. **SIEM** (1 integration)
   - Azure Sentinel

4. **Cloud Security** (2 integrations)
   - AWS Security Hub
   - GCP Security Command Center

5. **Identity & Access** (2 integrations)
   - Okta
   - Azure Active Directory

6. **Network Security** (1 integration)
   - Palo Alto Networks

7. **Incident Management** (1 integration)
   - Jira

8. **Communications** (7 integrations)
   - Slack
   - PagerDuty
   - Microsoft Teams
   - Email (SMTP)
   - Generic Webhook
   - Discord
   - Mattermost

9. **Sandbox Analysis** (3 integrations)
   - Hybrid Analysis
   - Joe Sandbox
   - ANY.RUN

**Total: 27 pre-configured integrations ready to use!**

## How to Use

### Setting Up an Integration

1. **Navigate to Settings**
   - Click the Settings icon in the main navigation
   - Select the **"Integrations"** tab

2. **Browse Available Integrations**
   - Integrations are organized by category in expandable sections
   - Click the expand icon to view integrations in each category

3. **Configure an Integration**
   - Click the **"Setup"** button on any integration card
   - A wizard dialog will open with step-by-step configuration

4. **Fill in Required Fields**
   - Each integration has specific requirements (API keys, URLs, etc.)
   - Required fields are marked with an asterisk (*)
   - Helpful text and placeholders guide you through the process

5. **Review Configuration**
   - The wizard shows a review step before saving
   - Sensitive fields (passwords, API keys) are masked
   - Click **"Save Configuration"** to complete setup

6. **Integration is Active**
   - Successfully configured integrations show a green checkmark
   - They appear in the "Active Integrations" summary at the top
   - MCP servers can now access these configurations

### Managing Existing Integrations

#### Reconfigure an Integration
- Click the **"Reconfigure"** button on a configured integration
- The wizard will open pre-populated with existing settings
- Make changes and save

#### Disable an Integration
- Click the **X** on an integration chip in the Active Integrations section
- The integration will be disabled but configuration is preserved
- Re-enable by clicking "Setup" again

#### View Documentation
- Click the **"Docs"** button on any integration card
- Opens vendor documentation in a new tab
- Useful for finding API keys, setting up accounts, etc.

## Integration Configuration Examples

### Example 1: Setting Up VirusTotal

1. Go to Settings → Integrations → Threat Intelligence
2. Click "Setup" on the VirusTotal card
3. Enter your API key:
   - Get it from: https://www.virustotal.com/gui/my-apikey
   - Paste into the "API Key" field
4. Review and save
5. VirusTotal is now ready to use!

### Example 2: Configuring Jira

1. Go to Settings → Integrations → Incident Management
2. Click "Setup" on the Jira card
3. Fill in required fields:
   - **Jira URL**: Your Atlassian instance URL (e.g., `https://yourcompany.atlassian.net`)
   - **Email/Username**: Your Jira login email
   - **API Token**: Create at https://id.atlassian.com/manage-profile/security/api-tokens
   - **Default Project Key** (optional): e.g., "SEC"
4. Review and save
5. Jira integration is active!

### Example 3: AWS Security Hub Setup

1. Go to Settings → Integrations → Cloud Security
2. Click "Setup" on AWS Security Hub
3. Provide AWS credentials:
   - **Access Key ID**: Your AWS IAM access key
   - **Secret Access Key**: Your AWS IAM secret
   - **Region**: AWS region (e.g., `us-east-1`)
4. Review and save
5. AWS Security Hub is connected!

## Configuration Storage

### Where Configurations are Stored

All integration configurations are stored securely in:
```
~/.deeptempo/integrations_config.json
```

### Configuration Format

```json
{
  "enabled_integrations": [
    "virustotal",
    "jira",
    "slack"
  ],
  "integrations": {
    "virustotal": {
      "api_key": "your-api-key-here"
    },
    "jira": {
      "url": "https://yourcompany.atlassian.net",
      "username": "user@example.com",
      "api_token": "your-token",
      "project_key": "SEC"
    },
    "slack": {
      "bot_token": "xoxb-your-token",
      "default_channel": "#security-alerts"
    }
  }
}
```

## For Developers

### Adding a New Integration

To add a new integration to the wizard:

1. **Update Integration Metadata** (`frontend/src/config/integrations.ts`):

```typescript
{
  id: 'my-new-tool',
  name: 'My Security Tool',
  category: 'Threat Intelligence',
  description: 'Connect to My Security Tool for enhanced threat detection',
  fields: [
    {
      name: 'api_key',
      label: 'API Key',
      type: 'password',
      required: true,
      helpText: 'Get your API key from https://example.com/api'
    }
  ],
  docs_url: 'https://docs.example.com'
}
```

2. **Create MCP Server** (if needed):
   - Create folder: `mcp_servers/my_new_tool_server/`
   - Add `server.py` with tools
   - Use `config_utils.get_integration_config('my-new-tool')` to load config

3. **Add to MCP Config** (`mcp-config.json`):

```json
"my-new-tool": {
  "command": "python3",
  "args": ["-m", "mcp_servers.my_new_tool_server.server"],
  "cwd": "${workspaceFolder}",
  "env": {}
}
```

### Using Integration Config in MCP Servers

```python
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config_utils import get_integration_config

def my_tool_function():
    config = get_integration_config('my-new-tool')
    api_key = config.get('api_key')
    
    if not api_key:
        return {"error": "Integration not configured"}
    
    # Use the API key...
```

## Security Considerations

### Sensitive Data Protection

- **Password Fields**: All sensitive fields use `type: 'password'` in the wizard
- **Display Masking**: Passwords and API keys are masked in the review step
- **File Permissions**: Config file at `~/.deeptempo/` should have appropriate permissions
- **No Logging**: Sensitive values are never logged by the system

### Best Practices

1. **API Keys**: Use dedicated API keys with minimum required permissions
2. **Service Accounts**: Create service accounts specifically for DeepTempo
3. **Key Rotation**: Regularly rotate API keys and tokens
4. **Access Review**: Periodically review which integrations are enabled
5. **Least Privilege**: Grant only necessary permissions to service accounts

## Troubleshooting

### Integration Not Working

1. **Check Configuration**:
   - Go to Settings → Integrations
   - Click "Reconfigure" on the integration
   - Verify all fields are correct

2. **Check MCP Server Status**:
   - Go to Settings → MCP Servers tab
   - Look for the integration's MCP server
   - Check if it's running (green status)
   - View logs if there are errors

3. **Verify API Credentials**:
   - Test credentials directly with vendor's API documentation
   - Check for expired tokens or keys
   - Ensure proper permissions are granted

4. **Check Network Connectivity**:
   - Ensure firewall allows outbound connections
   - Verify proxy settings if applicable

### Common Issues

**Issue**: Integration shows as enabled but not working
- **Solution**: Restart the corresponding MCP server from Settings → MCP Servers

**Issue**: API key rejected
- **Solution**: Verify the key is correct and has not expired. Check vendor documentation for required permissions.

**Issue**: Configuration not saving
- **Solution**: Check file permissions on `~/.deeptempo/` directory. Ensure write access.

## Migration from Old System

If you were using the old `ui.integrations_config` system:

1. Your existing configurations should be migrated automatically
2. The new system reads from the same location: `~/.deeptempo/integrations_config.json`
3. MCP servers have been updated to use the new `config_utils` module
4. Old configurations are backward compatible

## Future Enhancements

Planned improvements include:

- **Connection Testing**: Test integration before saving
- **Import/Export**: Share configurations between environments
- **Templates**: Pre-configured templates for common setups
- **Bulk Operations**: Enable/disable multiple integrations at once
- **Configuration History**: Track changes to configurations over time
- **Secret Management**: Integration with external secret managers (HashiCorp Vault, AWS Secrets Manager)

## Support

For issues or questions:
- Check the integration's documentation link in the wizard
- Review MCP server logs in Settings → MCP Servers
- Consult vendor documentation for API setup requirements

---

**Last Updated**: January 2026
**Version**: 1.0.0

