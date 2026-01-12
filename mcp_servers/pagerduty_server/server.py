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
        from ui.integrations_config import IntegrationsConfigDialog
        config = IntegrationsConfigDialog.get_integration_config('pagerduty')
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
            name="pd_create_incident",
            description="Create a PagerDuty incident",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="pd_acknowledge_incident",
            description="Acknowledge an incident",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="pd_get_on_call",
            description="Get current on-call information",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="pd_trigger_escalation",
            description="Trigger escalation policy",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_pagerduty_config()
    
    if not config:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "PagerDuty not configured",
                "message": "Please configure PagerDuty in Settings > Integrations"
            }, indent=2)
        )]
    
    try:
        # TODO: Implement tool handlers
        
        if name == "pd_create_incident":
            # TODO: Implement pd_create_incident
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "pd_acknowledge_incident":
            # TODO: Implement pd_acknowledge_incident
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "pd_get_on_call":
            # TODO: Implement pd_get_on_call
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "pd_trigger_escalation":
            # TODO: Implement pd_trigger_escalation
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        
        
        raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in PagerDuty tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the PagerDuty MCP server."""
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
