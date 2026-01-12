"""MCP Server for Joe Sandbox integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_joe_sandbox_config():
    """Get Joe Sandbox configuration from integrations config."""
    try:
        from ui.integrations_config import IntegrationsConfigDialog
        config = IntegrationsConfigDialog.get_integration_config('joe_sandbox')
        return config
    except Exception as e:
        logger.error(f"Error loading Joe Sandbox config: {e}")
        return {}

server = Server("joe_sandbox-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Joe Sandbox tools."""
    return [
        types.Tool(
            name="joe_submit_sample",
            description="Submit a sample to Joe Sandbox for malware analysis. Supports files and URLs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file to submit (optional if url provided)"
                    },
                    "url": {
                        "type": "string",
                        "description": "URL to analyze (optional if file_path provided)"
                    },
                    "systems": {
                        "type": "string",
                        "description": "Comma-separated list of system IDs (e.g., 'w7', 'w10x64')",
                        "default": "w10x64"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="joe_get_analysis",
            description="Get detailed analysis results for a submitted sample by webid.",
            inputSchema={
                "type": "object",
                "properties": {
                    "webid": {
                        "type": "string",
                        "description": "Web ID of the analysis"
                    }
                },
                "required": ["webid"]
            }
        ),
        types.Tool(
            name="joe_search_behavior",
            description="Search for samples with specific behavior patterns or indicators.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (file hash, domain, IP, etc.)"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="joe_get_iocs",
            description="Extract indicators of compromise (IOCs) from an analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "webid": {
                        "type": "string",
                        "description": "Web ID of the analysis"
                    }
                },
                "required": ["webid"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_joe_sandbox_config()
    api_key = config.get('api_key')
    api_url = config.get('api_url', 'https://jbxcloud.joesecurity.org/api')
    
    if not api_key:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "Joe Sandbox not configured",
                "message": "Please configure Joe Sandbox API key in Settings > Integrations"
            }, indent=2)
        )]
    
    try:
        import requests
        
        if name == "joe_submit_sample":
            file_path = arguments.get("file_path") if arguments else None
            url = arguments.get("url") if arguments else None
            systems = arguments.get("systems", "w10x64") if arguments else "w10x64"
            
            if not file_path and not url:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Either file_path or url parameter is required"}, indent=2)
                )]
            
            data = {
                'apikey': api_key,
                'systems': systems,
                'accept-tac': '1'
            }
            
            if url:
                data['url'] = url
                response = requests.post(f"{api_url}/v2/submission/url", data=data, timeout=60)
            else:
                try:
                    with open(file_path, 'rb') as f:
                        files = {'sample': f}
                        response = requests.post(f"{api_url}/v2/submission/new", data=data, files=files, timeout=60)
                except FileNotFoundError:
                    return [types.TextContent(
                        type="text",
                        text=json.dumps({"error": f"File not found: {file_path}"}, indent=2)
                    )]
            
            response.raise_for_status()
            result = response.json()
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "webids": result.get("webids", []),
                    "submission_id": result.get("submission_id"),
                    "message": "Sample submitted successfully"
                }, indent=2)
            )]
        
        elif name == "joe_get_analysis":
            webid = arguments.get("webid") if arguments else None
            
            if not webid:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "webid parameter is required"}, indent=2)
                )]
            
            data = {'apikey': api_key, 'webid': webid}
            response = requests.post(f"{api_url}/v2/analysis/info", data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            analysis = result.get('data', {})
            
            formatted = {
                "webid": webid,
                "status": analysis.get("status"),
                "filename": analysis.get("filename"),
                "md5": analysis.get("md5"),
                "sha1": analysis.get("sha1"),
                "sha256": analysis.get("sha256"),
                "filesize": analysis.get("filesize"),
                "filetype": analysis.get("filetype"),
                "detection": analysis.get("detection"),
                "score": analysis.get("score"),
                "yara_rules": analysis.get("yara", []),
                "signatures": analysis.get("signatures", [])[:10],  # First 10
                "domains": analysis.get("domains", [])[:10],
                "ips": analysis.get("ips", [])[:10],
                "contacted_hosts": analysis.get("contacted_hosts", [])[:10]
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(formatted, indent=2)
            )]
        
        elif name == "joe_search_behavior":
            query = arguments.get("query") if arguments else None
            
            if not query:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "query parameter is required"}, indent=2)
                )]
            
            data = {
                'apikey': api_key,
                'q': query
            }
            response = requests.post(f"{api_url}/v2/analysis/search", data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            analyses = []
            for item in result.get('data', [])[:10]:  # First 10
                analyses.append({
                    "webid": item.get("webid"),
                    "filename": item.get("filename"),
                    "md5": item.get("md5"),
                    "sha256": item.get("sha256"),
                    "detection": item.get("detection"),
                    "score": item.get("score"),
                    "time": item.get("time")
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "query": query,
                    "results": analyses
                }, indent=2)
            )]
        
        elif name == "joe_get_iocs":
            webid = arguments.get("webid") if arguments else None
            
            if not webid:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "webid parameter is required"}, indent=2)
                )]
            
            data = {'apikey': api_key, 'webid': webid}
            response = requests.post(f"{api_url}/v2/analysis/iocs", data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            iocs = result.get('data', {})
            
            formatted = {
                "webid": webid,
                "file_hashes": {
                    "md5": iocs.get("md5", []),
                    "sha1": iocs.get("sha1", []),
                    "sha256": iocs.get("sha256", [])
                },
                "domains": iocs.get("domains", []),
                "ips": iocs.get("ips", []),
                "urls": iocs.get("urls", [])[:20],  # First 20
                "registry_keys": iocs.get("registry", [])[:10],
                "mutexes": iocs.get("mutexes", [])
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(formatted, indent=2)
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
        logger.error(f"Error in Joe Sandbox tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the Joe Sandbox MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="joe_sandbox-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
