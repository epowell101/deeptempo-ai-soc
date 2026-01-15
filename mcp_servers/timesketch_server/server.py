"""MCP Server for Timesketch integration."""

import asyncio
import logging
import json
from typing import Any
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

server = Server("timesketch-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Timesketch tools."""
    return [
        types.Tool(
            name="list_sketches",
            description="List all Timesketch sketches (investigation workspaces). Use this to see what investigations exist.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_sketch",
            description="Get details about a specific Timesketch sketch including its timelines.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sketch_id": {
                        "type": "integer",
                        "description": "Sketch ID to retrieve"
                    }
                },
                "required": ["sketch_id"]
            }
        ),
        types.Tool(
            name="create_sketch",
            description="Create a new Timesketch sketch (investigation workspace) for log analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name for the sketch"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what this investigation is about",
                        "default": ""
                    }
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="search_timesketch",
            description="Search logs in Timesketch using query string. Returns matching log events for forensic analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (Lucene syntax or keywords)"
                    },
                    "sketch_id": {
                        "type": "integer",
                        "description": "Sketch ID to search in (optional)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 100
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="export_to_timesketch",
            description="Export findings or a case to Timesketch for timeline analysis. Creates a sketch and timeline.",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeline_name": {
                        "type": "string",
                        "description": "Name for the timeline"
                    },
                    "sketch_name": {
                        "type": "string",
                        "description": "Name for new sketch (if creating one)"
                    },
                    "sketch_id": {
                        "type": "integer",
                        "description": "Existing sketch ID to add timeline to"
                    },
                    "case_id": {
                        "type": "string",
                        "description": "Case ID to export"
                    },
                    "finding_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of finding IDs to export"
                    }
                },
                "required": ["timeline_name"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    try:
        from backend.api.timesketch_helper import load_timesketch_service_from_integrations
        from services.timeline_service import TimelineService
        
        timesketch_service = load_timesketch_service_from_integrations()
        if not timesketch_service:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "Timesketch not configured. Please configure Timesketch integration in Settings."}, indent=2)
            )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": f"Could not load Timesketch service: {e}"}, indent=2)
        )]
    
    if name == "list_sketches":
        try:
            sketches = timesketch_service.list_sketches()
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "count": len(sketches),
                    "sketches": sketches
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "get_sketch":
        try:
            sketch_id = arguments.get("sketch_id") if arguments else None
            
            if not sketch_id:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "sketch_id is required"}, indent=2)
                )]
            
            sketch = timesketch_service.get_sketch(sketch_id)
            
            if not sketch:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": f"Sketch {sketch_id} not found"}, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "sketch": sketch
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "create_sketch":
        try:
            name_arg = arguments.get("name") if arguments else None
            description = arguments.get("description", "") if arguments else ""
            
            if not name_arg:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "name is required"}, indent=2)
                )]
            
            sketch_id = timesketch_service.create_sketch(name=name_arg, description=description)
            
            if not sketch_id:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Failed to create sketch"}, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "sketch_id": sketch_id,
                    "name": name_arg,
                    "message": "Sketch created successfully"
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "search_timesketch":
        try:
            query = arguments.get("query") if arguments else None
            sketch_id = arguments.get("sketch_id") if arguments else None
            max_results = arguments.get("max_results", 100) if arguments else 100
            
            if not query:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "query is required"}, indent=2)
                )]
            
            results = timesketch_service.search(
                query=query,
                sketch_id=sketch_id,
                max_results=max_results
            )
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "query": query,
                    "total_hits": len(results),
                    "results": results
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "export_to_timesketch":
        try:
            from services.data_service import DataService
            
            timeline_name = arguments.get("timeline_name") if arguments else None
            sketch_name = arguments.get("sketch_name") if arguments else None
            sketch_id = arguments.get("sketch_id") if arguments else None
            case_id = arguments.get("case_id") if arguments else None
            finding_ids = arguments.get("finding_ids") if arguments else None
            
            if not timeline_name:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "timeline_name is required"}, indent=2)
                )]
            
            # Get or create sketch
            if not sketch_id and sketch_name:
                sketch_id = timesketch_service.create_sketch(
                    name=sketch_name,
                    description=f"Timeline export: {timeline_name}"
                )
                if not sketch_id:
                    return [types.TextContent(
                        type="text",
                        text=json.dumps({"error": "Failed to create sketch"}, indent=2)
                    )]
            elif not sketch_id:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Either sketch_id or sketch_name must be provided"}, indent=2)
                )]
            
            # Prepare timeline events
            data_service = DataService()
            events = []
            
            # Export case with findings
            if case_id:
                case = data_service.get_case(case_id)
                if not case:
                    return [types.TextContent(
                        type="text",
                        text=json.dumps({"error": "Case not found"}, indent=2)
                    )]
                
                finding_ids_from_case = case.get('findings', [])
                findings = [data_service.get_finding(fid) for fid in finding_ids_from_case]
                findings = [f for f in findings if f is not None]
                
                events = TimelineService.case_to_timeline_events(case, findings)
            
            # Export specific findings
            elif finding_ids:
                findings = [data_service.get_finding(fid) for fid in finding_ids]
                findings = [f for f in findings if f is not None]
                
                if not findings:
                    return [types.TextContent(
                        type="text",
                        text=json.dumps({"error": "No findings found"}, indent=2)
                    )]
                
                events = TimelineService.findings_to_timeline_events(findings)
            else:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Either case_id or finding_ids must be provided"}, indent=2)
                )]
            
            if not events:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "No events to export"}, indent=2)
                )]
            
            # Add timeline to sketch
            timeline_id = timesketch_service.add_timeline(
                sketch_id=sketch_id,
                timeline_name=timeline_name,
                events=events
            )
            
            if not timeline_id:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Failed to add timeline to sketch"}, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "sketch_id": sketch_id,
                    "timeline_id": timeline_id,
                    "event_count": len(events),
                    "message": f"Exported {len(events)} events to Timesketch"
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the Timesketch MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="timesketch-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

