"""MCP Server for Hybrid Analysis integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_hybrid_analysis_config():
    """Get Hybrid Analysis configuration from integrations config."""
    try:
        from ui.integrations_config import IntegrationsConfigDialog
        config = IntegrationsConfigDialog.get_integration_config('hybrid_analysis')
        return config
    except Exception as e:
        logger.error(f"Error loading Hybrid Analysis config: {e}")
        return {}

server = Server("hybrid_analysis-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Hybrid Analysis tools."""
    return [
        types.Tool(
            name="ha_submit_file",
            description="Submit a file to Hybrid Analysis for malware analysis. Returns submission ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file to submit for analysis"
                    },
                    "environment_id": {
                        "type": "integer",
                        "description": "Analysis environment ID (e.g., 100=Win7 32bit, 120=Win10 64bit)",
                        "default": 120
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="ha_get_report",
            description="Get detailed analysis report for a submitted sample by hash or submission ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hash": {
                        "type": "string",
                        "description": "File hash (MD5, SHA1, or SHA256) or submission ID"
                    }
                },
                "required": ["hash"]
            }
        ),
        types.Tool(
            name="ha_search_hash",
            description="Search for existing analysis reports by file hash.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hash": {
                        "type": "string",
                        "description": "File hash (MD5, SHA1, or SHA256)"
                    }
                },
                "required": ["hash"]
            }
        ),
        types.Tool(
            name="ha_get_similar_samples",
            description="Get samples similar to a given hash based on behavioral analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hash": {
                        "type": "string",
                        "description": "File hash (SHA256)"
                    }
                },
                "required": ["hash"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_hybrid_analysis_config()
    api_key = config.get('api_key')
    
    if not api_key:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "Hybrid Analysis not configured",
                "message": "Please configure Hybrid Analysis API key in Settings > Integrations"
            }, indent=2)
        )]
    
    try:
        import requests
        
        headers = {
            "api-key": api_key,
            "User-Agent": "Falcon Sandbox",
            "Accept": "application/json"
        }
        
        if name == "ha_submit_file":
            file_path = arguments.get("file_path") if arguments else None
            environment_id = arguments.get("environment_id", 120) if arguments else 120
            
            if not file_path:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "file_path parameter is required"}, indent=2)
                )]
            
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': f}
                    data = {'environment_id': environment_id}
                    
                    response = requests.post(
                        "https://www.hybrid-analysis.com/api/v2/submit/file",
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=60
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    return [types.TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "submission_id": result.get("job_id"),
                            "sha256": result.get("sha256"),
                            "environment_id": result.get("environment_id"),
                            "status": "submitted"
                        }, indent=2)
                    )]
            except FileNotFoundError:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": f"File not found: {file_path}"}, indent=2)
                )]
        
        elif name == "ha_get_report":
            hash_value = arguments.get("hash") if arguments else None
            
            if not hash_value:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "hash parameter is required"}, indent=2)
                )]
            
            url = f"https://www.hybrid-analysis.com/api/v2/report/{hash_value}/summary"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "hash": hash_value,
                        "found": False,
                        "message": "No report found for this hash"
                    }, indent=2)
                )]
            
            response.raise_for_status()
            data = response.json()
            
            result = {
                "hash": hash_value,
                "found": True,
                "verdict": data.get("verdict"),
                "threat_score": data.get("threat_score"),
                "av_detect": data.get("av_detect"),
                "vx_family": data.get("vx_family"),
                "type": data.get("type"),
                "size": data.get("size"),
                "md5": data.get("md5"),
                "sha1": data.get("sha1"),
                "sha256": data.get("sha256"),
                "submit_name": data.get("submit_name"),
                "analysis_start_time": data.get("analysis_start_time"),
                "environment_description": data.get("environment_description"),
                "domains": data.get("domains", [])[:10],
                "hosts": data.get("hosts", [])[:10],
                "mitre_attcks": data.get("mitre_attcks", [])
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "ha_search_hash":
            hash_value = arguments.get("hash") if arguments else None
            
            if not hash_value:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "hash parameter is required"}, indent=2)
                )]
            
            url = "https://www.hybrid-analysis.com/api/v2/search/hash"
            data = {"hash": hash_value}
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            results = response.json()
            
            if not results:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "hash": hash_value,
                        "found": False
                    }, indent=2)
                )]
            
            analyses = []
            for r in results[:5]:  # First 5
                analyses.append({
                    "job_id": r.get("job_id"),
                    "verdict": r.get("verdict"),
                    "threat_score": r.get("threat_score"),
                    "environment_description": r.get("environment_description"),
                    "submit_name": r.get("submit_name"),
                    "analysis_start_time": r.get("analysis_start_time")
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "hash": hash_value,
                    "found": True,
                    "analyses": analyses
                }, indent=2)
            )]
        
        elif name == "ha_get_similar_samples":
            hash_value = arguments.get("hash") if arguments else None
            
            if not hash_value:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "hash parameter is required"}, indent=2)
                )]
            
            url = f"https://www.hybrid-analysis.com/api/v2/report/{hash_value}/similar"
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            similar = []
            for s in data[:10]:  # First 10
                similar.append({
                    "sha256": s.get("sha256"),
                    "verdict": s.get("verdict"),
                    "threat_score": s.get("threat_score"),
                    "vx_family": s.get("vx_family"),
                    "similarity_score": s.get("similarity_score")
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "hash": hash_value,
                    "similar_samples": similar
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
        logger.error(f"Error in Hybrid Analysis tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the Hybrid Analysis MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="hybrid_analysis-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
