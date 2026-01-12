"""Generate scaffolding for all MCP servers based on configuration."""

import os
from pathlib import Path

# MCP Server definitions
MCP_SERVERS = {
    # Tier 1 - Threat Intel (already created: virustotal, misp)
    "opencti": {
        "name": "OpenCTI",
        "description": "Structured threat intelligence platform",
        "tools": [
            ("opencti_query_indicators", "Query indicators of compromise from OpenCTI"),
            ("opencti_get_reports", "Get threat intelligence reports"),
            ("opencti_search_threat_actors", "Search for threat actor information"),
            ("opencti_create_observable", "Create a new observable in OpenCTI")
        ]
    },
    
    # Tier 1 - Ticketing
    "jira": {
        "name": "Jira",
        "description": "Atlassian Jira for ticket management",
        "tools": [
            ("jira_create_issue", "Create a new Jira issue/ticket"),
            ("jira_update_issue", "Update an existing Jira issue"),
            ("jira_search_issues", "Search for Jira issues"),
            ("jira_add_comment", "Add a comment to a Jira issue"),
            ("jira_transition_issue", "Transition issue workflow state")
        ]
    },
    "pagerduty": {
        "name": "PagerDuty",
        "description": "Alerting and on-call management",
        "tools": [
            ("pd_create_incident", "Create a PagerDuty incident"),
            ("pd_acknowledge_incident", "Acknowledge an incident"),
            ("pd_get_on_call", "Get current on-call information"),
            ("pd_trigger_escalation", "Trigger escalation policy")
        ]
    },
    "servicenow": {
        "name": "ServiceNow",
        "description": "Enterprise ITSM integration",
        "tools": [
            ("snow_create_incident", "Create a ServiceNow incident"),
            ("snow_update_incident", "Update an existing incident"),
            ("snow_create_change_request", "Create a change request"),
            ("snow_query_cmdb", "Query the Configuration Management Database")
        ]
    },
    
    # Tier 1 - Communications
    "slack": {
        "name": "Slack",
        "description": "Real-time team collaboration",
        "tools": [
            ("slack_send_message", "Send a message to a Slack channel"),
            ("slack_create_channel", "Create a new Slack channel"),
            ("slack_upload_file", "Upload a file to Slack"),
            ("slack_search_messages", "Search Slack messages")
        ]
    },
    "microsoft_teams": {
        "name": "Microsoft Teams",
        "description": "Enterprise collaboration platform",
        "tools": [
            ("teams_send_message", "Send a message to a Teams channel"),
            ("teams_create_channel", "Create a new Teams channel"),
            ("teams_post_card", "Post an adaptive card to Teams")
        ]
    },
    "email": {
        "name": "Email",
        "description": "Email-based alerting and reporting",
        "tools": [
            ("email_send", "Send an email"),
            ("email_send_report", "Send a formatted report via email"),
            ("email_send_alert_digest", "Send a digest of alerts")
        ]
    },
    
    # Tier 2 - EDR/XDR
    "microsoft_defender": {
        "name": "Microsoft Defender for Endpoint",
        "description": "Windows endpoint protection",
        "tools": [
            ("defender_get_alerts", "Get Defender alerts"),
            ("defender_isolate_machine", "Isolate an endpoint"),
            ("defender_run_antivirus_scan", "Run antivirus scan on endpoint"),
            ("defender_get_machine_info", "Get endpoint information"),
            ("defender_get_vulnerabilities", "Get endpoint vulnerabilities")
        ]
    },
    "sentinelone": {
        "name": "SentinelOne",
        "description": "AI-powered endpoint detection and response",
        "tools": [
            ("s1_get_threats", "Get SentinelOne threats"),
            ("s1_isolate_endpoint", "Isolate an endpoint"),
            ("s1_remediate_threat", "Remediate a detected threat"),
            ("s1_get_deep_visibility", "Get deep visibility data")
        ]
    },
    "carbon_black": {
        "name": "Carbon Black",
        "description": "Endpoint detection and response",
        "tools": [
            ("cb_query_processes", "Query process execution data"),
            ("cb_isolate_endpoint", "Isolate an endpoint"),
            ("cb_search_binaries", "Search for binary files"),
            ("cb_live_response", "Execute live response session")
        ]
    },
    
    # Tier 2 - Cloud Security
    "aws_security_hub": {
        "name": "AWS Security Hub",
        "description": "AWS security findings aggregation",
        "tools": [
            ("aws_get_findings", "Get AWS Security Hub findings"),
            ("aws_get_insights", "Get security insights"),
            ("aws_update_findings", "Update finding status"),
            ("aws_get_compliance_status", "Get compliance status")
        ]
    },
    "azure_sentinel": {
        "name": "Azure Sentinel",
        "description": "Cloud-native SIEM",
        "tools": [
            ("sentinel_query_logs", "Query Azure Sentinel logs"),
            ("sentinel_get_incidents", "Get Sentinel incidents"),
            ("sentinel_run_playbook", "Run a Sentinel playbook"),
            ("sentinel_update_incident", "Update incident status")
        ]
    },
    "gcp_security": {
        "name": "GCP Security Command Center",
        "description": "Google Cloud security management",
        "tools": [
            ("gcp_list_findings", "List GCP security findings"),
            ("gcp_list_assets", "List GCP assets"),
            ("gcp_get_vulnerabilities", "Get vulnerability data"),
            ("gcp_update_finding", "Update finding status")
        ]
    },
    
    # Tier 2 - Network Security
    "palo_alto": {
        "name": "Palo Alto Networks",
        "description": "Firewall and threat prevention",
        "tools": [
            ("pan_get_threat_logs", "Get threat prevention logs"),
            ("pan_block_ip", "Block an IP address"),
            ("pan_block_url", "Block a URL"),
            ("pan_get_wildfire_report", "Get WildFire malware analysis"),
            ("pan_create_security_policy", "Create security policy")
        ]
    },
    "cisco_secure": {
        "name": "Cisco Secure",
        "description": "Network security and DNS protection",
        "tools": [
            ("cisco_block_domain", "Block a domain via Umbrella"),
            ("cisco_get_security_events", "Get security events"),
            ("cisco_get_network_activity", "Get network activity"),
            ("cisco_create_policy", "Create security policy")
        ]
    },
    
    # Tier 2 - Vulnerability Management
    "tenable": {
        "name": "Tenable",
        "description": "Vulnerability scanning and assessment",
        "tools": [
            ("tenable_get_vulnerabilities", "Get vulnerability data"),
            ("tenable_scan_asset", "Scan an asset"),
            ("tenable_get_asset_info", "Get asset information"),
            ("tenable_export_scan", "Export scan results")
        ]
    },
    "qualys": {
        "name": "Qualys",
        "description": "Vulnerability and compliance scanning",
        "tools": [
            ("qualys_get_host_detections", "Get host vulnerability detections"),
            ("qualys_launch_scan", "Launch a vulnerability scan"),
            ("qualys_get_compliance_posture", "Get compliance posture")
        ]
    },
    
    # Tier 3 - Malware Analysis
    "hybrid_analysis": {
        "name": "Hybrid Analysis",
        "description": "Automated malware sandbox",
        "tools": [
            ("ha_submit_file", "Submit file for analysis"),
            ("ha_get_report", "Get analysis report"),
            ("ha_search_hash", "Search for hash"),
            ("ha_get_similar_samples", "Get similar malware samples")
        ]
    },
    "joe_sandbox": {
        "name": "Joe Sandbox",
        "description": "Advanced malware sandbox",
        "tools": [
            ("joe_submit_sample", "Submit malware sample"),
            ("joe_get_analysis", "Get analysis results"),
            ("joe_search_behavior", "Search behavior patterns"),
            ("joe_get_iocs", "Extract IOCs from analysis")
        ]
    },
    "anyrun": {
        "name": "ANY.RUN",
        "description": "Interactive malware sandbox",
        "tools": [
            ("anyrun_submit_file", "Submit file for analysis"),
            ("anyrun_get_report", "Get analysis report"),
            ("anyrun_search_tasks", "Search analysis tasks")
        ]
    },
    
    # Tier 3 - Additional Threat Feeds
    "alienvault_otx": {
        "name": "AlienVault OTX",
        "description": "Open threat exchange",
        "tools": [
            ("otx_get_pulses", "Get threat intelligence pulses"),
            ("otx_search_indicators", "Search for indicators"),
            ("otx_get_ioc_reputation", "Get IOC reputation")
        ]
    },
    "threatconnect": {
        "name": "ThreatConnect",
        "description": "Commercial threat intelligence platform",
        "tools": [
            ("tc_query_indicators", "Query threat indicators"),
            ("tc_get_groups", "Get threat groups"),
            ("tc_create_indicator", "Create new indicator"),
            ("tc_add_tag", "Add tag to indicator")
        ]
    },
    "shodan": {
        "name": "Shodan",
        "description": "Internet-connected device search",
        "tools": [
            ("shodan_search_ip", "Search for IP address information"),
            ("shodan_search_exploits", "Search for exploits"),
            ("shodan_get_host_info", "Get detailed host information"),
            ("shodan_search_vulnerabilities", "Search for vulnerabilities")
        ]
    },
    
    # Tier 3 - Identity
    "okta": {
        "name": "Okta",
        "description": "Identity and access management",
        "tools": [
            ("okta_get_user", "Get user information"),
            ("okta_suspend_user", "Suspend a user account"),
            ("okta_reset_mfa", "Reset user MFA"),
            ("okta_get_auth_logs", "Get authentication logs"),
            ("okta_get_app_usage", "Get application usage")
        ]
    },
    "azure_ad": {
        "name": "Azure Active Directory",
        "description": "Microsoft identity platform",
        "tools": [
            ("azuread_get_user", "Get user information"),
            ("azuread_disable_user", "Disable a user account"),
            ("azuread_get_signin_logs", "Get sign-in logs"),
            ("azuread_get_risky_users", "Get risky users"),
            ("azuread_reset_password", "Reset user password")
        ]
    },
    
    # Tier 3 - Data Storage
    "elasticsearch": {
        "name": "Elasticsearch",
        "description": "Advanced log search and analytics",
        "tools": [
            ("es_search", "Search Elasticsearch"),
            ("es_aggregate", "Run aggregation query"),
            ("es_get_document", "Get specific document"),
            ("es_bulk_query", "Run bulk query"),
            ("es_create_index", "Create new index")
        ]
    },
    "postgresql": {
        "name": "PostgreSQL",
        "description": "Relational database",
        "tools": [
            ("pg_query", "Execute SQL query"),
            ("pg_insert", "Insert data"),
            ("pg_update", "Update data"),
            ("pg_create_table", "Create table"),
            ("pg_execute_procedure", "Execute stored procedure")
        ]
    },
    
    # Tier 3 - Email Security
    "mimecast": {
        "name": "Mimecast",
        "description": "Email security platform",
        "tools": [
            ("mimecast_get_held_messages", "Get held messages"),
            ("mimecast_release_message", "Release held message"),
            ("mimecast_block_sender", "Block email sender"),
            ("mimecast_get_ttp_events", "Get targeted threat protection events")
        ]
    },
    "proofpoint": {
        "name": "Proofpoint",
        "description": "Advanced email threat protection",
        "tools": [
            ("pp_get_clicks_blocked", "Get blocked clicks"),
            ("pp_get_messages_delivered", "Get delivered messages"),
            ("pp_get_threat_details", "Get threat details")
        ]
    },
    
    # Tier 4 - Utilities
    "github": {
        "name": "GitHub",
        "description": "Code repository management",
        "tools": [
            ("github_search_code", "Search code repositories"),
            ("github_get_repo", "Get repository information"),
            ("github_create_issue", "Create GitHub issue"),
            ("github_search_repositories", "Search repositories")
        ]
    },
    "ip_geolocation": {
        "name": "IP Geolocation",
        "description": "IP address intelligence",
        "tools": [
            ("ipgeo_geolocate_ip", "Get IP geolocation"),
            ("ipgeo_get_asn", "Get ASN information"),
            ("ipgeo_get_abuse_contact", "Get abuse contact"),
            ("ipgeo_get_ip_reputation", "Get IP reputation")
        ]
    },
    "url_analysis": {
        "name": "URL/Domain Analysis",
        "description": "URL and domain reputation",
        "tools": [
            ("url_check_safety", "Check URL safety"),
            ("url_get_whois", "Get WHOIS information"),
            ("url_get_dns_records", "Get DNS records"),
            ("url_check_ssl_cert", "Check SSL certificate")
        ]
    }
}

SERVER_TEMPLATE = '''"""MCP Server for {name} integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_{id}_config():
    """Get {name} configuration from integrations config."""
    try:
        from ui.integrations_config import IntegrationsConfigDialog
        config = IntegrationsConfigDialog.get_integration_config('{id}')
        return config
    except Exception as e:
        logger.error(f"Error loading {name} config: {{e}}")
        return {{}}

server = Server("{id}-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available {name} tools."""
    return [{tools_list}
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_{id}_config()
    
    if not config:
        return [types.TextContent(
            type="text",
            text=json.dumps({{
                "error": "{name} not configured",
                "message": "Please configure {name} in Settings > Integrations"
            }}, indent=2)
        )]
    
    try:
        # TODO: Implement tool handlers
        {tool_handlers}
        
        raise ValueError(f"Unknown tool: {{name}}")
    
    except Exception as e:
        logger.error(f"Error in {name} tool {{name}}: {{e}}")
        return [types.TextContent(
            type="text",
            text=json.dumps({{
                "error": str(e),
                "tool": name
            }}, indent=2)
        )]

async def main():
    """Run the {name} MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="{id}-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={{}},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
'''

def generate_server(server_id: str, config: dict):
    """Generate an MCP server implementation."""
    name = config['name']
    description = config['description']
    tools = config['tools']
    
    # Generate tools list
    tools_list_items = []
    tool_handlers_items = []
    
    for tool_name, tool_desc in tools:
        tool_def = f'''
        types.Tool(
            name="{tool_name}",
            description="{tool_desc}",
            inputSchema={{
                "type": "object",
                "properties": {{
                    # TODO: Define tool parameters
                }},
                "required": []
            }}
        )'''
        tools_list_items.append(tool_def)
        
        # Generate tool handler stub
        handler = f'''
        if name == "{tool_name}":
            # TODO: Implement {tool_name}
            return [types.TextContent(
                type="text",
                text=json.dumps({{
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }}, indent=2)
            )]
        '''
        tool_handlers_items.append(handler)
    
    tools_list_str = ','.join(tools_list_items)
    tool_handlers_str = '\n'.join(tool_handlers_items)
    
    # Generate server code
    server_code = SERVER_TEMPLATE.format(
        name=name,
        id=server_id,
        description=description,
        tools_list=tools_list_str,
        tool_handlers=tool_handlers_str
    )
    
    # Create directory and files
    server_dir = Path(f"mcp_servers/{server_id}_server")
    server_dir.mkdir(parents=True, exist_ok=True)
    
    # Write __init__.py
    init_file = server_dir / "__init__.py"
    init_file.write_text(f'"""{name} MCP Server for {description}."""\n')
    
    # Write server.py
    server_file = server_dir / "server.py"
    server_file.write_text(server_code)
    
    print(f"✓ Generated {name} server at {server_dir}")

def main():
    """Generate all MCP servers."""
    print("Generating MCP server scaffolding...")
    print(f"Total servers to generate: {len(MCP_SERVERS)}\n")
    
    for server_id, config in MCP_SERVERS.items():
        # Skip already created servers
        server_dir = Path(f"mcp_servers/{server_id}_server")
        if server_dir.exists() and server_id not in ['opencti']:  # Allow opencti to be regenerated
            print(f"⊙ Skipping {config['name']} (already exists)")
            continue
        
        generate_server(server_id, config)
    
    print(f"\n✓ Server scaffolding generation complete!")
    print(f"\nNext steps:")
    print("1. Review generated servers in mcp_servers/")
    print("2. Implement TODO sections for each tool")
    print("3. Add required libraries to requirements.txt")
    print("4. Update mcp-config.json")
    print("5. Test each server")

if __name__ == "__main__":
    main()

