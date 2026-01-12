"""MCP Server for Slack integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_slack_config():
    """Get Slack configuration from integrations config."""
    try:
        from ui.integrations_config import IntegrationsConfigDialog
        config = IntegrationsConfigDialog.get_integration_config('slack')
        return config
    except Exception as e:
        logger.error(f"Error loading Slack config: {e}")
        return {}

server = Server("slack-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Slack tools."""
    return [
        types.Tool(
            name="slack_send_message",
            description="Send a message to a Slack channel. Use for security alerts and notifications.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID or name (e.g., '#security-alerts' or 'C1234567890')"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message text to send"
                    },
                    "thread_ts": {
                        "type": "string",
                        "description": "Thread timestamp to reply to (optional)"
                    }
                },
                "required": ["channel", "message"]
            }
        ),
        types.Tool(
            name="slack_send_alert",
            description="Send a formatted security alert to Slack with severity coloring and structured data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID or name"
                    },
                    "title": {
                        "type": "string",
                        "description": "Alert title"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "info"],
                        "description": "Alert severity level"
                    },
                    "description": {
                        "type": "string",
                        "description": "Alert description"
                    },
                    "fields": {
                        "type": "object",
                        "description": "Additional fields as key-value pairs"
                    }
                },
                "required": ["channel", "title", "severity", "description"]
            }
        ),
        types.Tool(
            name="slack_get_channel_history",
            description="Get recent message history from a Slack channel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of messages to retrieve (default: 10)",
                        "default": 10
                    }
                },
                "required": ["channel"]
            }
        ),
        types.Tool(
            name="slack_create_channel",
            description="Create a new Slack channel (e.g., for incident response).",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Channel name (lowercase, no spaces)"
                    },
                    "is_private": {
                        "type": "boolean",
                        "description": "Whether channel should be private",
                        "default": False
                    }
                },
                "required": ["name"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_slack_config()
    bot_token = config.get('bot_token')
    
    if not bot_token:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "Slack not configured",
                "message": "Please configure Slack bot token in Settings > Integrations"
            }, indent=2)
        )]
    
    try:
        import requests
        
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
        
        if name == "slack_send_message":
            channel = arguments.get("channel") if arguments else None
            message = arguments.get("message") if arguments else None
            thread_ts = arguments.get("thread_ts") if arguments else None
            
            if not channel or not message:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "channel and message parameters are required"}, indent=2)
                )]
            
            payload = {
                "channel": channel,
                "text": message
            }
            
            if thread_ts:
                payload["thread_ts"] = thread_ts
            
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if not result.get("ok"):
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": result.get("error"),
                        "message": "Failed to send Slack message"
                    }, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "channel": result.get("channel"),
                    "ts": result.get("ts"),
                    "message": "Message sent successfully"
                }, indent=2)
            )]
        
        elif name == "slack_send_alert":
            channel = arguments.get("channel") if arguments else None
            title = arguments.get("title") if arguments else None
            severity = arguments.get("severity") if arguments else None
            description = arguments.get("description") if arguments else None
            fields = arguments.get("fields", {}) if arguments else {}
            
            if not all([channel, title, severity, description]):
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "channel, title, severity, and description are required"}, indent=2)
                )]
            
            # Color coding based on severity
            color_map = {
                "critical": "#ff0000",
                "high": "#ff6600",
                "medium": "#ffcc00",
                "low": "#00cc00",
                "info": "#0099cc"
            }
            
            # Build blocks for rich formatting
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 {title}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Severity:* {severity.upper()}\n\n{description}"
                    }
                }
            ]
            
            # Add additional fields if provided
            if fields:
                field_items = []
                for key, value in fields.items():
                    field_items.append({
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n{value}"
                    })
                
                blocks.append({
                    "type": "section",
                    "fields": field_items
                })
            
            payload = {
                "channel": channel,
                "blocks": blocks,
                "attachments": [{
                    "color": color_map.get(severity, "#808080")
                }]
            }
            
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if not result.get("ok"):
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": result.get("error"),
                        "message": "Failed to send alert"
                    }, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "channel": result.get("channel"),
                    "ts": result.get("ts"),
                    "message": "Alert sent successfully"
                }, indent=2)
            )]
        
        elif name == "slack_get_channel_history":
            channel = arguments.get("channel") if arguments else None
            limit = arguments.get("limit", 10) if arguments else 10
            
            if not channel:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "channel parameter is required"}, indent=2)
                )]
            
            params = {
                "channel": channel,
                "limit": limit
            }
            
            response = requests.get(
                "https://slack.com/api/conversations.history",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if not result.get("ok"):
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": result.get("error"),
                        "message": "Failed to get channel history"
                    }, indent=2)
                )]
            
            messages = []
            for msg in result.get("messages", []):
                messages.append({
                    "text": msg.get("text"),
                    "user": msg.get("user"),
                    "ts": msg.get("ts"),
                    "type": msg.get("type")
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "channel": channel,
                    "messages": messages
                }, indent=2)
            )]
        
        elif name == "slack_create_channel":
            name_param = arguments.get("name") if arguments else None
            is_private = arguments.get("is_private", False) if arguments else False
            
            if not name_param:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "name parameter is required"}, indent=2)
                )]
            
            payload = {
                "name": name_param,
                "is_private": is_private
            }
            
            response = requests.post(
                "https://slack.com/api/conversations.create",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if not result.get("ok"):
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": result.get("error"),
                        "message": "Failed to create channel"
                    }, indent=2)
                )]
            
            channel_info = result.get("channel", {})
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "channel_id": channel_info.get("id"),
                    "channel_name": channel_info.get("name"),
                    "is_private": channel_info.get("is_private"),
                    "message": "Channel created successfully"
                }, indent=2)
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
        logger.error(f"Error in Slack tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the Slack MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="slack-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
