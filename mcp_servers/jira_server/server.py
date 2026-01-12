"""MCP Server for Jira integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_jira_config():
    """Get Jira configuration from integrations config."""
    try:
        from ui.integrations_config import IntegrationsConfigDialog
        config = IntegrationsConfigDialog.get_integration_config('jira')
        return config
    except Exception as e:
        logger.error(f"Error loading Jira config: {e}")
        return {}

server = Server("jira-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Jira tools."""
    return [
        types.Tool(
            name="jira_create_issue",
            description="Create a new Jira issue/ticket",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="jira_update_issue",
            description="Update an existing Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="jira_search_issues",
            description="Search for Jira issues",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="jira_add_comment",
            description="Add a comment to a Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    # TODO: Define tool parameters
                },
                "required": []
            }
        ),
        types.Tool(
            name="jira_transition_issue",
            description="Transition issue workflow state",
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
    
    config = get_jira_config()
    
    if not config:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "Jira not configured",
                "message": "Please configure Jira in Settings > Integrations"
            }, indent=2)
        )]
    
    try:
        # TODO: Implement tool handlers
        
        if name == "jira_create_issue":
            # TODO: Implement jira_create_issue
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "jira_update_issue":
            # TODO: Implement jira_update_issue
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "jira_search_issues":
            # TODO: Implement jira_search_issues
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "jira_add_comment":
            # TODO: Implement jira_add_comment
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        

        if name == "jira_transition_issue":
            # TODO: Implement jira_transition_issue
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Not implemented",
                    "message": "This tool is not yet implemented"
                }, indent=2)
            )]
        
        
        raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in Jira tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the Jira MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jira-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
