"""MCP Server for AlienVault OTX integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_alienvault_otx_config():
    """Get Alienvault Otx configuration from integrations config."""
    try:
        import sys
        from pathlib import Path
        # Add parent directory to path to import config_utils
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from config_utils import get_integration_config
        config = get_integration_config('alienvault_otx')
        return config
    except Exception as e:
        logger.error(f"Error loading Alienvault Otx config: {e}")
        return {}

server = Server("alienvault_otx-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available AlienVault OTX tools."""
    return [
        types.Tool(
            name="otx_get_pulses",
            description="Get recent threat intelligence pulses from AlienVault OTX. Returns latest threat indicators and campaigns.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of pulses to return (default: 10)",
                        "default": 10
                    },
                    "modified_since": {
                        "type": "string",
                        "description": "ISO 8601 date to filter pulses modified since (optional)"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="otx_search_indicators",
            description="Search for indicators of compromise (IOCs) in AlienVault OTX by type and value.",
            inputSchema={
                "type": "object",
                "properties": {
                    "indicator_type": {
                        "type": "string",
                        "enum": ["IPv4", "IPv6", "domain", "hostname", "URL", "FileHash-MD5", "FileHash-SHA1", "FileHash-SHA256"],
                        "description": "Type of indicator to search for"
                    },
                    "indicator": {
                        "type": "string",
                        "description": "The indicator value to search for"
                    }
                },
                "required": ["indicator_type", "indicator"]
            }
        ),
        types.Tool(
            name="otx_get_ioc_reputation",
            description="Get reputation and threat intelligence for an IP, domain, or hash from AlienVault OTX.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ioc": {
                        "type": "string",
                        "description": "IP address, domain, or file hash to check"
                    },
                    "ioc_type": {
                        "type": "string",
                        "enum": ["IPv4", "domain", "hash"],
                        "description": "Type of IOC"
                    }
                },
                "required": ["ioc", "ioc_type"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_alienvault_otx_config()
    api_key = config.get('api_key')
    
    if not api_key:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "AlienVault OTX not configured",
                "message": "Please configure AlienVault OTX API key in Settings > Integrations"
            }, indent=2)
        )]
    
    try:
        import requests
        
        if name == "otx_get_pulses":
            limit = arguments.get("limit", 10) if arguments else 10
            modified_since = arguments.get("modified_since") if arguments else None
            
            headers = {"X-OTX-API-KEY": api_key}
            url = "https://otx.alienvault.com/api/v1/pulses/subscribed"
            params = {"limit": limit}
            if modified_since:
                params["modified_since"] = modified_since
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract key information from pulses
            pulses = []
            for pulse in data.get("results", [])[:limit]:
                pulses.append({
                    "id": pulse.get("id"),
                    "name": pulse.get("name"),
                    "description": pulse.get("description", "")[:200],  # Truncate
                    "created": pulse.get("created"),
                    "modified": pulse.get("modified"),
                    "author_name": pulse.get("author_name"),
                    "tags": pulse.get("tags", []),
                    "targeted_countries": pulse.get("targeted_countries", []),
                    "indicator_count": pulse.get("indicator_count", 0),
                    "tlp": pulse.get("TLP", "white")
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "pulses": pulses,
                    "count": len(pulses)
                }, indent=2)
            )]
        
        elif name == "otx_search_indicators":
            indicator_type = arguments.get("indicator_type") if arguments else None
            indicator = arguments.get("indicator") if arguments else None
            
            if not indicator_type or not indicator:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "indicator_type and indicator are required"
                    }, indent=2)
                )]
            
            headers = {"X-OTX-API-KEY": api_key}
            url = f"https://otx.alienvault.com/api/v1/indicators/{indicator_type}/{indicator}/general"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "indicator": indicator,
                        "indicator_type": indicator_type,
                        "found": False,
                        "message": "Indicator not found in AlienVault OTX"
                    }, indent=2)
                )]
            
            response.raise_for_status()
            data = response.json()
            
            result = {
                "indicator": indicator,
                "indicator_type": indicator_type,
                "found": True,
                "pulse_count": data.get("pulse_info", {}).get("count", 0),
                "pulses": [],
                "validation": data.get("validation", []),
                "whitelisted": data.get("whitelisted", False)
            }
            
            # Get pulse details
            for pulse in data.get("pulse_info", {}).get("pulses", [])[:5]:  # First 5
                result["pulses"].append({
                    "name": pulse.get("name"),
                    "created": pulse.get("created"),
                    "tags": pulse.get("tags", []),
                    "tlp": pulse.get("TLP", "white")
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "otx_get_ioc_reputation":
            ioc = arguments.get("ioc") if arguments else None
            ioc_type = arguments.get("ioc_type") if arguments else None
            
            if not ioc or not ioc_type:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "ioc and ioc_type are required"
                    }, indent=2)
                )]
            
            headers = {"X-OTX-API-KEY": api_key}
            
            # Map ioc_type to OTX section
            if ioc_type == "IPv4":
                url = f"https://otx.alienvault.com/api/v1/indicators/IPv4/{ioc}/reputation"
            elif ioc_type == "domain":
                url = f"https://otx.alienvault.com/api/v1/indicators/domain/{ioc}/general"
            elif ioc_type == "hash":
                url = f"https://otx.alienvault.com/api/v1/indicators/file/{ioc}/general"
            else:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Unsupported ioc_type: {ioc_type}"
                    }, indent=2)
                )]
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "ioc": ioc,
                        "ioc_type": ioc_type,
                        "found": False,
                        "reputation": "unknown"
                    }, indent=2)
                )]
            
            response.raise_for_status()
            data = response.json()
            
            result = {
                "ioc": ioc,
                "ioc_type": ioc_type,
                "found": True,
                "pulse_count": data.get("pulse_info", {}).get("count", 0),
                "validation": data.get("validation", []),
                "reputation_score": data.get("reputation", 0),
                "threat_score": data.get("threat_score", 0),
                "tags": []
            }
            
            # Collect tags from pulses
            for pulse in data.get("pulse_info", {}).get("pulses", [])[:10]:
                result["tags"].extend(pulse.get("tags", []))
            result["tags"] = list(set(result["tags"]))[:10]  # Unique, first 10
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
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
        logger.error(f"Error in AlienVault OTX tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the AlienVault OTX MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="alienvault_otx-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
