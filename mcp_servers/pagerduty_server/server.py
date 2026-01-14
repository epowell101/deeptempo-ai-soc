"""MCP Server for PagerDuty integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_pagerduty_config():
    """Get PagerDuty configuration from integrations config."""
    try:
        import sys
        from pathlib import Path
        # Add parent directory to path to import config_utils
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from config_utils import get_integration_config
        config = get_integration_config('pagerduty')
        return config
    except Exception as e:
        logger.error(f"Error loading PagerDuty config: {e}")
        return {}

server = Server("pagerduty-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available PagerDuty tools."""
    return [
        types.Tool(
            name="pagerduty_create_incident",
            description="Create a new incident in PagerDuty for critical security events.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Incident title/summary"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed incident description"
                    },
                    "urgency": {
                        "type": "string",
                        "description": "Incident urgency (high or low)",
                        "enum": ["high", "low"]
                    },
                    "severity": {
                        "type": "string",
                        "description": "Incident severity",
                        "enum": ["critical", "error", "warning", "info"]
                    }
                },
                "required": ["title", "description"]
            }
        ),
        types.Tool(
            name="pagerduty_send_alert",
            description="Send an alert to PagerDuty using Events API v2.",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of the alert"
                    },
                    "severity": {
                        "type": "string",
                        "description": "Alert severity",
                        "enum": ["critical", "error", "warning", "info"]
                    },
                    "source": {
                        "type": "string",
                        "description": "Source of the alert (e.g., 'DeepTempo AI SOC')"
                    },
                    "custom_details": {
                        "type": "object",
                        "description": "Additional details as key-value pairs"
                    }
                },
                "required": ["summary", "severity"]
            }
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    if not arguments:
        arguments = {}
    
    config = get_pagerduty_config()
    if not config:
        return [types.TextContent(
            type="text",
            text="PagerDuty integration not configured. Please configure in Settings → Integrations."
        )]
    
    if name == "pagerduty_create_incident":
        # Mock implementation - replace with actual PagerDuty API call
        result = {
            "status": "success",
            "message": f"Incident created: {arguments.get('title')}",
            "incident_id": "mock-incident-001",
            "urgency": arguments.get('urgency', config.get('default_urgency', 'high')),
            "note": "This is a mock response. Implement actual PagerDuty API integration."
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "pagerduty_send_alert":
        # Mock implementation - replace with actual Events API v2 call
        result = {
            "status": "success",
            "message": f"Alert sent: {arguments.get('summary')}",
            "dedup_key": "mock-dedup-key-001",
            "note": "This is a mock response. Implement actual PagerDuty Events API v2 integration."
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="pagerduty-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

