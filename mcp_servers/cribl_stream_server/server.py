"""MCP Server for Cribl Stream data pipeline management."""

import asyncio
import logging
import json
import os
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

# Cribl Stream configuration from environment or config
def get_cribl_config():
    """Get Cribl Stream configuration from environment or config file."""
    from pathlib import Path
    import json
    
    config = {
        "server_url": os.environ.get("CRIBL_URL"),
        "username": os.environ.get("CRIBL_USERNAME"),
        "password": os.environ.get("CRIBL_PASSWORD"),
        "verify_ssl": os.environ.get("CRIBL_VERIFY_SSL", "false").lower() == "true",
        "worker_group": os.environ.get("CRIBL_WORKER_GROUP", "default")
    }
    
    # Try to load from config file if env vars not set
    if not config["server_url"]:
        config_file = Path.home() / ".deeptempo" / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    cribl_config = file_config.get("cribl", {})
                    config.update({
                        "server_url": cribl_config.get("server_url"),
                        "username": cribl_config.get("username"),
                        "password": cribl_config.get("password"),
                        "verify_ssl": cribl_config.get("verify_ssl", False),
                        "worker_group": cribl_config.get("worker_group", "default")
                    })
            except Exception as e:
                logger.warning(f"Could not load config from file: {e}")
    
    return config

def get_cribl_service():
    """Get configured Cribl Stream service instance."""
    try:
        from services.cribl_service import CriblService
        config = get_cribl_config()
        
        if not config.get("server_url"):
            return None
            
        return CriblService(
            server_url=config["server_url"],
            username=config["username"],
            password=config["password"],
            verify_ssl=config["verify_ssl"]
        )
    except Exception as e:
        logger.error(f"Error creating Cribl Stream service: {e}")
        return None

server = Server("cribl-stream-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Cribl Stream tools."""
    return [
        types.Tool(
            name="get_pipelines",
            description="Get list of configured data processing pipelines in Cribl Stream. Pipelines define how data is transformed, enriched, filtered, and routed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "worker_group": {
                        "type": "string",
                        "description": "Worker group to query (default: 'default')"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_routes",
            description="Get list of configured data routes. Routes determine which data flows through which pipelines to which destinations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "worker_group": {
                        "type": "string",
                        "description": "Worker group to query (default: 'default')"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_data_sources",
            description="Get list of configured data sources (inputs) in Cribl Stream. Shows where data is being ingested from (Splunk, Syslog, HTTP, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "worker_group": {
                        "type": "string",
                        "description": "Worker group to query (default: 'default')"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_destinations",
            description="Get list of configured data destinations (outputs). Shows where processed data is being sent (Splunk, S3, Kafka, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "worker_group": {
                        "type": "string",
                        "description": "Worker group to query (default: 'default')"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_metrics",
            description="Get system metrics showing data throughput, event rates, pipeline performance, and resource utilization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "worker_group": {
                        "type": "string",
                        "description": "Worker group to query (default: 'default')"
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time range for metrics (e.g., '1h', '24h', '7d', default: '1h')"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_health_status",
            description="Get overall health status of Cribl Stream system including worker status, connectivity, and resource health.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="create_pipeline",
            description="Create a new data processing pipeline. Pipelines can filter, transform, enrich, mask, or sample data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_id": {
                        "type": "string",
                        "description": "Unique identifier for the pipeline"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of pipeline purpose"
                    },
                    "functions": {
                        "type": "array",
                        "description": "Array of function configurations to apply",
                        "items": {
                            "type": "object"
                        }
                    },
                    "worker_group": {
                        "type": "string",
                        "description": "Worker group (default: 'default')"
                    }
                },
                "required": ["pipeline_id", "functions"]
            }
        ),
        types.Tool(
            name="apply_route",
            description="Create or update a route to direct data from sources through pipelines to destinations. Routes use filter expressions to match events.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_filter": {
                        "type": "string",
                        "description": "Filter expression to match source data (e.g., 'sourcetype==syslog' or '__inputId==\"splunk:main\"')"
                    },
                    "pipeline": {
                        "type": "string",
                        "description": "Pipeline ID to apply to matched data"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination ID where data should be sent"
                    },
                    "worker_group": {
                        "type": "string",
                        "description": "Worker group (default: 'default')"
                    }
                },
                "required": ["source_filter", "pipeline", "destination"]
            }
        ),
        types.Tool(
            name="preview_pipeline",
            description="Preview how a pipeline would transform sample data. Useful for testing pipeline configurations before deployment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_id": {
                        "type": "string",
                        "description": "Pipeline ID to test"
                    },
                    "sample_data": {
                        "type": "array",
                        "description": "Array of sample events to transform",
                        "items": {
                            "type": "object"
                        }
                    },
                    "worker_group": {
                        "type": "string",
                        "description": "Worker group (default: 'default')"
                    }
                },
                "required": ["pipeline_id", "sample_data"]
            }
        ),
        types.Tool(
            name="get_data_flow_summary",
            description="Get a comprehensive summary of data flowing through Cribl Stream, including sources, pipelines, routes, and destinations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "worker_group": {
                        "type": "string",
                        "description": "Worker group to query (default: 'default')"
                    }
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
    
    # Get Cribl service
    cribl = get_cribl_service()
    
    if not cribl and name != "get_health_status":
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "Cribl Stream not configured",
                "message": "Please configure Cribl Stream connection in ~/.deeptempo/config.json or environment variables",
                "required_config": {
                    "server_url": "https://cribl.example.com:9000",
                    "username": "admin",
                    "password": "password",
                    "verify_ssl": False,
                    "worker_group": "default"
                }
            }, indent=2)
        )]
    
    worker_group = arguments.get("worker_group", "default") if arguments else "default"
    
    if name == "get_pipelines":
        try:
            pipelines = cribl.get_pipelines(worker_group)
            
            if pipelines is None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Failed to retrieve pipelines"}, indent=2)
                )]
            
            # Format pipeline summary
            summary = {
                "worker_group": worker_group,
                "pipeline_count": len(pipelines),
                "pipelines": [
                    {
                        "id": p.get("id"),
                        "description": p.get("description", ""),
                        "function_count": len(p.get("conf", {}).get("functions", [])),
                        "enabled": p.get("conf", {}).get("enabled", True)
                    }
                    for p in pipelines
                ]
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(summary, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "get_routes":
        try:
            routes = cribl.get_routes(worker_group)
            
            if routes is None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Failed to retrieve routes"}, indent=2)
                )]
            
            summary = {
                "worker_group": worker_group,
                "route_count": len(routes),
                "routes": [
                    {
                        "id": r.get("id"),
                        "filter": r.get("filter", ""),
                        "pipeline": r.get("pipeline", ""),
                        "output": r.get("output", ""),
                        "enabled": r.get("enabled", True)
                    }
                    for r in routes
                ]
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(summary, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "get_data_sources":
        try:
            sources = cribl.get_sources(worker_group)
            
            if sources is None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Failed to retrieve data sources"}, indent=2)
                )]
            
            summary = {
                "worker_group": worker_group,
                "source_count": len(sources),
                "sources": [
                    {
                        "id": s.get("id"),
                        "type": s.get("type", ""),
                        "description": s.get("description", ""),
                        "enabled": s.get("enabled", True)
                    }
                    for s in sources
                ]
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(summary, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "get_destinations":
        try:
            destinations = cribl.get_destinations(worker_group)
            
            if destinations is None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Failed to retrieve destinations"}, indent=2)
                )]
            
            summary = {
                "worker_group": worker_group,
                "destination_count": len(destinations),
                "destinations": [
                    {
                        "id": d.get("id"),
                        "type": d.get("type", ""),
                        "description": d.get("description", ""),
                        "enabled": d.get("enabled", True)
                    }
                    for d in destinations
                ]
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(summary, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "get_metrics":
        time_range = arguments.get("time_range", "1h") if arguments else "1h"
        
        try:
            metrics = cribl.get_metrics(worker_group, time_range)
            
            if metrics is None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Failed to retrieve metrics"}, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "worker_group": worker_group,
                    "time_range": time_range,
                    "metrics": metrics
                }, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "get_health_status":
        try:
            health = cribl.get_health_status()
            
            if health is None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Failed to retrieve health status"}, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps(health, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "create_pipeline":
        pipeline_id = arguments.get("pipeline_id") if arguments else None
        description = arguments.get("description", "") if arguments else ""
        functions = arguments.get("functions", []) if arguments else []
        
        if not pipeline_id:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "pipeline_id is required"}, indent=2)
            )]
        
        if not functions:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "functions array is required"}, indent=2)
            )]
        
        try:
            config = {
                "id": pipeline_id,
                "conf": {
                    "description": description,
                    "functions": functions,
                    "enabled": True
                }
            }
            
            result = cribl.create_pipeline(pipeline_id, config, worker_group)
            
            if result is None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Failed to create pipeline"}, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"Pipeline '{pipeline_id}' created successfully",
                    "pipeline": result
                }, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "apply_route":
        source_filter = arguments.get("source_filter") if arguments else None
        pipeline = arguments.get("pipeline") if arguments else None
        destination = arguments.get("destination") if arguments else None
        
        if not all([source_filter, pipeline, destination]):
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "source_filter, pipeline, and destination are required"
                }, indent=2)
            )]
        
        try:
            result = cribl.apply_route(source_filter, pipeline, destination, worker_group)
            
            if result is None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Failed to create route"}, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": "Route created successfully",
                    "route": result
                }, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "preview_pipeline":
        pipeline_id = arguments.get("pipeline_id") if arguments else None
        sample_data = arguments.get("sample_data", []) if arguments else []
        
        if not pipeline_id:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "pipeline_id is required"}, indent=2)
            )]
        
        if not sample_data:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "sample_data is required"}, indent=2)
            )]
        
        try:
            result = cribl.preview_pipeline(pipeline_id, sample_data, worker_group)
            
            if result is None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Failed to preview pipeline"}, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "pipeline": pipeline_id,
                    "preview": result
                }, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "get_data_flow_summary":
        try:
            # Get all components
            sources = cribl.get_sources(worker_group) or []
            pipelines = cribl.get_pipelines(worker_group) or []
            routes = cribl.get_routes(worker_group) or []
            destinations = cribl.get_destinations(worker_group) or []
            metrics = cribl.get_metrics(worker_group, "1h")
            
            summary = {
                "worker_group": worker_group,
                "overview": {
                    "sources": len(sources),
                    "pipelines": len(pipelines),
                    "routes": len(routes),
                    "destinations": len(destinations)
                },
                "data_flow": {
                    "sources": [
                        {"id": s.get("id"), "type": s.get("type"), "enabled": s.get("enabled")}
                        for s in sources
                    ],
                    "active_routes": [
                        {
                            "filter": r.get("filter"),
                            "pipeline": r.get("pipeline"),
                            "output": r.get("output")
                        }
                        for r in routes if r.get("enabled", True)
                    ],
                    "destinations": [
                        {"id": d.get("id"), "type": d.get("type"), "enabled": d.get("enabled")}
                        for d in destinations
                    ]
                },
                "metrics": metrics
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(summary, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the Cribl Stream MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cribl-stream-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

