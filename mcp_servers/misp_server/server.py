"""MCP Server for MISP (Malware Information Sharing Platform) integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_misp_config():
    """Get MISP configuration from integrations config."""
    try:
        import sys
        from pathlib import Path
        # Add parent directory to path to import config_utils
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from config_utils import get_integration_config
        config = get_integration_config('misp')
        return config
    except Exception as e:
        logger.error(f"Error loading MISP config: {e}")
        return {}

server = Server("misp-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available MISP tools."""
    return [
        types.Tool(
            name="misp_search_attributes",
            description="Search MISP for attributes (IOCs) by value, type, or category. Returns matching indicators and their context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "value": {
                        "type": "string",
                        "description": "Value to search for (IP, hash, domain, etc.)"
                    },
                    "type": {
                        "type": "string",
                        "description": "Attribute type (ip-src, ip-dst, domain, md5, sha256, etc.)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category (Network activity, Payload delivery, etc.)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 100)"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="misp_get_event",
            description="Get detailed information about a specific MISP event by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "MISP event ID"
                    }
                },
                "required": ["event_id"]
            }
        ),
        types.Tool(
            name="misp_add_event",
            description="Create a new MISP event with indicators and metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "info": {
                        "type": "string",
                        "description": "Event description/title"
                    },
                    "threat_level_id": {
                        "type": "integer",
                        "description": "Threat level (1=High, 2=Medium, 3=Low, 4=Undefined)"
                    },
                    "analysis": {
                        "type": "integer",
                        "description": "Analysis status (0=Initial, 1=Ongoing, 2=Complete)"
                    },
                    "distribution": {
                        "type": "integer",
                        "description": "Distribution (0=Your org only, 1=This community, 2=Connected communities, 3=All communities)"
                    }
                },
                "required": ["info"]
            }
        ),
        types.Tool(
            name="misp_add_attribute",
            description="Add an attribute (IOC) to an existing MISP event.",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "MISP event ID"
                    },
                    "type": {
                        "type": "string",
                        "description": "Attribute type (ip-src, domain, md5, sha256, url, etc.)"
                    },
                    "value": {
                        "type": "string",
                        "description": "Attribute value"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category (Network activity, Payload delivery, etc.)"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional comment"
                    }
                },
                "required": ["event_id", "type", "value"]
            }
        ),
        types.Tool(
            name="misp_search_iocs",
            description="Search for Indicators of Compromise across all MISP events. Supports multiple IOC types.",
            inputSchema={
                "type": "object",
                "properties": {
                    "iocs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of IOCs to search for"
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)"
                    },
                    "to_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
                    }
                },
                "required": ["iocs"]
            }
        ),
        types.Tool(
            name="misp_add_sighting",
            description="Add a sighting to an attribute indicating it was observed in your environment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "attribute_id": {
                        "type": "string",
                        "description": "Attribute ID"
                    },
                    "type": {
                        "type": "integer",
                        "description": "Sighting type (0=Sighting, 1=False positive, 2=Expiration)"
                    },
                    "source": {
                        "type": "string",
                        "description": "Source of the sighting"
                    }
                },
                "required": ["attribute_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_misp_config()
    url = config.get('url')
    api_key = config.get('api_key')
    verify_ssl = config.get('verify_ssl', True)
    
    if not url or not api_key:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "MISP not configured",
                "message": "Please configure MISP URL and API key in Settings > Integrations"
            }, indent=2)
        )]
    
    try:
        from pymisp import PyMISP
        
        # Initialize MISP client
        misp = PyMISP(url, api_key, verify_ssl)
        
        if name == "misp_search_attributes":
            value = arguments.get("value") if arguments else None
            attr_type = arguments.get("type") if arguments else None
            category = arguments.get("category") if arguments else None
            limit = arguments.get("limit", 100) if arguments else 100
            
            # Build search parameters
            search_params = {
                "limit": limit,
                "pythonify": False
            }
            if value:
                search_params["value"] = value
            if attr_type:
                search_params["type_attribute"] = attr_type
            if category:
                search_params["category"] = category
            
            result = misp.search("attributes", **search_params)
            
            # Format results
            attributes = result.get('Attribute', [])
            formatted_results = []
            
            for attr in attributes[:limit]:
                formatted_results.append({
                    "id": attr.get('id'),
                    "event_id": attr.get('event_id'),
                    "type": attr.get('type'),
                    "category": attr.get('category'),
                    "value": attr.get('value'),
                    "comment": attr.get('comment'),
                    "to_ids": attr.get('to_ids'),
                    "timestamp": attr.get('timestamp'),
                    "event_info": attr.get('Event', {}).get('info')
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "count": len(formatted_results),
                    "attributes": formatted_results
                }, indent=2)
            )]
        
        elif name == "misp_get_event":
            event_id = arguments.get("event_id") if arguments else None
            if not event_id:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "event_id is required"}, indent=2)
                )]
            
            event = misp.get_event(event_id, pythonify=False)
            
            if 'Event' not in event:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Event not found",
                        "event_id": event_id
                    }, indent=2)
                )]
            
            event_data = event['Event']
            
            result = {
                "success": True,
                "event": {
                    "id": event_data.get('id'),
                    "info": event_data.get('info'),
                    "threat_level_id": event_data.get('threat_level_id'),
                    "analysis": event_data.get('analysis'),
                    "date": event_data.get('date'),
                    "published": event_data.get('published'),
                    "attribute_count": event_data.get('attribute_count'),
                    "attributes": event_data.get('Attribute', [])[:20],  # First 20 attributes
                    "tags": [tag.get('name') for tag in event_data.get('Tag', [])]
                }
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "misp_add_event":
            info = arguments.get("info") if arguments else None
            if not info:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "info is required"}, indent=2)
                )]
            
            threat_level = arguments.get("threat_level_id", 3) if arguments else 3
            analysis = arguments.get("analysis", 0) if arguments else 0
            distribution = arguments.get("distribution", 0) if arguments else 0
            
            event = misp.add_event({
                "info": info,
                "threat_level_id": threat_level,
                "analysis": analysis,
                "distribution": distribution
            }, pythonify=False)
            
            if 'Event' in event:
                event_data = event['Event']
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "event_id": event_data.get('id'),
                        "info": event_data.get('info'),
                        "message": "Event created successfully"
                    }, indent=2)
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Failed to create event",
                        "response": event
                    }, indent=2)
                )]
        
        elif name == "misp_add_attribute":
            event_id = arguments.get("event_id") if arguments else None
            attr_type = arguments.get("type") if arguments else None
            value = arguments.get("value") if arguments else None
            
            if not all([event_id, attr_type, value]):
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "event_id, type, and value are required"
                    }, indent=2)
                )]
            
            category = arguments.get("category", "Network activity") if arguments else "Network activity"
            comment = arguments.get("comment", "") if arguments else ""
            
            attribute = misp.add_attribute(
                event_id,
                {
                    "type": attr_type,
                    "value": value,
                    "category": category,
                    "comment": comment
                },
                pythonify=False
            )
            
            if 'Attribute' in attribute:
                attr_data = attribute['Attribute']
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "attribute_id": attr_data.get('id'),
                        "type": attr_data.get('type'),
                        "value": attr_data.get('value'),
                        "message": "Attribute added successfully"
                    }, indent=2)
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Failed to add attribute",
                        "response": attribute
                    }, indent=2)
                )]
        
        elif name == "misp_search_iocs":
            iocs = arguments.get("iocs") if arguments else []
            if not iocs:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "iocs list is required"}, indent=2)
                )]
            
            from_date = arguments.get("from_date") if arguments else None
            to_date = arguments.get("to_date") if arguments else None
            
            search_params = {
                "value": iocs,
                "pythonify": False
            }
            if from_date:
                search_params["date_from"] = from_date
            if to_date:
                search_params["date_to"] = to_date
            
            result = misp.search("attributes", **search_params)
            
            # Group results by IOC
            ioc_results = {}
            for attr in result.get('Attribute', []):
                ioc_value = attr.get('value')
                if ioc_value not in ioc_results:
                    ioc_results[ioc_value] = []
                
                ioc_results[ioc_value].append({
                    "event_id": attr.get('event_id'),
                    "event_info": attr.get('Event', {}).get('info'),
                    "type": attr.get('type'),
                    "category": attr.get('category'),
                    "comment": attr.get('comment'),
                    "timestamp": attr.get('timestamp')
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "iocs_searched": len(iocs),
                    "iocs_found": len(ioc_results),
                    "results": ioc_results
                }, indent=2)
            )]
        
        elif name == "misp_add_sighting":
            attribute_id = arguments.get("attribute_id") if arguments else None
            if not attribute_id:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "attribute_id is required"}, indent=2)
                )]
            
            sighting_type = arguments.get("type", 0) if arguments else 0
            source = arguments.get("source", "") if arguments else ""
            
            sighting = misp.add_sighting({
                "id": attribute_id,
                "type": sighting_type,
                "source": source
            })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": "Sighting added successfully",
                    "attribute_id": attribute_id
                }, indent=2)
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except ImportError:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "PyMISP library not installed",
                "message": "Please install pymisp: pip install pymisp"
            }, indent=2)
        )]
    except Exception as e:
        logger.error(f"Error in MISP tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the MISP MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="misp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

