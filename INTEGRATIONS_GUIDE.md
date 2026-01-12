# DeepTempo AI SOC - Integrations Guide

## Overview

The DeepTempo AI SOC now supports **35+ security tool integrations** organized into 11 categories. All integrations are managed through a unified configuration interface and exposed as MCP tools to Claude.

## Quick Start

### 1. Configure Integrations

1. Open the application
2. Go to **Settings → Integrations**
3. Click **"Configure Integrations"**
4. Navigate to the category you want (e.g., Threat Intelligence)
5. **Enable** the integration by checking the checkbox
6. Fill in the required credentials/settings
7. Click **"Save Configuration"**

### 2. Generate MCP Configuration

After enabling integrations, generate the MCP configuration:

```bash
python3 scripts/generate_mcp_config.py
```

This creates `mcp-config.json` with only the enabled integrations.

### 3. Restart MCP Servers

Restart your MCP servers or Claude Desktop to load the new integrations.

## Available Integrations

### 🔍 Threat Intelligence (6 integrations)

#### VirusTotal ✅ FULLY IMPLEMENTED
- **Status**: Production Ready
- **Tools**: `vt_check_hash`, `vt_check_ip`, `vt_check_domain`, `vt_check_url`, `vt_get_file_report`
- **Config**: API Key, Rate Limit
- **Library**: `requests` (built-in)
- **Use Case**: File/URL/IP/domain reputation checks, malware analysis

#### MISP ✅ FULLY IMPLEMENTED
- **Status**: Production Ready
- **Tools**: `misp_search_attributes`, `misp_get_event`, `misp_add_event`, `misp_add_attribute`, `misp_search_iocs`, `misp_add_sighting`
- **Config**: MISP URL, API Key, SSL Verification
- **Library**: `pymisp>=2.4.170`
- **Use Case**: Community threat intelligence sharing, IOC management

#### OpenCTI 🔄 SCAFFOLD READY
- **Status**: Scaffold Created, Needs Implementation
- **Tools**: `opencti_query_indicators`, `opencti_get_reports`, `opencti_search_threat_actors`, `opencti_create_observable`
- **Config**: OpenCTI URL, API Token, SSL Verification
- **Library**: `pycti>=5.12.0`
- **Use Case**: Structured threat intelligence with relationships

#### AlienVault OTX 🔄 SCAFFOLD READY
- **Tools**: `otx_get_pulses`, `otx_search_indicators`, `otx_get_ioc_reputation`
- **Config**: API Key
- **Use Case**: Open threat exchange community intelligence

#### ThreatConnect 🔄 SCAFFOLD READY
- **Tools**: `tc_query_indicators`, `tc_get_groups`, `tc_create_indicator`, `tc_add_tag`
- **Config**: API URL, Access ID, Secret Key
- **Use Case**: Commercial threat intelligence platform

#### Shodan 🔄 SCAFFOLD READY
- **Tools**: `shodan_search_ip`, `shodan_search_exploits`, `shodan_get_host_info`, `shodan_search_vulnerabilities`
- **Config**: API Key
- **Library**: `shodan>=1.30.1`
- **Use Case**: Internet-connected device discovery, vulnerability research

### 🎫 Incident Management (3 integrations)

#### Jira 🔄 SCAFFOLD READY
- **Tools**: `jira_create_issue`, `jira_update_issue`, `jira_search_issues`, `jira_add_comment`, `jira_transition_issue`
- **Config**: Jira URL, Email, API Token, Project Key
- **Library**: `jira>=3.5.0`
- **Use Case**: Ticket creation and workflow management

#### PagerDuty 🔄 SCAFFOLD READY
- **Tools**: `pd_create_incident`, `pd_acknowledge_incident`, `pd_get_on_call`, `pd_trigger_escalation`
- **Config**: API Token, Service ID, Escalation Policy ID
- **Library**: `pdpyras>=5.1.0`
- **Use Case**: Alerting, on-call management, incident response

#### ServiceNow 🔄 SCAFFOLD READY
- **Tools**: `snow_create_incident`, `snow_update_incident`, `snow_create_change_request`, `snow_query_cmdb`
- **Config**: Instance Name, Username, Password, Assignment Group
- **Library**: `pysnow>=0.7.17`
- **Use Case**: Enterprise ITSM integration

### 💬 Communications (3 integrations)

#### Slack 🔄 SCAFFOLD READY
- **Tools**: `slack_send_message`, `slack_create_channel`, `slack_upload_file`, `slack_search_messages`
- **Config**: Bot Token, Default Channel
- **Library**: `slack_sdk>=3.23.0`
- **Use Case**: Real-time team notifications and collaboration

#### Microsoft Teams 🔄 SCAFFOLD READY
- **Tools**: `teams_send_message`, `teams_create_channel`, `teams_post_card`
- **Config**: Webhook URL, Tenant ID
- **Library**: `msal>=1.24.1`
- **Use Case**: Enterprise collaboration and notifications

#### Email 🔄 SCAFFOLD READY
- **Tools**: `email_send`, `email_send_report`, `email_send_alert_digest`
- **Config**: SMTP Server, Port, Username, Password, From Address, Recipients
- **Library**: Built-in `smtplib`
- **Use Case**: Email-based alerting and reporting

### 🛡️ EDR/XDR Platforms (3 integrations)

#### Microsoft Defender 🔄 SCAFFOLD READY
- **Tools**: `defender_get_alerts`, `defender_isolate_machine`, `defender_run_antivirus_scan`, `defender_get_machine_info`, `defender_get_vulnerabilities`
- **Config**: Tenant ID, Client ID, Client Secret
- **Library**: `azure-identity>=1.14.0`, `azure-mgmt-security>=5.0.0`
- **Use Case**: Windows endpoint protection

#### SentinelOne 🔄 SCAFFOLD READY
- **Tools**: `s1_get_threats`, `s1_isolate_endpoint`, `s1_remediate_threat`, `s1_get_deep_visibility`
- **Config**: Console URL, API Token
- **Use Case**: AI-powered EDR

#### Carbon Black 🔄 SCAFFOLD READY
- **Tools**: `cb_query_processes`, `cb_isolate_endpoint`, `cb_search_binaries`, `cb_live_response`
- **Config**: URL, Org Key, API ID, API Secret
- **Use Case**: Endpoint detection with detailed telemetry

### ☁️ Cloud Security (3 integrations)

#### AWS Security Hub 🔄 SCAFFOLD READY
- **Tools**: `aws_get_findings`, `aws_get_insights`, `aws_update_findings`, `aws_get_compliance_status`
- **Config**: Access Key ID, Secret Access Key, Region, Account ID
- **Library**: `boto3>=1.34.0`
- **Use Case**: AWS security findings and compliance

#### Azure Sentinel 🔄 SCAFFOLD READY
- **Tools**: `sentinel_query_logs`, `sentinel_get_incidents`, `sentinel_run_playbook`, `sentinel_update_incident`
- **Config**: Tenant ID, Client ID, Client Secret, Workspace ID
- **Library**: `azure-mgmt-sentinel>=1.0.0`
- **Use Case**: Cloud-native SIEM for Azure

#### GCP Security Command Center 🔄 SCAFFOLD READY
- **Tools**: `gcp_list_findings`, `gcp_list_assets`, `gcp_get_vulnerabilities`, `gcp_update_finding`
- **Config**: Project ID, Credentials File
- **Library**: `google-cloud-security-command-center>=1.23.0`
- **Use Case**: Google Cloud security management

### 🌐 Network Security (2 integrations)

#### Palo Alto Networks 🔄 SCAFFOLD READY
- **Tools**: `pan_get_threat_logs`, `pan_block_ip`, `pan_block_url`, `pan_get_wildfire_report`, `pan_create_security_policy`
- **Config**: Hostname, API Key, SSL Verification
- **Library**: `pan-os-python>=1.11.0`
- **Use Case**: Firewall management and threat prevention

#### Cisco Secure 🔄 SCAFFOLD READY
- **Tools**: `cisco_block_domain`, `cisco_get_security_events`, `cisco_get_network_activity`, `cisco_create_policy`
- **Config**: API URL, API Key, API Secret
- **Use Case**: DNS security and next-gen firewall

### 🔍 Vulnerability Management (2 integrations)

#### Tenable 🔄 SCAFFOLD READY
- **Tools**: `tenable_get_vulnerabilities`, `tenable_scan_asset`, `tenable_get_asset_info`, `tenable_export_scan`
- **Config**: Access Key, Secret Key, URL
- **Library**: `tenable-io>=1.16.0`
- **Use Case**: Vulnerability scanning and assessment

#### Qualys 🔄 SCAFFOLD READY
- **Tools**: `qualys_get_host_detections`, `qualys_launch_scan`, `qualys_get_compliance_posture`
- **Config**: API URL, Username, Password
- **Use Case**: Vulnerability and compliance scanning

### 🦠 Malware Analysis (3 integrations)

#### Hybrid Analysis 🔄 SCAFFOLD READY
- **Tools**: `ha_submit_file`, `ha_get_report`, `ha_search_hash`, `ha_get_similar_samples`
- **Config**: API Key
- **Use Case**: Automated malware sandbox

#### Joe Sandbox 🔄 SCAFFOLD READY
- **Tools**: `joe_submit_sample`, `joe_get_analysis`, `joe_search_behavior`, `joe_get_iocs`
- **Config**: API Key, API URL
- **Use Case**: Advanced malware sandbox

#### ANY.RUN 🔄 SCAFFOLD READY
- **Tools**: `anyrun_submit_file`, `anyrun_get_report`, `anyrun_search_tasks`
- **Config**: API Key
- **Use Case**: Interactive malware sandbox

### 🔐 Identity & Access (2 integrations)

#### Okta 🔄 SCAFFOLD READY
- **Tools**: `okta_get_user`, `okta_suspend_user`, `okta_reset_mfa`, `okta_get_auth_logs`, `okta_get_app_usage`
- **Config**: Domain, API Token
- **Use Case**: Identity and access management

#### Azure AD 🔄 SCAFFOLD READY
- **Tools**: `azuread_get_user`, `azuread_disable_user`, `azuread_get_signin_logs`, `azuread_get_risky_users`, `azuread_reset_password`
- **Config**: Tenant ID, Client ID, Client Secret
- **Use Case**: Microsoft identity platform

### 📧 Email Security (2 integrations)

#### Mimecast 🔄 SCAFFOLD READY
- **Tools**: `mimecast_get_held_messages`, `mimecast_release_message`, `mimecast_block_sender`, `mimecast_get_ttp_events`
- **Config**: Base URL, App ID, App Key, Access Key, Secret Key
- **Use Case**: Email security platform

#### Proofpoint 🔄 SCAFFOLD READY
- **Tools**: `pp_get_clicks_blocked`, `pp_get_messages_delivered`, `pp_get_threat_details`
- **Config**: API URL, Service Principal, Secret
- **Use Case**: Advanced email threat protection

### 🛠️ Data Storage (2 integrations)

#### Elasticsearch 🔄 SCAFFOLD READY
- **Tools**: `es_search`, `es_aggregate`, `es_get_document`, `es_bulk_query`, `es_create_index`
- **Config**: Hosts, Username, Password, SSL Settings
- **Library**: `elasticsearch>=8.10.0`
- **Use Case**: Advanced log search and analytics

#### PostgreSQL 🔄 SCAFFOLD READY
- **Tools**: `pg_query`, `pg_insert`, `pg_update`, `pg_create_table`, `pg_execute_procedure`
- **Config**: Host, Port, Database, Username, Password
- **Library**: `psycopg2-binary>=2.9.9`
- **Use Case**: Relational database for structured data

### 🔧 Utilities (3 integrations)

#### GitHub 🔄 SCAFFOLD READY
- **Tools**: `github_search_code`, `github_get_repo`, `github_create_issue`, `github_search_repositories`
- **Config**: Personal Access Token, Default Organization
- **Library**: `PyGithub>=2.1.1`
- **Use Case**: Code repository management, IOC tracking

#### IP Geolocation 🔄 SCAFFOLD READY
- **Tools**: `ipgeo_geolocate_ip`, `ipgeo_get_asn`, `ipgeo_get_abuse_contact`, `ipgeo_get_ip_reputation`
- **Config**: Service (IPinfo/MaxMind/IP2Location), API Key
- **Use Case**: IP address intelligence and geolocation

#### URL/Domain Analysis 🔄 SCAFFOLD READY
- **Tools**: `url_check_safety`, `url_get_whois`, `url_get_dns_records`, `url_check_ssl_cert`
- **Config**: None (uses public APIs)
- **Use Case**: URL and domain reputation analysis

## Implementation Status

| Status | Count | Description |
|--------|-------|-------------|
| ✅ Production Ready | 2 | Fully implemented and tested (VirusTotal, MISP) |
| 🔄 Scaffold Ready | 33 | Server structure created, needs tool implementation |
| ⏳ Planned | 0 | Not yet started |

## Using Integrations

### From Claude Desktop

Once configured and MCP servers are running:

```
You: "Check if this IP 192.168.1.100 is malicious on VirusTotal"
Claude: [Uses vt_check_ip tool]

You: "Search MISP for any events related to this hash: abc123..."
Claude: [Uses misp_search_attributes tool]

You: "Create a Jira ticket for this incident"
Claude: [Uses jira_create_issue tool]

You: "Send an alert to our security team on Slack"
Claude: [Uses slack_send_message tool]
```

### From Python

```python
from ui.integrations_config import IntegrationsConfigDialog

# Check if integration is enabled
if IntegrationsConfigDialog.is_integration_enabled('virustotal'):
    # Get configuration
    config = IntegrationsConfigDialog.get_integration_config('virustotal')
    api_key = config.get('api_key')
    
    # Use the integration
    # ...
```

## Security Notes

1. **Credentials Storage**: Sensitive data (API keys, passwords) stored in system keyring
2. **Config File**: Non-sensitive settings in `~/.deeptempo/integrations_config.json`
3. **Rate Limiting**: Implemented for APIs with rate limits (e.g., VirusTotal)
4. **SSL Verification**: Configurable per integration
5. **Access Control**: Only enabled integrations are exposed to Claude

## Development Guide

### Implementing a New Tool

For scaffold servers, implement tools by:

1. Open the server file: `mcp_servers/[integration]_server/server.py`
2. Find the tool handler with `# TODO: Implement [tool_name]`
3. Add implementation:

```python
if name == "tool_name":
    # Get required parameters
    param = arguments.get("param") if arguments else None
    
    if not param:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": "param is required"}, indent=2)
        )]
    
    # Call external API
    import requests
    
    api_key = config.get('api_key')
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(f"https://api.service.com/endpoint", headers=headers)
    response.raise_for_status()
    data = response.json()
    
    # Return results
    return [types.TextContent(
        type="text",
        text=json.dumps(data, indent=2)
    )]
```

4. Test the tool
5. Update this guide

### Adding a New Integration

1. Add to `ui/integrations_config.py`:
   - Add section in appropriate category tab
   - Define required fields

2. Create MCP server:
   ```bash
   # Add to scripts/generate_mcp_servers.py
   # Then run:
   python3 scripts/generate_mcp_servers.py
   ```

3. Add to `scripts/generate_mcp_config.py`:
   - Add entry in `integration_servers` dict

4. Add required library to `requirements.txt`

5. Implement tools in generated server file

6. Update documentation

## Troubleshooting

### Integration Not Working

1. Check if enabled:
   - Go to Settings → Integrations
   - Click "Configure Integrations"
   - Verify integration is checked

2. Check configuration:
   - Review credentials and settings
   - Click "Test Connection" if available

3. Check logs:
   - Application logs: `~/.deeptempo/app.log`
   - MCP server logs: Check MCP Manager

4. Regenerate MCP config:
   ```bash
   python3 scripts/generate_mcp_config.py
   ```

5. Restart MCP servers

### API Rate Limits

Some integrations have rate limits:
- **VirusTotal**: 4 requests/minute (free tier)
- **Shodan**: Varies by plan
- **Others**: Check provider documentation

Rate limiting is implemented where needed.

### Missing Libraries

If you get import errors:

```bash
# Install specific integration libraries
pip install pymisp pycti jira slack_sdk shodan

# Or install all optional dependencies
pip install -r requirements.txt
```

## Next Steps

1. **Configure Your Integrations**: Start with critical ones (VirusTotal, Jira, Slack)
2. **Implement Scaffold Tools**: Prioritize based on your needs
3. **Test Thoroughly**: Test each integration before production use
4. **Monitor Usage**: Track API usage and rate limits
5. **Extend**: Add custom integrations as needed

## Support

For issues or questions:
- Check logs: `~/.deeptempo/app.log`
- Review `IMPLEMENTATION_PLAN_MCP_SERVERS.md`
- Check individual server files for TODOs
- Consult integration provider documentation

## License

Same as main project (Apache 2.0)

