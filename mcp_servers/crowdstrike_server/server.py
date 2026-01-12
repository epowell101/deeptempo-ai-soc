"""MCP Server for CrowdStrike integrations."""

import asyncio
import logging
from typing import Any
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

# Mock data - replace with actual CrowdStrike API calls
MOCK_CROWDSTRIKE_ALERTS = {
    "192.168.1.100": [
        {
            "alert_id": "cs-alert-001",
            "timestamp": "2026-01-12T10:28:00Z",
            "ip_address": "192.168.1.100",
            "hostname": "WORKSTATION-01",
            "severity": "critical",
            "detection_type": "Malware",
            "description": "Ransomware behavior detected - file encryption activity",
            "confidence": 0.95,
            "process": "suspicious.exe",
            "user": "john.doe",
            "status": "active",
            "isolated": False
        }
    ],
    "10.0.0.50": [
        {
            "alert_id": "cs-alert-002",
            "timestamp": "2026-01-12T10:32:00Z",
            "ip_address": "10.0.0.50",
            "hostname": "SERVER-DMZ-01",
            "severity": "high",
            "detection_type": "Intrusion",
            "description": "Suspicious PowerShell execution detected",
            "confidence": 0.88,
            "process": "powershell.exe",
            "user": "SYSTEM",
            "status": "active",
            "isolated": False
        }
    ]
}

# Track isolated hosts
ISOLATED_HOSTS = set()

server = Server("crowdstrike-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available CrowdStrike tools."""
    return [
        types.Tool(
            name="get_crowdstrike_alert_by_ip",
            description="Get CrowdStrike Falcon alerts for a specific IP address or hostname. Returns endpoint detections and host information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip_address": {
                        "type": "string",
                        "description": "IP address to query"
                    },
                    "hostname": {
                        "type": "string",
                        "description": "Hostname to query (optional)"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Filter by severity (optional)"
                    }
                },
                "required": ["ip_address"]
            }
        ),
        types.Tool(
            name="crowdstrike_foundry_isolate",
            description="(MOCK) Isolate a host using CrowdStrike Foundry. This will network-isolate the endpoint to prevent lateral movement. USE WITH CAUTION - only when confidence is high (>0.85).",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip_address": {
                        "type": "string",
                        "description": "IP address of host to isolate"
                    },
                    "hostname": {
                        "type": "string",
                        "description": "Hostname to isolate (optional, used for confirmation)"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for isolation (required for audit)"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score (0.0-1.0) for this action",
                        "minimum": 0.0,
                        "maximum": 1.0
                    }
                },
                "required": ["ip_address", "reason", "confidence"]
            }
        ),
        types.Tool(
            name="crowdstrike_foundry_unisolate",
            description="(MOCK) Remove network isolation from a host. Only use after threat has been confirmed remediated.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip_address": {
                        "type": "string",
                        "description": "IP address of host to unisolate"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for removing isolation"
                    }
                },
                "required": ["ip_address", "reason"]
            }
        ),
        types.Tool(
            name="get_host_status",
            description="Get the current status of a host including isolation state.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip_address": {
                        "type": "string",
                        "description": "IP address to check"
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
    import json
    
    if name == "get_crowdstrike_alert_by_ip":
        ip_address = arguments.get("ip_address") if arguments else None
        hostname = arguments.get("hostname") if arguments else None
        severity = arguments.get("severity") if arguments else None
        
        if not ip_address:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "ip_address is required"}, indent=2)
            )]
        
        # Get alerts for IP
        alerts = MOCK_CROWDSTRIKE_ALERTS.get(ip_address, [])
        
        # Filter by severity if specified
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        
        # Filter by hostname if specified
        if hostname:
            alerts = [a for a in alerts if a["hostname"] == hostname]
        
        result = {
            "ip_address": ip_address,
            "alerts": alerts,
            "total": len(alerts),
            "isolated": ip_address in ISOLATED_HOSTS
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "crowdstrike_foundry_isolate":
        ip_address = arguments.get("ip_address") if arguments else None
        hostname = arguments.get("hostname") if arguments else None
        reason = arguments.get("reason") if arguments else None
        confidence = arguments.get("confidence") if arguments else 0.0
        
        if not ip_address or not reason:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "ip_address and reason are required"}, indent=2)
            )]
        
        # Check confidence threshold
        if confidence < 0.85:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Confidence too low for automatic isolation",
                    "confidence": confidence,
                    "threshold": 0.85,
                    "recommendation": "Manual review required"
                }, indent=2)
            )]
        
        # Check if already isolated
        if ip_address in ISOLATED_HOSTS:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "already_isolated",
                    "ip_address": ip_address,
                    "message": "Host is already isolated"
                }, indent=2)
            )]
        
        # Perform isolation (mock)
        ISOLATED_HOSTS.add(ip_address)
        
        result = {
            "status": "success",
            "action": "host_isolated",
            "ip_address": ip_address,
            "hostname": hostname,
            "reason": reason,
            "confidence": confidence,
            "timestamp": "2026-01-12T10:45:00Z",
            "isolation_type": "network",
            "message": "Host has been network isolated successfully",
            "next_steps": [
                "Verify threat containment",
                "Conduct forensic analysis",
                "Remediate threat",
                "Consider unisolation after remediation"
            ]
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "crowdstrike_foundry_unisolate":
        ip_address = arguments.get("ip_address") if arguments else None
        reason = arguments.get("reason") if arguments else None
        
        if not ip_address or not reason:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "ip_address and reason are required"}, indent=2)
            )]
        
        # Check if actually isolated
        if ip_address not in ISOLATED_HOSTS:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "not_isolated",
                    "ip_address": ip_address,
                    "message": "Host is not currently isolated"
                }, indent=2)
            )]
        
        # Remove isolation (mock)
        ISOLATED_HOSTS.remove(ip_address)
        
        result = {
            "status": "success",
            "action": "host_unisolated",
            "ip_address": ip_address,
            "reason": reason,
            "timestamp": "2026-01-12T11:00:00Z",
            "message": "Host isolation has been removed successfully",
            "next_steps": [
                "Monitor host for 24 hours",
                "Verify normal operations",
                "Update incident documentation"
            ]
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "get_host_status":
        ip_address = arguments.get("ip_address") if arguments else None
        
        if not ip_address:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "ip_address is required"}, indent=2)
            )]
        
        # Get host status
        alerts = MOCK_CROWDSTRIKE_ALERTS.get(ip_address, [])
        active_alerts = [a for a in alerts if a["status"] == "active"]
        
        status = {
            "ip_address": ip_address,
            "isolated": ip_address in ISOLATED_HOSTS,
            "active_alerts": len(active_alerts),
            "highest_severity": max([a["severity"] for a in alerts], default="none") if alerts else "none",
            "last_seen": "2026-01-12T10:45:00Z",
            "status": "isolated" if ip_address in ISOLATED_HOSTS else "active"
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(status, indent=2)
        )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the CrowdStrike MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="crowdstrike-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

