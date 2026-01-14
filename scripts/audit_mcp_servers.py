#!/usr/bin/env python3
"""
Audit MCP Server Implementation Status

This script analyzes all MCP servers to determine:
1. Which are fully implemented
2. Which are stubs (have TODOs)
3. Lines of code for each server
4. Tools exposed by each server
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def count_todos(file_path: str) -> int:
    """Count TODO comments in a file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            return len(re.findall(r'#\s*TODO', content, re.IGNORECASE))
    except Exception:
        return 0


def count_lines_of_code(file_path: str) -> int:
    """Count non-empty, non-comment lines of code."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            loc = 0
            for line in lines:
                stripped = line.strip()
                # Skip empty lines and comment-only lines
                if stripped and not stripped.startswith('#'):
                    loc += 1
            return loc
    except Exception:
        return 0


def extract_tools(file_path: str) -> List[str]:
    """Extract tool names from server.py file."""
    tools = []
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            # Look for Tool definitions with name parameter
            tool_matches = re.findall(r'types\.Tool\s*\(\s*name=["\']([^"\']+)["\']', content)
            tools = tool_matches
    except Exception:
        pass
    return tools


def get_server_status(server_path: Path) -> Dict:
    """Analyze a single MCP server directory."""
    server_file = server_path / "server.py"
    
    if not server_file.exists():
        return {
            "name": server_path.name,
            "status": "missing",
            "todos": 0,
            "loc": 0,
            "tools": [],
            "notes": "No server.py file found"
        }
    
    todos = count_todos(str(server_file))
    loc = count_lines_of_code(str(server_file))
    tools = extract_tools(str(server_file))
    
    # Determine status
    if todos == 0 and loc > 100:
        status = "implemented"
        status_color = Colors.GREEN
    elif todos > 5 or loc < 100:
        status = "stub"
        status_color = Colors.RED
    else:
        status = "partial"
        status_color = Colors.YELLOW
    
    return {
        "name": server_path.name,
        "status": status,
        "status_color": status_color,
        "todos": todos,
        "loc": loc,
        "tools": tools,
        "tools_count": len(tools),
        "notes": ""
    }


def categorize_servers() -> Dict[str, List[str]]:
    """Categorize servers by type."""
    return {
        "Custom Business Logic": [
            "approval_server",
            "case_store_server",
            "deeptempo_findings_server",
            "evidence_snippets_server",
            "tempo_flow_server"
        ],
        "Infrastructure & Development": [
            "github_server",
            "postgresql_server",
            "elasticsearch_server"
        ],
        "Communication": [
            "slack_server",
            "microsoft_teams_server",
            "email_server"
        ],
        "Ticketing & Incident Management": [
            "jira_server",
            "servicenow_server",
            "pagerduty_server"
        ],
        "Cloud Platforms": [
            "aws_security_hub_server",
            "azure_ad_server",
            "azure_sentinel_server",
            "gcp_security_server"
        ],
        "Identity & Access": [
            "okta_server"
        ],
        "EDR/XDR": [
            "crowdstrike_server",
            "microsoft_defender_server",
            "sentinelone_server",
            "carbon_black_server",
            "cisco_secure_server"
        ],
        "SIEM": [
            "splunk_server"
        ],
        "Email Security": [
            "proofpoint_server",
            "mimecast_server"
        ],
        "Vulnerability Management": [
            "qualys_server",
            "tenable_server"
        ],
        "Network Security": [
            "palo_alto_server"
        ],
        "Threat Intelligence": [
            "virustotal_server",
            "alienvault_otx_server",
            "shodan_server",
            "misp_server",
            "opencti_server",
            "threatconnect_server",
            "url_analysis_server",
            "ip_geolocation_server"
        ],
        "Sandbox Analysis": [
            "hybrid_analysis_server",
            "joe_sandbox_server",
            "anyrun_server"
        ]
    }


def main():
    """Main audit function."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}MCP Server Implementation Audit{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    mcp_servers_dir = project_root / "mcp_servers"
    
    if not mcp_servers_dir.exists():
        print(f"{Colors.RED}Error: mcp_servers directory not found!{Colors.RESET}")
        return
    
    # Get all server directories
    server_dirs = [d for d in mcp_servers_dir.iterdir() 
                   if d.is_dir() and not d.name.startswith('_')]
    
    # Analyze each server
    servers_data = []
    for server_dir in sorted(server_dirs):
        status = get_server_status(server_dir)
        servers_data.append(status)
    
    # Categorize and display results
    categories = categorize_servers()
    
    implemented_count = 0
    partial_count = 0
    stub_count = 0
    total_loc = 0
    total_tools = 0
    
    for category, server_names in categories.items():
        print(f"\n{Colors.BOLD}{Colors.BLUE}{category}{Colors.RESET}")
        print(f"{Colors.BLUE}{'-' * len(category)}{Colors.RESET}")
        
        for server_name in server_names:
            # Find server data
            server_data = next((s for s in servers_data if s['name'] == server_name), None)
            
            if not server_data:
                print(f"  {Colors.RED}✗{Colors.RESET} {server_name:<40} NOT FOUND")
                continue
            
            status = server_data['status']
            status_color = server_data.get('status_color', Colors.RESET)
            todos = server_data['todos']
            loc = server_data['loc']
            tools_count = server_data['tools_count']
            
            # Update counts
            total_loc += loc
            total_tools += tools_count
            
            if status == "implemented":
                icon = f"{Colors.GREEN}✓{Colors.RESET}"
                implemented_count += 1
            elif status == "partial":
                icon = f"{Colors.YELLOW}◐{Colors.RESET}"
                partial_count += 1
            else:
                icon = f"{Colors.RED}✗{Colors.RESET}"
                stub_count += 1
            
            # Format output
            status_text = f"{status_color}{status.upper():<12}{Colors.RESET}"
            loc_text = f"{loc:>4} LOC"
            tools_text = f"{tools_count:>2} tools"
            todos_text = f"{todos:>2} TODOs" if todos > 0 else "       "
            
            print(f"  {icon} {server_name:<35} {status_text} {loc_text}  {tools_text}  {todos_text}")
    
    # Summary statistics
    total_servers = len(servers_data)
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}Summary Statistics{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")
    
    print(f"  Total Servers:       {total_servers}")
    print(f"  {Colors.GREEN}✓ Implemented:{Colors.RESET}       {implemented_count} ({implemented_count/total_servers*100:.1f}%)")
    print(f"  {Colors.YELLOW}◐ Partial:{Colors.RESET}           {partial_count} ({partial_count/total_servers*100:.1f}%)")
    print(f"  {Colors.RED}✗ Stub/Incomplete:{Colors.RESET}   {stub_count} ({stub_count/total_servers*100:.1f}%)")
    print(f"  Total Lines of Code: {total_loc:,}")
    print(f"  Total Tools Exposed: {total_tools}")
    print(f"  Avg LOC per Server:  {total_loc/total_servers:.0f}")
    print(f"  Avg Tools per Server: {total_tools/total_servers:.1f}")
    
    # Recommendations
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}Recommendations{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")
    
    # Find stub servers that could be replaced
    stub_servers = [s for s in servers_data if s['status'] == 'stub']
    
    replaceable_servers = {
        "github_server": "@modelcontextprotocol/server-github",
        "postgresql_server": "@modelcontextprotocol/server-postgres",
    }
    
    print(f"{Colors.BOLD}High Priority Actions:{Colors.RESET}\n")
    
    action_num = 1
    for server in stub_servers:
        server_name = server['name']
        if server_name in replaceable_servers:
            replacement = replaceable_servers[server_name]
            print(f"  {action_num}. {Colors.YELLOW}REPLACE{Colors.RESET} {server_name}")
            print(f"     → Use community server: {Colors.GREEN}{replacement}{Colors.RESET}")
            action_num += 1
    
    # Servers to implement
    priority_servers = ["crowdstrike_server", "splunk_server"]
    for server in stub_servers:
        if server['name'] in priority_servers:
            print(f"  {action_num}. {Colors.BLUE}IMPLEMENT{Colors.RESET} {server['name']}")
            print(f"     → High-value integration for SOC operations")
            action_num += 1
    
    # Servers to remove
    low_priority_stubs = [s for s in stub_servers 
                          if s['name'] not in replaceable_servers 
                          and s['name'] not in priority_servers
                          and s['loc'] < 200]
    
    if low_priority_stubs:
        print(f"  {action_num}. {Colors.RED}EVALUATE FOR REMOVAL{Colors.RESET} ({len(low_priority_stubs)} servers)")
        print(f"     → Stub servers with <200 LOC that may not be needed:")
        for server in low_priority_stubs[:5]:  # Show first 5
            print(f"       - {server['name']}")
        if len(low_priority_stubs) > 5:
            print(f"       ... and {len(low_priority_stubs) - 5} more")
    
    # Export to JSON for further processing
    output_file = project_root / "mcp_server_audit.json"
    with open(output_file, 'w') as f:
        json.dump(servers_data, f, indent=2)
    
    print(f"\n{Colors.GREEN}✓ Audit complete! Results saved to:{Colors.RESET} {output_file}\n")
    
    # Export recommendations to markdown
    recommendations_file = project_root / "MCP_AUDIT_RECOMMENDATIONS.md"
    with open(recommendations_file, 'w') as f:
        f.write("# MCP Server Audit Recommendations\n\n")
        f.write(f"**Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Total Servers: {total_servers}\n")
        f.write(f"- ✓ Implemented: {implemented_count} ({implemented_count/total_servers*100:.1f}%)\n")
        f.write(f"- ◐ Partial: {partial_count} ({partial_count/total_servers*100:.1f}%)\n")
        f.write(f"- ✗ Stub: {stub_count} ({stub_count/total_servers*100:.1f}%)\n\n")
        
        f.write("## High Priority Actions\n\n")
        
        f.write("### 1. Replace with Community Servers\n\n")
        for server_name, replacement in replaceable_servers.items():
            server = next((s for s in servers_data if s['name'] == server_name), None)
            if server and server['status'] == 'stub':
                f.write(f"- **{server_name}**\n")
                f.write(f"  - Current Status: Stub ({server['loc']} LOC, {server['todos']} TODOs)\n")
                f.write(f"  - Replacement: `{replacement}`\n")
                f.write(f"  - Action: Install and configure community server\n\n")
        
        f.write("### 2. Implement Priority Servers\n\n")
        for server_name in priority_servers:
            server = next((s for s in servers_data if s['name'] == server_name), None)
            if server and server['status'] == 'stub':
                f.write(f"- **{server_name}**\n")
                f.write(f"  - Current Status: Stub ({server['loc']} LOC, {server['todos']} TODOs)\n")
                f.write(f"  - Action: Fully implement integration\n")
                f.write(f"  - Rationale: Critical for SOC operations\n\n")
        
        f.write("### 3. Evaluate Stub Servers\n\n")
        for server in low_priority_stubs:
            f.write(f"- **{server['name']}** - {server['loc']} LOC, {server['tools_count']} tools\n")
        
        f.write(f"\n## Detailed Server Status\n\n")
        for category, server_names in categories.items():
            f.write(f"\n### {category}\n\n")
            for server_name in server_names:
                server = next((s for s in servers_data if s['name'] == server_name), None)
                if server:
                    f.write(f"- **{server_name}**: {server['status'].upper()} "
                           f"({server['loc']} LOC, {server['tools_count']} tools, "
                           f"{server['todos']} TODOs)\n")
    
    print(f"{Colors.GREEN}✓ Recommendations saved to:{Colors.RESET} {recommendations_file}\n")


if __name__ == "__main__":
    main()

