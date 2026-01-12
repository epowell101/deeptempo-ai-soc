"""MCP Server for Tempo Flow Alerts."""

import asyncio
import logging
from typing import Any
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

# Mock data - replace with actual Tempo Flow API calls
MOCK_FLOW_ALERTS = [
    {
        "alert_id": "flow-001",
        "timestamp": "2026-01-12T10:30:00Z",
        "source_ip": "192.168.1.100",
        "dest_ip": "10.0.0.50",
        "protocol": "TCP",
        "port": 445,
        "severity": "high",
        "description": "Suspicious SMB lateral movement detected",
        "confidence": 0.85,
        "indicators": ["lateral_movement", "smb_brute_force"]
    },
    {
        "alert_id": "flow-002",
        "timestamp": "2026-01-12T10:35:00Z",
        "source_ip": "192.168.1.100",
        "dest_ip": "10.0.0.75",
        "protocol": "TCP",
        "port": 3389,
        "severity": "critical",
        "description": "RDP connection from compromised host",
        "confidence": 0.92,
        "indicators": ["lateral_movement", "rdp_connection"]
    }
]

server = Server("tempo-flow-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Tempo Flow tools."""
    return [
        types.Tool(
            name="get_tempo_flow_alert",
            description="Get Tempo Flow network alerts by IP address or alert ID. Returns network flow analytics and behavioral alerts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "alert_id": {
                        "type": "string",
                        "description": "Alert ID to retrieve (optional)"
                    },
                    "source_ip": {
                        "type": "string",
                        "description": "Source IP address to filter alerts (optional)"
                    },
                    "dest_ip": {
                        "type": "string",
                        "description": "Destination IP address to filter alerts (optional)"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Filter by severity level (optional)"
                    }
                }
            }
        ),
        types.Tool(
            name="get_flow_statistics",
            description="Get network flow statistics and patterns for an IP address over time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip_address": {
                        "type": "string",
                        "description": "IP address to analyze"
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time range (e.g., '1h', '24h', '7d')",
                        "default": "24h"
                    }
                },
                "required": ["ip_address"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    if name == "get_tempo_flow_alert":
        alert_id = arguments.get("alert_id") if arguments else None
        source_ip = arguments.get("source_ip") if arguments else None
        dest_ip = arguments.get("dest_ip") if arguments else None
        severity = arguments.get("severity") if arguments else None
        
        # Filter alerts
        results = MOCK_FLOW_ALERTS.copy()
        
        if alert_id:
            results = [a for a in results if a["alert_id"] == alert_id]
        if source_ip:
            results = [a for a in results if a["source_ip"] == source_ip]
        if dest_ip:
            results = [a for a in results if a["dest_ip"] == dest_ip]
        if severity:
            results = [a for a in results if a["severity"] == severity]
        
        if results:
            import json
            return [types.TextContent(
                type="text",
                text=json.dumps({"alerts": results, "total": len(results)}, indent=2)
            )]
        else:
            return [types.TextContent(
                type="text",
                text=json.dumps({"alerts": [], "total": 0, "message": "No alerts found matching criteria"}, indent=2)
            )]
    
    elif name == "get_flow_statistics":
        ip_address = arguments.get("ip_address") if arguments else None
        time_range = arguments.get("time_range", "24h") if arguments else "24h"
        
        if not ip_address:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "ip_address is required"}, indent=2)
            )]
        
        # Mock statistics
        stats = {
            "ip_address": ip_address,
            "time_range": time_range,
            "total_flows": 1523,
            "unique_destinations": 45,
            "total_bytes_sent": 15234567,
            "total_bytes_received": 8765432,
            "top_protocols": [
                {"protocol": "TCP", "count": 1200},
                {"protocol": "UDP", "count": 300},
                {"protocol": "ICMP", "count": 23}
            ],
            "suspicious_patterns": [
                "High port scan activity detected",
                "Unusual data transfer volume to external IPs"
            ],
            "risk_score": 75
        }
        
        import json
        return [types.TextContent(
            type="text",
            text=json.dumps(stats, indent=2)
        )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the Tempo Flow MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="tempo-flow-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

