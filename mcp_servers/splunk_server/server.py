"""MCP Server for Splunk integration with natural language query generation."""

import asyncio
import logging
import json
import os
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

# Splunk configuration from environment or config
def get_splunk_config():
    """Get Splunk configuration from environment or config file."""
    from pathlib import Path
    import json
    
    config = {
        "server_url": os.environ.get("SPLUNK_URL"),
        "username": os.environ.get("SPLUNK_USERNAME"),
        "password": os.environ.get("SPLUNK_PASSWORD"),
        "verify_ssl": os.environ.get("SPLUNK_VERIFY_SSL", "false").lower() == "true"
    }
    
    # Try to load from config file if env vars not set
    if not config["server_url"]:
        config_file = Path.home() / ".deeptempo" / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    splunk_config = file_config.get("splunk", {})
                    config.update({
                        "server_url": splunk_config.get("server_url"),
                        "username": splunk_config.get("username"),
                        "password": splunk_config.get("password"),
                        "verify_ssl": splunk_config.get("verify_ssl", False)
                    })
            except Exception as e:
                logger.warning(f"Could not load config from file: {e}")
    
    return config

def get_splunk_service():
    """Get configured Splunk service instance."""
    try:
        from services.splunk_service import SplunkService
        config = get_splunk_config()
        
        if not config.get("server_url"):
            return None
            
        return SplunkService(
            server_url=config["server_url"],
            username=config["username"],
            password=config["password"],
            verify_ssl=config["verify_ssl"]
        )
    except Exception as e:
        logger.error(f"Error creating Splunk service: {e}")
        return None

# Mock SPL generation for demo (in production, this would call Claude)
def generate_spl_from_natural_language(query: str, indexes: Optional[list] = None) -> dict:
    """
    Generate SPL query from natural language.
    In production, this would use Claude API to translate.
    """
    query_lower = query.lower()
    
    # Simple pattern matching for demo
    spl_templates = {
        "failed login": 'index=* (failed OR failure) (login OR logon OR authentication) | stats count by src_ip, user | sort -count',
        "powershell": 'index=* sourcetype=WinEventLog:Security EventCode=4688 (powershell.exe OR pwsh.exe) | table _time, Computer, User, CommandLine',
        "brute force": 'index=* (failed OR failure) (login OR authentication) | stats count by src_ip | where count > 10 | sort -count',
        "c2 beacon": 'index=* sourcetype=firewall action=allowed | stats count by dest_ip, dest_port | where count > 100 | sort -count',
        "data exfiltration": 'index=* (upload OR POST OR exfil) | stats sum(bytes_out) as total_bytes by src_ip, dest_ip | where total_bytes > 1000000000 | sort -total_bytes',
        "lateral movement": 'index=* (EventCode=4624 OR EventCode=4648 OR psexec OR wmic) Logon_Type=3 | stats dc(dest) as unique_hosts by user | where unique_hosts > 5',
        "suspicious process": 'index=* sourcetype=sysmon EventCode=1 (cmd.exe OR powershell.exe OR wscript.exe OR cscript.exe) | table _time, Computer, User, Image, CommandLine, ParentImage',
        "network scan": 'index=* sourcetype=firewall | stats dc(dest_ip) as unique_destinations by src_ip | where unique_destinations > 100 | sort -unique_destinations',
        "malware execution": 'index=* (virus OR malware OR trojan OR ransomware OR suspicious) | table _time, host, process, file_path, signature',
        "privilege escalation": 'index=* (EventCode=4672 OR EventCode=4673 OR sudo OR runas) | table _time, user, dest, CommandLine'
    }
    
    # Find matching template
    spl_query = None
    matched_pattern = None
    for pattern, template in spl_templates.items():
        if pattern in query_lower:
            spl_query = template
            matched_pattern = pattern
            break
    
    # Default query if no match
    if not spl_query:
        # Extract potential search terms
        search_terms = query_lower.replace("show me", "").replace("find", "").replace("search for", "").strip()
        spl_query = f'index=* {search_terms} | head 100'
        matched_pattern = "generic search"
    
    # Add index restriction if specified
    if indexes:
        index_clause = "index=" + " OR index=".join(indexes)
        spl_query = spl_query.replace("index=*", index_clause)
    
    return {
        "spl_query": spl_query,
        "natural_language": query,
        "matched_pattern": matched_pattern,
        "explanation": f"Generated SPL query based on pattern: {matched_pattern}",
        "time_range": "-24h to now",
        "estimated_events": "unknown"
    }

server = Server("splunk-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Splunk tools."""
    return [
        types.Tool(
            name="generate_spl_query",
            description="Generate a Splunk SPL query from natural language description. Translates human-readable questions into optimized SPL queries.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language description of what to search for (e.g., 'Find all failed login attempts in the last 24 hours')"
                    },
                    "indexes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: Specific indexes to search (e.g., ['windows', 'linux'])"
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Optional: Time range for search (e.g., '-24h', '-7d', default: '-24h')"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="execute_spl_search",
            description="Execute a Splunk SPL query and return results. Can execute pre-generated or custom SPL queries.",
            inputSchema={
                "type": "object",
                "properties": {
                    "spl_query": {
                        "type": "string",
                        "description": "The SPL query to execute (e.g., 'index=main sourcetype=access_combined | stats count by status')"
                    },
                    "earliest_time": {
                        "type": "string",
                        "description": "Start time for search (e.g., '-24h', '-7d', default: '-24h')"
                    },
                    "latest_time": {
                        "type": "string",
                        "description": "End time for search (default: 'now')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 100)"
                    }
                },
                "required": ["spl_query"]
            }
        ),
        types.Tool(
            name="get_splunk_indexes",
            description="Get list of available Splunk indexes that can be queried.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="search_by_ip",
            description="Search Splunk for all events related to a specific IP address.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip_address": {
                        "type": "string",
                        "description": "IP address to search for"
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Number of hours to look back (default: 24)"
                    }
                },
                "required": ["ip_address"]
            }
        ),
        types.Tool(
            name="search_by_hostname",
            description="Search Splunk for all events related to a specific hostname.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hostname": {
                        "type": "string",
                        "description": "Hostname to search for"
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Number of hours to look back (default: 24)"
                    }
                },
                "required": ["hostname"]
            }
        ),
        types.Tool(
            name="search_by_username",
            description="Search Splunk for all events related to a specific username.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Username to search for"
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Number of hours to look back (default: 24)"
                    }
                },
                "required": ["username"]
            }
        ),
        types.Tool(
            name="natural_language_search",
            description="Combined tool that generates SPL from natural language and executes it in one step. Most convenient for ad-hoc investigations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language question (e.g., 'Show me all PowerShell executions with encoded commands')"
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time range (default: '-24h')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results (default: 100)"
                    }
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    if name == "generate_spl_query":
        query = arguments.get("query") if arguments else None
        indexes = arguments.get("indexes") if arguments else None
        time_range = arguments.get("time_range", "-24h") if arguments else "-24h"
        
        if not query:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "query parameter is required"}, indent=2)
            )]
        
        result = generate_spl_from_natural_language(query, indexes)
        result["time_range"] = time_range
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "execute_spl_search":
        spl_query = arguments.get("spl_query") if arguments else None
        earliest_time = arguments.get("earliest_time", "-24h") if arguments else "-24h"
        latest_time = arguments.get("latest_time", "now") if arguments else "now"
        max_results = arguments.get("max_results", 100) if arguments else 100
        
        if not spl_query:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "spl_query parameter is required"}, indent=2)
            )]
        
        # Get Splunk service
        splunk = get_splunk_service()
        
        if not splunk:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Splunk not configured",
                    "message": "Please configure Splunk connection in ~/.deeptempo/config.json or environment variables",
                    "required_config": {
                        "server_url": "https://splunk.example.com:8089",
                        "username": "admin",
                        "password": "password",
                        "verify_ssl": False
                    }
                }, indent=2)
            )]
        
        # Execute search
        try:
            results = splunk.search(spl_query, earliest_time, latest_time, max_results)
            
            if results is None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Search execution failed",
                        "query": spl_query
                    }, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "query": spl_query,
                    "time_range": f"{earliest_time} to {latest_time}",
                    "result_count": len(results),
                    "results": results
                }, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "query": spl_query
                }, indent=2)
            )]
    
    elif name == "get_splunk_indexes":
        splunk = get_splunk_service()
        
        if not splunk:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Splunk not configured",
                    "indexes": ["main", "windows", "linux", "network", "security"]  # Mock data
                }, indent=2)
            )]
        
        try:
            indexes = splunk.get_indexes()
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "indexes": indexes if indexes else []
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "search_by_ip":
        ip_address = arguments.get("ip_address") if arguments else None
        hours = arguments.get("hours", 24) if arguments else 24
        
        if not ip_address:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "ip_address parameter is required"}, indent=2)
            )]
        
        splunk = get_splunk_service()
        if not splunk:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "Splunk not configured"}, indent=2)
            )]
        
        try:
            results = splunk.search_by_ip(ip_address, hours)
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "ip_address": ip_address,
                    "time_range": f"last {hours} hours",
                    "result_count": len(results) if results else 0,
                    "results": results if results else []
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "search_by_hostname":
        hostname = arguments.get("hostname") if arguments else None
        hours = arguments.get("hours", 24) if arguments else 24
        
        if not hostname:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "hostname parameter is required"}, indent=2)
            )]
        
        splunk = get_splunk_service()
        if not splunk:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "Splunk not configured"}, indent=2)
            )]
        
        try:
            results = splunk.search_by_hostname(hostname, hours)
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "hostname": hostname,
                    "time_range": f"last {hours} hours",
                    "result_count": len(results) if results else 0,
                    "results": results if results else []
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "search_by_username":
        username = arguments.get("username") if arguments else None
        hours = arguments.get("hours", 24) if arguments else 24
        
        if not username:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "username parameter is required"}, indent=2)
            )]
        
        splunk = get_splunk_service()
        if not splunk:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "Splunk not configured"}, indent=2)
            )]
        
        try:
            results = splunk.search_by_username(username, hours)
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "username": username,
                    "time_range": f"last {hours} hours",
                    "result_count": len(results) if results else 0,
                    "results": results if results else []
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "natural_language_search":
        query = arguments.get("query") if arguments else None
        time_range = arguments.get("time_range", "-24h") if arguments else "-24h"
        max_results = arguments.get("max_results", 100) if arguments else 100
        
        if not query:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "query parameter is required"}, indent=2)
            )]
        
        # Generate SPL
        spl_result = generate_spl_from_natural_language(query)
        spl_query = spl_result["spl_query"]
        
        # Execute search
        splunk = get_splunk_service()
        if not splunk:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Splunk not configured",
                    "generated_spl": spl_result,
                    "message": "SPL was generated but cannot execute without Splunk configuration"
                }, indent=2)
            )]
        
        try:
            results = splunk.search(spl_query, time_range, "now", max_results)
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "natural_language": query,
                    "generated_spl": spl_query,
                    "pattern_matched": spl_result["matched_pattern"],
                    "time_range": time_range,
                    "result_count": len(results) if results else 0,
                    "results": results if results else []
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "generated_spl": spl_query
                }, indent=2)
            )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the Splunk MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="splunk-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

