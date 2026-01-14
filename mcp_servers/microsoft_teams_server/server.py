"""MCP Server for Microsoft Teams integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_microsoft_teams_config():
    """Get Microsoft Teams configuration from integrations config."""
    try:
        import sys
        from pathlib import Path
        # Add parent directory to path to import config_utils
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from config_utils import get_integration_config
        config = get_integration_config('microsoft-teams')
        return config
    except Exception as e:
        logger.error(f"Error loading Microsoft Teams config: {e}")
        return {}

server = Server("microsoft-teams-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Microsoft Teams tools."""
    return [
        types.Tool(
            name="teams_send_message",
            description="Send a message to Microsoft Teams channel via webhook.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Message title"
                    },
                    "text": {
                        "type": "string",
                        "description": "Message text content"
                    },
                    "color": {
                        "type": "string",
                        "description": "Theme color for the card (hex color code)",
                        "default": "0078D4"
                    },
                    "sections": {
                        "type": "array",
                        "description": "Additional sections with facts",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "facts": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "value": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "required": ["title", "text"]
            }
        ),
        types.Tool(
            name="teams_send_alert",
            description="Send a formatted security alert to Microsoft Teams.",
            inputSchema={
                "type": "object",
                "properties": {
                    "alert_type": {
                        "type": "string",
                        "description": "Type of alert",
                        "enum": ["critical", "high", "medium", "low", "info"]
                    },
                    "title": {
                        "type": "string",
                        "description": "Alert title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Alert description"
                    },
                    "details": {
                        "type": "object",
                        "description": "Additional alert details as key-value pairs"
                    }
                },
                "required": ["alert_type", "title", "description"]
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
    
    config = get_microsoft_teams_config()
    if not config:
        return [types.TextContent(
            type="text",
            text="Microsoft Teams integration not configured. Please configure in Settings → Integrations."
        )]
    
    if name == "teams_send_message":
        # Mock implementation - replace with actual Teams webhook call
        result = {
            "status": "success",
            "message": f"Message sent to Teams: {arguments.get('title')}",
            "note": "This is a mock response. Implement actual Microsoft Teams webhook integration."
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "teams_send_alert":
        # Mock implementation
        alert_colors = {
            "critical": "FF0000",
            "high": "FF6B00",
            "medium": "FFA500",
            "low": "FFFF00",
            "info": "0078D4"
        }
        color = alert_colors.get(arguments.get('alert_type', 'info'), "0078D4")
        
        result = {
            "status": "success",
            "message": f"Alert sent to Teams: {arguments.get('title')}",
            "alert_type": arguments.get('alert_type'),
            "color": color,
            "note": "This is a mock response. Implement actual Microsoft Teams webhook integration."
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
                server_name="microsoft-teams-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

