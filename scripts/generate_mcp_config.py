"""Generate MCP configuration dynamically based on enabled integrations."""

import json
from pathlib import Path

def get_enabled_integrations():
    """Get list of enabled integrations from config."""
    config_file = Path.home() / '.deeptempo' / 'integrations_config.json'
    
    if not config_file.exists():
        print("No integrations config found. Using default core servers.")
        return []
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config.get('enabled_integrations', [])
    except Exception as e:
        print(f"Error loading integrations config: {e}")
        return []

def generate_mcp_config():
    """Generate mcp-config.json based on enabled integrations."""
    
    # Core MCP servers (always included)
    core_servers = {
        "deeptempo-findings": {
            "command": "python",
            "args": ["-m", "mcp_servers.deeptempo_findings_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "evidence-snippets": {
            "command": "python",
            "args": ["-m", "mcp_servers.evidence_snippets_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "case-store": {
            "command": "python",
            "args": ["-m", "mcp_servers.case_store_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "tempo-flow": {
            "command": "python",
            "args": ["-m", "mcp_servers.tempo_flow_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "crowdstrike": {
            "command": "python",
            "args": ["-m", "mcp_servers.crowdstrike_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "splunk": {
            "command": "python",
            "args": ["-m", "mcp_servers.splunk_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "approval": {
            "command": "python",
            "args": ["-m", "mcp_servers.approval_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        }
    }
    
    # Integration server mappings
    integration_servers = {
        # Threat Intelligence
        "virustotal": {
            "command": "python",
            "args": ["-m", "mcp_servers.virustotal_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "misp": {
            "command": "python",
            "args": ["-m", "mcp_servers.misp_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "opencti": {
            "command": "python",
            "args": ["-m", "mcp_servers.opencti_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "alienvault_otx": {
            "command": "python",
            "args": ["-m", "mcp_servers.alienvault_otx_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "threatconnect": {
            "command": "python",
            "args": ["-m", "mcp_servers.threatconnect_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "shodan": {
            "command": "python",
            "args": ["-m", "mcp_servers.shodan_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        
        # Incident Management
        "jira": {
            "command": "python",
            "args": ["-m", "mcp_servers.jira_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "pagerduty": {
            "command": "python",
            "args": ["-m", "mcp_servers.pagerduty_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "servicenow": {
            "command": "python",
            "args": ["-m", "mcp_servers.servicenow_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        
        # Communications
        "slack": {
            "command": "python",
            "args": ["-m", "mcp_servers.slack_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "microsoft_teams": {
            "command": "python",
            "args": ["-m", "mcp_servers.microsoft_teams_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "email": {
            "command": "python",
            "args": ["-m", "mcp_servers.email_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        
        # EDR/XDR
        "microsoft_defender": {
            "command": "python",
            "args": ["-m", "mcp_servers.microsoft_defender_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "sentinelone": {
            "command": "python",
            "args": ["-m", "mcp_servers.sentinelone_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "carbon_black": {
            "command": "python",
            "args": ["-m", "mcp_servers.carbon_black_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        
        # Cloud Security
        "aws_security_hub": {
            "command": "python",
            "args": ["-m", "mcp_servers.aws_security_hub_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "azure_sentinel": {
            "command": "python",
            "args": ["-m", "mcp_servers.azure_sentinel_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "gcp_security": {
            "command": "python",
            "args": ["-m", "mcp_servers.gcp_security_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        
        # Network Security
        "palo_alto": {
            "command": "python",
            "args": ["-m", "mcp_servers.palo_alto_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "cisco_secure": {
            "command": "python",
            "args": ["-m", "mcp_servers.cisco_secure_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        
        # Vulnerability Management
        "tenable": {
            "command": "python",
            "args": ["-m", "mcp_servers.tenable_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "qualys": {
            "command": "python",
            "args": ["-m", "mcp_servers.qualys_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        
        # Malware Analysis
        "hybrid_analysis": {
            "command": "python",
            "args": ["-m", "mcp_servers.hybrid_analysis_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "joe_sandbox": {
            "command": "python",
            "args": ["-m", "mcp_servers.joe_sandbox_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "anyrun": {
            "command": "python",
            "args": ["-m", "mcp_servers.anyrun_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        
        # Identity & Access
        "okta": {
            "command": "python",
            "args": ["-m", "mcp_servers.okta_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "azure_ad": {
            "command": "python",
            "args": ["-m", "mcp_servers.azure_ad_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        
        # Data Storage
        "elasticsearch": {
            "command": "python",
            "args": ["-m", "mcp_servers.elasticsearch_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "postgresql": {
            "command": "python",
            "args": ["-m", "mcp_servers.postgresql_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        
        # Email Security
        "mimecast": {
            "command": "python",
            "args": ["-m", "mcp_servers.mimecast_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "proofpoint": {
            "command": "python",
            "args": ["-m", "mcp_servers.proofpoint_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        
        # Utilities
        "github": {
            "command": "python",
            "args": ["-m", "mcp_servers.github_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "ip_geolocation": {
            "command": "python",
            "args": ["-m", "mcp_servers.ip_geolocation_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        },
        "url_analysis": {
            "command": "python",
            "args": ["-m", "mcp_servers.url_analysis_server.server"],
            "cwd": "${workspaceFolder}",
            "env": {}
        }
    }
    
    # Build final config
    mcp_servers = core_servers.copy()
    
    # Add enabled integration servers
    enabled = get_enabled_integrations()
    for integration_id in enabled:
        if integration_id in integration_servers:
            mcp_servers[integration_id] = integration_servers[integration_id]
            print(f"  + Added {integration_id} server")
    
    config = {
        "mcpServers": mcp_servers
    }
    
    return config

def main():
    """Generate and save MCP configuration."""
    print("Generating MCP configuration...")
    print()
    
    config = generate_mcp_config()
    
    # Save to mcp-config.json
    output_file = Path("mcp-config.json")
    with open(output_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    total_servers = len(config['mcpServers'])
    core_count = 7  # Core servers
    integration_count = total_servers - core_count
    
    print()
    print(f"✓ MCP configuration generated successfully!")
    print(f"  - Total servers: {total_servers}")
    print(f"  - Core servers: {core_count}")
    print(f"  - Integration servers: {integration_count}")
    print(f"  - Saved to: {output_file}")
    print()
    print("Note: This configuration uses ${workspaceFolder} placeholder.")
    print("Replace with actual paths when deploying to Claude Desktop.")

if __name__ == "__main__":
    main()

