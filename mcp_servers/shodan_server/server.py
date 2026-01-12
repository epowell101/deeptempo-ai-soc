"""MCP Server for Shodan integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_shodan_config():
    """Get Shodan configuration from integrations config."""
    try:
        from ui.integrations_config import IntegrationsConfigDialog
        config = IntegrationsConfigDialog.get_integration_config('shodan')
        return config
    except Exception as e:
        logger.error(f"Error loading Shodan config: {e}")
        return {}

server = Server("shodan-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Shodan tools."""
    return [
        types.Tool(
            name="shodan_search_ip",
            description="Search for IP address information in Shodan. Returns open ports, services, vulnerabilities, and banners.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "IP address to search"
                    }
                },
                "required": ["ip"]
            }
        ),
        types.Tool(
            name="shodan_search_exploits",
            description="Search for exploits related to a CVE or product in Shodan's exploit database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (CVE ID, product name, or keyword)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="shodan_get_host_info",
            description="Get detailed host information including all historical data, ports, and services for an IP.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "IP address to get information for"
                    },
                    "history": {
                        "type": "boolean",
                        "description": "Include historical data (default: false)",
                        "default": False
                    }
                },
                "required": ["ip"]
            }
        ),
        types.Tool(
            name="shodan_search_vulnerabilities",
            description="Search for hosts vulnerable to a specific CVE.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cve": {
                        "type": "string",
                        "description": "CVE ID (e.g., CVE-2021-44228)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["cve"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_shodan_config()
    api_key = config.get('api_key')
    
    if not api_key:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "Shodan not configured",
                "message": "Please configure Shodan API key in Settings > Integrations"
            }, indent=2)
        )]
    
    try:
        import requests
        
        if name == "shodan_search_ip":
            ip = arguments.get("ip") if arguments else None
            
            if not ip:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "ip parameter is required"}, indent=2)
                )]
            
            url = f"https://api.shodan.io/shodan/host/{ip}"
            params = {"key": api_key}
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 404:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "ip": ip,
                        "found": False,
                        "message": "No information found for this IP"
                    }, indent=2)
                )]
            
            response.raise_for_status()
            data = response.json()
            
            result = {
                "ip": ip,
                "found": True,
                "hostnames": data.get("hostnames", []),
                "organization": data.get("org", "Unknown"),
                "country": data.get("country_name", "Unknown"),
                "city": data.get("city", "Unknown"),
                "isp": data.get("isp", "Unknown"),
                "asn": data.get("asn", "Unknown"),
                "last_update": data.get("last_update"),
                "open_ports": data.get("ports", []),
                "vulnerabilities": data.get("vulns", []),
                "services": []
            }
            
            # Extract service information
            for service in data.get("data", [])[:5]:  # First 5 services
                result["services"].append({
                    "port": service.get("port"),
                    "transport": service.get("transport"),
                    "product": service.get("product"),
                    "version": service.get("version"),
                    "banner": service.get("data", "")[:200]  # Truncate banner
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "shodan_search_exploits":
            query = arguments.get("query") if arguments else None
            limit = arguments.get("limit", 10) if arguments else 10
            
            if not query:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "query parameter is required"}, indent=2)
                )]
            
            url = "https://exploits.shodan.io/api/search"
            params = {
                "key": api_key,
                "query": query
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            exploits = []
            for exploit in data.get("matches", [])[:limit]:
                exploits.append({
                    "id": exploit.get("_id"),
                    "description": exploit.get("description", "")[:200],
                    "author": exploit.get("author"),
                    "platform": exploit.get("platform"),
                    "type": exploit.get("type"),
                    "port": exploit.get("port"),
                    "published": exploit.get("date"),
                    "source": exploit.get("source"),
                    "cve": exploit.get("cve", [])
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "query": query,
                    "total": data.get("total", 0),
                    "exploits": exploits
                }, indent=2)
            )]
        
        elif name == "shodan_get_host_info":
            ip = arguments.get("ip") if arguments else None
            history = arguments.get("history", False) if arguments else False
            
            if not ip:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "ip parameter is required"}, indent=2)
                )]
            
            url = f"https://api.shodan.io/shodan/host/{ip}"
            params = {
                "key": api_key,
                "history": str(history).lower()
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 404:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "ip": ip,
                        "found": False
                    }, indent=2)
                )]
            
            response.raise_for_status()
            data = response.json()
            
            result = {
                "ip": ip,
                "found": True,
                "hostnames": data.get("hostnames", []),
                "organization": data.get("org"),
                "country": data.get("country_name"),
                "city": data.get("city"),
                "isp": data.get("isp"),
                "asn": data.get("asn"),
                "os": data.get("os"),
                "ports": data.get("ports", []),
                "vulnerabilities": data.get("vulns", []),
                "tags": data.get("tags", []),
                "services": []
            }
            
            # Detailed service information
            for service in data.get("data", [])[:10]:
                result["services"].append({
                    "timestamp": service.get("timestamp"),
                    "port": service.get("port"),
                    "transport": service.get("transport"),
                    "protocol": service.get("_shodan", {}).get("module"),
                    "product": service.get("product"),
                    "version": service.get("version"),
                    "cpe": service.get("cpe", []),
                    "banner": service.get("data", "")[:300]
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "shodan_search_vulnerabilities":
            cve = arguments.get("cve") if arguments else None
            limit = arguments.get("limit", 10) if arguments else 10
            
            if not cve:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "cve parameter is required"}, indent=2)
                )]
            
            url = "https://api.shodan.io/shodan/host/search"
            params = {
                "key": api_key,
                "query": f"vuln:{cve}"
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            hosts = []
            for match in data.get("matches", [])[:limit]:
                hosts.append({
                    "ip": match.get("ip_str"),
                    "port": match.get("port"),
                    "organization": match.get("org"),
                    "hostnames": match.get("hostnames", []),
                    "country": match.get("location", {}).get("country_name"),
                    "city": match.get("location", {}).get("city"),
                    "product": match.get("product"),
                    "version": match.get("version"),
                    "timestamp": match.get("timestamp")
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "cve": cve,
                    "total": data.get("total", 0),
                    "vulnerable_hosts": hosts
                }, indent=2)
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except requests.exceptions.HTTPError as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "API error",
                "status_code": e.response.status_code if hasattr(e, 'response') else None,
                "message": str(e)
            }, indent=2)
        )]
    except Exception as e:
        logger.error(f"Error in Shodan tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the Shodan MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="shodan-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
