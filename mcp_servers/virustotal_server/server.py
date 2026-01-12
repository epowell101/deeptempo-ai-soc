"""MCP Server for VirusTotal API integration."""

import asyncio
import logging
import json
import time
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

# Rate limiting
class RateLimiter:
    def __init__(self, requests_per_minute: int = 4):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0
    
    async def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            await asyncio.sleep(self.min_interval - time_since_last)
        self.last_request_time = time.time()

def get_virustotal_config():
    """Get VirusTotal configuration from integrations config."""
    try:
        from ui.integrations_config import IntegrationsConfigDialog
        config = IntegrationsConfigDialog.get_integration_config('virustotal')
        return config
    except Exception as e:
        logger.error(f"Error loading VirusTotal config: {e}")
        return {}

server = Server("virustotal-server")
rate_limiter = RateLimiter()

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available VirusTotal tools."""
    return [
        types.Tool(
            name="vt_check_hash",
            description="Check a file hash (MD5, SHA1, SHA256) reputation on VirusTotal. Returns detection results from multiple antivirus engines.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hash": {
                        "type": "string",
                        "description": "File hash (MD5, SHA1, or SHA256)"
                    }
                },
                "required": ["hash"]
            }
        ),
        types.Tool(
            name="vt_check_ip",
            description="Check an IP address reputation on VirusTotal. Returns detection results and passive DNS data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "IP address to check"
                    }
                },
                "required": ["ip"]
            }
        ),
        types.Tool(
            name="vt_check_domain",
            description="Check a domain reputation on VirusTotal. Returns detection results and WHOIS data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain name to check"
                    }
                },
                "required": ["domain"]
            }
        ),
        types.Tool(
            name="vt_check_url",
            description="Check a URL reputation on VirusTotal. Returns detection results from URL scanners.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to check"
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="vt_get_file_report",
            description="Get detailed file analysis report from VirusTotal including behavior, network activity, and process tree.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hash": {
                        "type": "string",
                        "description": "File hash (MD5, SHA1, or SHA256)"
                    }
                },
                "required": ["hash"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_virustotal_config()
    api_key = config.get('api_key')
    
    if not api_key:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "VirusTotal not configured",
                "message": "Please configure VirusTotal API key in Settings > Integrations"
            }, indent=2)
        )]
    
    # Rate limiting
    await rate_limiter.wait_if_needed()
    
    try:
        import requests
        
        if name == "vt_check_hash":
            hash_value = arguments.get("hash") if arguments else None
            if not hash_value:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "hash parameter is required"}, indent=2)
                )]
            
            # Call VirusTotal API
            headers = {"x-apikey": api_key}
            url = f"https://www.virustotal.com/api/v3/files/{hash_value}"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "hash": hash_value,
                        "found": False,
                        "message": "File not found in VirusTotal database"
                    }, indent=2)
                )]
            
            response.raise_for_status()
            data = response.json()
            
            # Extract key information
            attributes = data.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})
            
            result = {
                "hash": hash_value,
                "found": True,
                "malicious": stats.get('malicious', 0),
                "suspicious": stats.get('suspicious', 0),
                "undetected": stats.get('undetected', 0),
                "total_engines": sum(stats.values()),
                "detection_ratio": f"{stats.get('malicious', 0)}/{sum(stats.values())}",
                "names": attributes.get('names', [])[:5],  # First 5 names
                "file_type": attributes.get('type_description'),
                "size": attributes.get('size'),
                "reputation": attributes.get('reputation', 0),
                "first_seen": attributes.get('first_submission_date'),
                "last_seen": attributes.get('last_submission_date')
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "vt_check_ip":
            ip = arguments.get("ip") if arguments else None
            if not ip:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "ip parameter is required"}, indent=2)
                )]
            
            headers = {"x-apikey": api_key}
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            attributes = data.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})
            
            result = {
                "ip": ip,
                "malicious": stats.get('malicious', 0),
                "suspicious": stats.get('suspicious', 0),
                "undetected": stats.get('undetected', 0),
                "total_engines": sum(stats.values()),
                "detection_ratio": f"{stats.get('malicious', 0)}/{sum(stats.values())}",
                "asn": attributes.get('asn'),
                "as_owner": attributes.get('as_owner'),
                "country": attributes.get('country'),
                "reputation": attributes.get('reputation', 0),
                "network": attributes.get('network')
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "vt_check_domain":
            domain = arguments.get("domain") if arguments else None
            if not domain:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "domain parameter is required"}, indent=2)
                )]
            
            headers = {"x-apikey": api_key}
            url = f"https://www.virustotal.com/api/v3/domains/{domain}"
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            attributes = data.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})
            
            result = {
                "domain": domain,
                "malicious": stats.get('malicious', 0),
                "suspicious": stats.get('suspicious', 0),
                "undetected": stats.get('undetected', 0),
                "total_engines": sum(stats.values()),
                "detection_ratio": f"{stats.get('malicious', 0)}/{sum(stats.values())}",
                "categories": attributes.get('categories', {}),
                "reputation": attributes.get('reputation', 0),
                "creation_date": attributes.get('creation_date'),
                "last_update_date": attributes.get('last_update_date'),
                "registrar": attributes.get('registrar')
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "vt_check_url":
            url_to_check = arguments.get("url") if arguments else None
            if not url_to_check:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "url parameter is required"}, indent=2)
                )]
            
            # URL needs to be base64 encoded for API
            import base64
            url_id = base64.urlsafe_b64encode(url_to_check.encode()).decode().strip("=")
            
            headers = {"x-apikey": api_key}
            url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "url": url_to_check,
                        "found": False,
                        "message": "URL not found in VirusTotal database"
                    }, indent=2)
                )]
            
            response.raise_for_status()
            data = response.json()
            
            attributes = data.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})
            
            result = {
                "url": url_to_check,
                "found": True,
                "malicious": stats.get('malicious', 0),
                "suspicious": stats.get('suspicious', 0),
                "undetected": stats.get('undetected', 0),
                "total_engines": sum(stats.values()),
                "detection_ratio": f"{stats.get('malicious', 0)}/{sum(stats.values())}",
                "categories": attributes.get('categories', {}),
                "reputation": attributes.get('reputation', 0),
                "title": attributes.get('title'),
                "last_final_url": attributes.get('last_final_url')
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "vt_get_file_report":
            hash_value = arguments.get("hash") if arguments else None
            if not hash_value:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "hash parameter is required"}, indent=2)
                )]
            
            headers = {"x-apikey": api_key}
            url = f"https://www.virustotal.com/api/v3/files/{hash_value}"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "hash": hash_value,
                        "found": False,
                        "message": "File not found in VirusTotal database"
                    }, indent=2)
                )]
            
            response.raise_for_status()
            data = response.json()
            
            attributes = data.get('data', {}).get('attributes', {})
            
            # Get detailed behavior information
            result = {
                "hash": hash_value,
                "found": True,
                "basic_info": {
                    "names": attributes.get('names', [])[:5],
                    "type": attributes.get('type_description'),
                    "size": attributes.get('size'),
                    "magic": attributes.get('magic')
                },
                "detection": {
                    "stats": attributes.get('last_analysis_stats', {}),
                    "results": {k: v for k, v in list(attributes.get('last_analysis_results', {}).items())[:10]}  # First 10 detections
                },
                "signatures": attributes.get('signature_info', {}),
                "pe_info": attributes.get('pe_info', {}).get('imports', [])[:5] if attributes.get('pe_info') else [],
                "tags": attributes.get('tags', []),
                "reputation": attributes.get('reputation', 0),
                "times": {
                    "first_submission": attributes.get('first_submission_date'),
                    "last_submission": attributes.get('last_submission_date'),
                    "last_analysis": attributes.get('last_analysis_date')
                }
            }
            
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
                "status_code": e.response.status_code,
                "message": str(e)
            }, indent=2)
        )]
    except Exception as e:
        logger.error(f"Error in VirusTotal tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the VirusTotal MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="virustotal-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

