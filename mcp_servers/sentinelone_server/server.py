"""MCP Server for SentinelOne integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_sentinelone_config():
    """Get SentinelOne configuration from integrations config."""
    try:
        from ui.integrations_config import IntegrationsConfigDialog
        config = IntegrationsConfigDialog.get_integration_config('sentinelone')
        return config
    except Exception as e:
        logger.error(f"Error loading SentinelOne config: {e}")
        return {}

server = Server("sentinelone-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available SentinelOne tools."""
    return [
        types.Tool(
            name="s1_get_threats",
            description="Get SentinelOne threats",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="s1_isolate_endpoint",
            description="Isolate an endpoint",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="s1_remediate_threat",
            description="Remediate a detected threat",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="s1_get_deep_visibility",
            description="Get deep visibility data",
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
    
    config = get_sentinelone_config()
    
    if not config:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "SentinelOne not configured",
                "message": "Please configure SentinelOne in Settings > Integrations"
            }, indent=2)
        )]
    
    try:
        # TODO: Implement tool handlers
        
        if name == "s1_get_threats":
            # TODO: Implement s1_get_threats
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "s1_isolate_endpoint":
            # TODO: Implement s1_isolate_endpoint
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "s1_remediate_threat":
            # TODO: Implement s1_remediate_threat
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "s1_get_deep_visibility":
            # TODO: Implement s1_get_deep_visibility
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        
        
        raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in SentinelOne tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the SentinelOne MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sentinelone-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
