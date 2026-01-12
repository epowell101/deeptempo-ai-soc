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
            description="Create a new Jira issue for incident tracking or task management.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project key (e.g., 'SEC', 'INCIDENT')"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Issue summary/title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description"
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Issue type (e.g., 'Bug', 'Task', 'Story')",
                        "default": "Task"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["Highest", "High", "Medium", "Low", "Lowest"],
                        "description": "Issue priority",
                        "default": "Medium"
                    }
                },
                "required": ["project", "summary", "description"]
            }
        ),
        types.Tool(
            name="jira_get_issue",
            description="Get details of a specific Jira issue by key.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Issue key (e.g., 'SEC-123')"
                    }
                },
                "required": ["issue_key"]
            }
        ),
        types.Tool(
            name="jira_search_issues",
            description="Search for Jira issues using JQL (Jira Query Language).",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query (e.g., 'project = SEC AND status = Open')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["jql"]
            }
        ),
        types.Tool(
            name="jira_update_issue",
            description="Update a Jira issue with new status, assignee, or comments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Issue key to update"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment to add (optional)"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status (optional)"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Assignee username (optional)"
                    }
                },
                "required": ["issue_key"]
            }
        ),
        types.Tool(
            name="jira_add_comment",
            description="Add a comment to an existing Jira issue.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Issue key"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment text"
                    }
                },
                "required": ["issue_key", "comment"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_jira_config()
    jira_url = config.get('url')
    username = config.get('username')
    api_token = config.get('api_token')
    
    if not all([jira_url, username, api_token]):
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "Jira not configured",
                "message": "Please configure Jira URL, username, and API token in Settings > Integrations"
            }, indent=2)
        )]
    
    try:
        import requests
        from requests.auth import HTTPBasicAuth
        
        auth = HTTPBasicAuth(username, api_token)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if name == "jira_create_issue":
            project = arguments.get("project") if arguments else None
            summary = arguments.get("summary") if arguments else None
            description = arguments.get("description") if arguments else None
            issue_type = arguments.get("issue_type", "Task") if arguments else "Task"
            priority = arguments.get("priority", "Medium") if arguments else "Medium"
            
            if not all([project, summary, description]):
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "project, summary, and description are required"}, indent=2)
                )]
            
            payload = {
                "fields": {
                    "project": {"key": project},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type},
                    "priority": {"name": priority}
                }
            }
            
            response = requests.post(
                f"{jira_url}/rest/api/3/issue",
                auth=auth,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "issue_key": result.get("key"),
                    "issue_id": result.get("id"),
                    "url": f"{jira_url}/browse/{result.get('key')}",
                    "message": "Issue created successfully"
                }, indent=2)
            )]
        
        elif name == "jira_get_issue":
            issue_key = arguments.get("issue_key") if arguments else None
            
            if not issue_key:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "issue_key parameter is required"}, indent=2)
                )]
            
            response = requests.get(
                f"{jira_url}/rest/api/3/issue/{issue_key}",
                auth=auth,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            issue = response.json()
            
            fields = issue.get("fields", {})
            
            result = {
                "key": issue.get("key"),
                "summary": fields.get("summary"),
                "description": fields.get("description"),
                "status": fields.get("status", {}).get("name"),
                "priority": fields.get("priority", {}).get("name"),
                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
                "reporter": fields.get("reporter", {}).get("displayName"),
                "created": fields.get("created"),
                "updated": fields.get("updated"),
                "issue_type": fields.get("issuetype", {}).get("name"),
                "url": f"{jira_url}/browse/{issue.get('key')}"
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "jira_search_issues":
            jql = arguments.get("jql") if arguments else None
            max_results = arguments.get("max_results", 10) if arguments else 10
            
            if not jql:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "jql parameter is required"}, indent=2)
                )]
            
            params = {
                "jql": jql,
                "maxResults": max_results
            }
            
            response = requests.get(
                f"{jira_url}/rest/api/3/search",
                auth=auth,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            issues = []
            for issue in data.get("issues", []):
                fields = issue.get("fields", {})
                issues.append({
                    "key": issue.get("key"),
                    "summary": fields.get("summary"),
                    "status": fields.get("status", {}).get("name"),
                    "priority": fields.get("priority", {}).get("name"),
                    "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
                    "created": fields.get("created")
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "jql": jql,
                    "total": data.get("total"),
                    "issues": issues
                }, indent=2)
            )]
        
        elif name == "jira_update_issue":
            issue_key = arguments.get("issue_key") if arguments else None
            comment = arguments.get("comment") if arguments else None
            status = arguments.get("status") if arguments else None
            assignee = arguments.get("assignee") if arguments else None
            
            if not issue_key:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "issue_key parameter is required"}, indent=2)
                )]
            
            updates = {}
            
            if comment:
                response = requests.post(
                    f"{jira_url}/rest/api/3/issue/{issue_key}/comment",
                    auth=auth,
                    headers=headers,
                    json={"body": comment},
                    timeout=30
                )
                response.raise_for_status()
            
            if assignee:
                updates["assignee"] = {"name": assignee}
            
            if updates:
                response = requests.put(
                    f"{jira_url}/rest/api/3/issue/{issue_key}",
                    auth=auth,
                    headers=headers,
                    json={"fields": updates},
                    timeout=30
                )
                response.raise_for_status()
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "issue_key": issue_key,
                    "message": "Issue updated successfully"
                }, indent=2)
            )]
        
        elif name == "jira_add_comment":
            issue_key = arguments.get("issue_key") if arguments else None
            comment = arguments.get("comment") if arguments else None
            
            if not issue_key or not comment:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "issue_key and comment parameters are required"}, indent=2)
                )]
            
            payload = {
                "body": comment
            }
            
            response = requests.post(
                f"{jira_url}/rest/api/3/issue/{issue_key}/comment",
                auth=auth,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "comment_id": result.get("id"),
                    "message": "Comment added successfully"
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
