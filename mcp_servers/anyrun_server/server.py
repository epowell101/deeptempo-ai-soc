"""MCP Server for AnyRun integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_anyrun_config():
    """Get Anyrun configuration from integrations config."""
    try:
        import sys
        from pathlib import Path
        # Add parent directory to path to import config_utils
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from config_utils import get_integration_config
        config = get_integration_config('anyrun')
        return config
    except Exception as e:
        logger.error(f"Error loading Anyrun config: {e}")
        return {}

server = Server("anyrun-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available AnyRun tools."""
    return [
        types.Tool(
            name="anyrun_submit_file",
            description="Submit a file to ANY.RUN interactive malware analysis sandbox. Returns task ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file to submit for analysis"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="anyrun_get_report",
            description="Get interactive analysis report for a submitted sample by task UUID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_uuid": {
                        "type": "string",
                        "description": "Task UUID from submission"
                    }
                },
                "required": ["task_uuid"]
            }
        ),
        types.Tool(
            name="anyrun_search_tasks",
            description="Search for analysis tasks by hash, domain, or IP address.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (hash, domain, or IP)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_anyrun_config()
    api_key = config.get('api_key')
    
    if not api_key:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "ANY.RUN not configured",
                "message": "Please configure ANY.RUN API key in Settings > Integrations"
            }, indent=2)
        )]
    
    try:
        import requests
        
        headers = {
            "Authorization": f"API-Key {api_key}",
            "Content-Type": "application/json"
        }
        
        if name == "anyrun_submit_file":
            file_path = arguments.get("file_path") if arguments else None
            
            if not file_path:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "file_path parameter is required"}, indent=2)
                )]
            
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': f}
                    # Note: ANY.RUN API requires multipart/form-data for file upload
                    headers_upload = {"Authorization": f"API-Key {api_key}"}
                    
                    response = requests.post(
                        "https://api.any.run/v1/analysis",
                        headers=headers_upload,
                        files=files,
                        timeout=60
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    return [types.TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "task_uuid": result.get("data", {}).get("taskid"),
                            "status": "submitted",
                            "message": "File submitted to ANY.RUN for analysis"
                        }, indent=2)
                    )]
            except FileNotFoundError:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": f"File not found: {file_path}"}, indent=2)
                )]
        
        elif name == "anyrun_get_report":
            task_uuid = arguments.get("task_uuid") if arguments else None
            
            if not task_uuid:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "task_uuid parameter is required"}, indent=2)
                )]
            
            response = requests.get(
                f"https://api.any.run/v1/analysis/{task_uuid}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 404:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "task_uuid": task_uuid,
                        "found": False,
                        "message": "Task not found"
                    }, indent=2)
                )]
            
            response.raise_for_status()
            data = response.json().get("data", {})
            
            result = {
                "task_uuid": task_uuid,
                "found": True,
                "status": data.get("status"),
                "verdict": data.get("verdict"),
                "malware_family": data.get("malware", {}).get("family"),
                "threats": data.get("threats", []),
                "iocs": {
                    "domains": data.get("iocs", {}).get("domains", [])[:10],
                    "ips": data.get("iocs", {}).get("ips", [])[:10],
                    "urls": data.get("iocs", {}).get("urls", [])[:10]
                },
                "processes": [p.get("name") for p in data.get("processes", [])[:10]],
                "network_connections": len(data.get("network", {}).get("connections", [])),
                "file_activity": len(data.get("files", [])),
                "registry_activity": len(data.get("registry", []))
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "anyrun_search_tasks":
            query = arguments.get("query") if arguments else None
            limit = arguments.get("limit", 10) if arguments else 10
            
            if not query:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "query parameter is required"}, indent=2)
                )]
            
            params = {
                "search": query,
                "limit": limit
            }
            
            response = requests.get(
                "https://api.any.run/v1/analysis/search",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            results = response.json().get("data", {}).get("tasks", [])
            
            tasks = []
            for task in results[:limit]:
                tasks.append({
                    "task_uuid": task.get("uuid"),
                    "name": task.get("name"),
                    "verdict": task.get("verdict"),
                    "malware_family": task.get("malware"),
                    "created": task.get("date"),
                    "tags": task.get("tags", [])
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "query": query,
                    "results": tasks
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
        logger.error(f"Error in ANY.RUN tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the ANY.RUN MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="anyrun-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
