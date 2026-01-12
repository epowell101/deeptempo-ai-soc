"""MCP Server for Tenable integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_tenable_config():
    """Get Tenable configuration from integrations config."""
    try:
        from ui.integrations_config import IntegrationsConfigDialog
        config = IntegrationsConfigDialog.get_integration_config('tenable')
        return config
    except Exception as e:
        logger.error(f"Error loading Tenable config: {e}")
        return {}

server = Server("tenable-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Tenable tools."""
    return [
        types.Tool(
            name="tenable_get_vulnerabilities",
            description="Get vulnerability data",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="tenable_scan_asset",
            description="Scan an asset",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="tenable_get_asset_info",
            description="Get asset information",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="tenable_export_scan",
            description="Export scan results",
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
    
    config = get_tenable_config()
    
    if not config:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "Tenable not configured",
                "message": "Please configure Tenable in Settings > Integrations"
            }, indent=2)
        )]
    
    try:
        # TODO: Implement tool handlers
        
        if name == "tenable_get_vulnerabilities":
            # TODO: Implement tenable_get_vulnerabilities
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "tenable_scan_asset":
            # TODO: Implement tenable_scan_asset
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "tenable_get_asset_info":
            # TODO: Implement tenable_get_asset_info
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "tenable_export_scan":
            # TODO: Implement tenable_export_scan
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        
        
        raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in Tenable tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the Tenable MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="tenable-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
