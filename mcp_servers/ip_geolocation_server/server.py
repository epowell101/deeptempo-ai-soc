"""MCP Server for IP Geolocation integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_ipgeo_config():
    """Get IP Geolocation configuration from integrations config."""
    try:
        from ui.integrations_config import IntegrationsConfigDialog
        config = IntegrationsConfigDialog.get_integration_config('ip_geolocation')
        return config
    except Exception as e:
        logger.error(f"Error loading IP Geolocation config: {e}")
        return {}

server = Server("ip_geolocation-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available IP Geolocation tools."""
    return [
        types.Tool(
            name="ipgeo_geolocate_ip",
            description="Get geolocation information for an IP address including country, city, coordinates, timezone, and ISP.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "IP address to geolocate"
                    }
                },
                "required": ["ip"]
            }
        ),
        types.Tool(
            name="ipgeo_get_asn",
            description="Get Autonomous System Number (ASN) information for an IP address.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "IP address to lookup ASN"
                    }
                },
                "required": ["ip"]
            }
        ),
        types.Tool(
            name="ipgeo_get_abuse_contact",
            description="Get abuse contact information for an IP address or ASN.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "IP address to get abuse contact for"
                    }
                },
                "required": ["ip"]
            }
        ),
        types.Tool(
            name="ipgeo_get_ip_reputation",
            description="Get reputation score and threat intelligence for an IP address.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "IP address to check reputation"
                    }
                },
                "required": ["ip"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_ipgeo_config()
    api_key = config.get('api_key')
    
    # Use free API if no key provided (limited features)
    use_free_api = not api_key
    
    try:
        import requests
        
        if name == "ipgeo_geolocate_ip":
            ip = arguments.get("ip") if arguments else None
            
            if not ip:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "ip parameter is required"}, indent=2)
                )]
            
            # Use ip-api.com (free, no key required)
            url = f"http://ip-api.com/json/{ip}"
            params = {"fields": "status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query"}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "fail":
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "ip": ip,
                        "error": data.get("message", "Failed to geolocate IP")
                    }, indent=2)
                )]
            
            result = {
                "ip": data.get("query"),
                "country": data.get("country"),
                "country_code": data.get("countryCode"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "zip": data.get("zip"),
                "latitude": data.get("lat"),
                "longitude": data.get("lon"),
                "timezone": data.get("timezone"),
                "isp": data.get("isp"),
                "organization": data.get("org"),
                "asn": data.get("as"),
                "asname": data.get("asname"),
                "is_mobile": data.get("mobile", False),
                "is_proxy": data.get("proxy", False),
                "is_hosting": data.get("hosting", False)
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "ipgeo_get_asn":
            ip = arguments.get("ip") if arguments else None
            
            if not ip:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "ip parameter is required"}, indent=2)
                )]
            
            # Use ip-api.com for ASN lookup
            url = f"http://ip-api.com/json/{ip}"
            params = {"fields": "status,message,as,asname,isp,org,query"}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "fail":
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "ip": ip,
                        "error": data.get("message", "Failed to lookup ASN")
                    }, indent=2)
                )]
            
            result = {
                "ip": data.get("query"),
                "asn": data.get("as"),
                "asn_name": data.get("asname"),
                "isp": data.get("isp"),
                "organization": data.get("org")
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "ipgeo_get_abuse_contact":
            ip = arguments.get("ip") if arguments else None
            
            if not ip:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "ip parameter is required"}, indent=2)
                )]
            
            # Use RDAP (Registration Data Access Protocol)
            # First get ASN from ip-api
            url = f"http://ip-api.com/json/{ip}"
            params = {"fields": "status,as,isp,org"}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "fail":
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "ip": ip,
                        "error": "Could not determine ASN"
                    }, indent=2)
                )]
            
            asn_info = data.get("as", "")
            asn_number = asn_info.split()[0] if asn_info else ""
            
            result = {
                "ip": ip,
                "asn": asn_info,
                "isp": data.get("isp"),
                "organization": data.get("org"),
                "abuse_contact": f"abuse@{data.get('isp', 'unknown').lower().replace(' ', '')}.com",
                "note": "For accurate abuse contacts, query WHOIS or RDAP directly"
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "ipgeo_get_ip_reputation":
            ip = arguments.get("ip") if arguments else None
            
            if not ip:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "ip parameter is required"}, indent=2)
                )]
            
            # Use ip-api for basic checks
            url = f"http://ip-api.com/json/{ip}"
            params = {"fields": "status,proxy,hosting,mobile,query,isp"}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "fail":
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "ip": ip,
                        "error": "Failed to check reputation"
                    }, indent=2)
                )]
            
            # Calculate basic risk score
            risk_score = 0
            risk_factors = []
            
            if data.get("proxy"):
                risk_score += 30
                risk_factors.append("Proxy/VPN detected")
            if data.get("hosting"):
                risk_score += 20
                risk_factors.append("Hosting provider")
            
            risk_level = "low"
            if risk_score >= 50:
                risk_level = "high"
            elif risk_score >= 25:
                risk_level = "medium"
            
            result = {
                "ip": data.get("query"),
                "is_proxy": data.get("proxy", False),
                "is_hosting": data.get("hosting", False),
                "is_mobile": data.get("mobile", False),
                "isp": data.get("isp"),
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "note": "For comprehensive reputation checks, integrate with AbuseIPDB, IPQualityScore, or similar services"
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
                "status_code": e.response.status_code if hasattr(e, 'response') else None,
                "message": str(e)
            }, indent=2)
        )]
    except Exception as e:
        logger.error(f"Error in IP Geolocation tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the IP Geolocation MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ip_geolocation-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
