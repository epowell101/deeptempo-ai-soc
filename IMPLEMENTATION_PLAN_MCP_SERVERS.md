# MCP Servers Implementation Plan

## Status: IN PROGRESS

This document tracks the implementation of all MCP servers for the DeepTempo AI SOC platform.

## Configuration UI
✅ **COMPLETED**: Unified integrations configuration dialog created at `ui/integrations_config.py`
- Category-based organization (11 categories)
- 30+ integrations supported
- Secure credential storage using keyring
- Non-bloated interface design
- Integrated into Settings Console

## Tier 1: Critical Integrations (High Priority)

### Threat Intelligence
- ✅ **VirusTotal** - File/URL/IP/domain reputation checks
  - Location: `mcp_servers/virustotal_server/`
  - Tools: vt_check_hash, vt_check_ip, vt_check_domain, vt_check_url, vt_get_file_report
  - Rate limiting: 4 req/min (configurable)

- ✅ **MISP** - Malware Information Sharing Platform
  - Location: `mcp_servers/misp_server/`
  - Tools: misp_search_attributes, misp_get_event, misp_add_event, misp_add_attribute, misp_search_iocs, misp_add_sighting
  - Requires: pymisp library

- 🔄 **OpenCTI** - Structured threat intelligence platform
  - Location: `mcp_servers/opencti_server/`
  - Tools: opencti_query_indicators, opencti_get_reports, opencti_search_threat_actors, opencti_create_observable
  - Requires: pycti library

### Incident Management
- ⏳ **Jira** - Ticket creation and workflow management
  - Tools: jira_create_issue, jira_update_issue, jira_search_issues, jira_add_comment, jira_transition_issue
  - Requires: jira library

- ⏳ **PagerDuty** - Alerting and on-call management
  - Tools: pd_create_incident, pd_acknowledge_incident, pd_get_on_call, pd_trigger_escalation
  - Requires: pdpyras library

- ⏳ **ServiceNow** - Enterprise ITSM integration
  - Tools: snow_create_incident, snow_update_incident, snow_create_change_request, snow_query_cmdb
  - Requires: pysnow library

### Communications
- ⏳ **Slack** - Real-time team notifications
  - Tools: slack_send_message, slack_create_channel, slack_upload_file, slack_search_messages
  - Requires: slack_sdk library

- ⏳ **Microsoft Teams** - Enterprise collaboration
  - Tools: teams_send_message, teams_create_channel, teams_post_card
  - Requires: msal, requests

- ⏳ **Email** - Email-based alerting
  - Tools: email_send, email_send_report, email_send_alert_digest
  - Requires: Built-in smtplib

## Tier 2: Important Integrations

### EDR/XDR Platforms
- ⏳ **Microsoft Defender** - Windows endpoint protection
- ⏳ **SentinelOne** - AI-powered EDR
- ⏳ **Carbon Black** - Endpoint detection and response

### Cloud Security
- ⏳ **AWS Security Hub** - AWS security findings
- ⏳ **Azure Sentinel** - Cloud-native SIEM
- ⏳ **GCP Security Command Center** - GCP security

### Network Security
- ⏳ **Palo Alto Networks** - Firewall management
- ⏳ **Cisco Secure** - DNS security and firewall

### Vulnerability Management
- ⏳ **Tenable** - Vulnerability scanning
- ⏳ **Qualys** - Vulnerability and compliance

## Tier 3: Advanced Features

### Malware Analysis
- ⏳ **Hybrid Analysis** - Automated malware sandbox
- ⏳ **Joe Sandbox** - Advanced malware sandbox
- ⏳ **ANY.RUN** - Interactive malware sandbox

### Additional Threat Feeds
- ⏳ **AlienVault OTX** - Open threat exchange
- ⏳ **ThreatConnect** - Commercial threat intelligence
- ⏳ **Shodan** - Internet-connected device search

### Identity & Access
- ⏳ **Okta** - Identity and access management
- ⏳ **Azure AD** - Microsoft identity platform

### Data Storage
- ⏳ **Elasticsearch** - Advanced log search
- ⏳ **PostgreSQL** - Relational database

### Email Security
- ⏳ **Mimecast** - Email security platform
- ⏳ **Proofpoint** - Advanced email threat protection

## Tier 4: Utilities

- ⏳ **GitHub** - Code repository management
- ⏳ **Web Scraping/OSINT** - Open-source intelligence
- ⏳ **URL/Domain Analysis** - URL/domain reputation
- ⏳ **IP Geolocation** - IP address intelligence

## Implementation Pattern

All MCP servers follow this standardized structure:

```python
"""MCP Server for [Integration Name]."""

import asyncio
import logging
import json
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_[integration]_config():
    """Get configuration from integrations config."""
    try:
        from ui.integrations_config import IntegrationsConfigDialog
        config = IntegrationsConfigDialog.get_integration_config('[integration_id]')
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

server = Server("[integration]-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        # Tool definitions
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    config = get_[integration]_config()
    
    # Validate configuration
    if not config or not config.get('required_field'):
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "[Integration] not configured",
                "message": "Please configure in Settings > Integrations"
            }, indent=2)
        )]
    
    # Tool implementation
    try:
        # Call external API/service
        pass
    except Exception as e:
        logger.error(f"Error: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]

async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="[integration]-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## MCP Configuration Updates

The `mcp-config.json` file needs to be updated with entries for all enabled integrations.
This will be generated dynamically based on enabled integrations in the configuration.

## Required Python Libraries

Add to `requirements.txt`:
```
# Threat Intelligence
pymisp>=2.4.170
pycti>=5.12.0

# Incident Management  
jira>=3.5.0
pdpyras>=5.1.0
pysnow>=0.7.17

# Communications
slack_sdk>=3.23.0
msal>=1.24.1

# EDR/XDR
azure-identity>=1.14.0
azure-mgmt-security>=5.0.0

# Cloud Security
boto3>=1.28.0
azure-mgmt-sentinel>=1.0.0
google-cloud-security-command-center>=1.23.0

# Network Security
pan-os-python>=1.11.0

# Vulnerability Management
tenable-io>=1.16.0

# Malware Analysis
requests>=2.31.0

# Data Storage
elasticsearch>=8.10.0
psycopg2-binary>=2.9.9

# Utilities
PyGithub>=2.1.1
shodan>=1.30.1
```

## Testing Plan

1. Test configuration UI with all integrations
2. Test each MCP server individually with mock/test credentials
3. Test integration with Claude Desktop
4. Test rate limiting and error handling
5. Test credential storage/retrieval via keyring

## Deployment Notes

1. MCP servers are only loaded for enabled integrations
2. Configuration is stored in `~/.deeptempo/integrations_config.json`
3. Sensitive data stored in system keyring
4. MCP servers can be started/stopped via MCP Manager
5. Restart required after configuration changes

## Next Steps

1. ✅ Complete configuration UI
2. 🔄 Complete Tier 1 server implementations
3. ⏳ Implement Tier 2 servers
4. ⏳ Implement Tier 3 servers
5. ⏳ Implement Tier 4 servers
6. ⏳ Update `mcp-config.json` generator
7. ⏳ Update `requirements.txt`
8. ⏳ Test all integrations
9. ⏳ Update documentation

## Legend
- ✅ Completed
- 🔄 In Progress
- ⏳ Pending
- ❌ Blocked/Deferred

