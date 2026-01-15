"""MCP Server for MITRE ATT&CK Layer management."""

import asyncio
import logging
import json
from typing import Any
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

server = Server("attack-layer-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available ATT&CK layer tools."""
    return [
        types.Tool(
            name="get_attack_layer",
            description="Get the current MITRE ATT&CK Navigator layer showing technique coverage from findings.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_technique_rollup",
            description="Get statistics about MITRE ATT&CK techniques detected across all findings, with counts and severity breakdown.",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_confidence": {
                        "type": "number",
                        "description": "Minimum confidence threshold (0.0-1.0)",
                        "default": 0.0
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_findings_by_technique",
            description="Get all findings associated with a specific MITRE ATT&CK technique ID (e.g., T1071).",
            inputSchema={
                "type": "object",
                "properties": {
                    "technique_id": {
                        "type": "string",
                        "description": "MITRE ATT&CK technique ID (e.g., T1071, T1059.001)"
                    }
                },
                "required": ["technique_id"]
            }
        ),
        types.Tool(
            name="get_tactics_summary",
            description="Get summary of MITRE ATT&CK tactics detected across all findings.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="create_attack_layer",
            description="Create a new MITRE ATT&CK Navigator layer from findings or a case for visualization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name for the layer"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what this layer represents",
                        "default": ""
                    },
                    "case_id": {
                        "type": "string",
                        "description": "Case ID to create layer from"
                    },
                    "finding_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific finding IDs to include"
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
    
    try:
        from services.data_service import DataService
        data_service = DataService()
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": f"Could not load data service: {e}"}, indent=2)
        )]
    
    if name == "get_attack_layer":
        try:
            layer = data_service.get_demo_layer()
            
            if not layer:
                # Generate a default empty layer
                layer = {
                    "name": "DeepTempo Findings",
                    "version": "4.5",
                    "domain": "enterprise-attack",
                    "description": "ATT&CK techniques detected in findings",
                    "techniques": []
                }
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "layer": layer
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "get_technique_rollup":
        try:
            min_confidence = arguments.get("min_confidence", 0.0) if arguments else 0.0
            
            findings = data_service.get_findings()
            
            technique_counts = {}
            technique_severities = {}
            
            for finding in findings:
                predicted_techniques = finding.get('predicted_techniques', [])
                severity = finding.get('severity', 'unknown')
                
                for tech in predicted_techniques:
                    technique_id = tech.get('technique_id')
                    confidence = tech.get('confidence', 0)
                    
                    if confidence < min_confidence or not technique_id:
                        continue
                    
                    # Count occurrences
                    technique_counts[technique_id] = technique_counts.get(technique_id, 0) + 1
                    
                    # Track severities
                    if technique_id not in technique_severities:
                        technique_severities[technique_id] = {
                            'critical': 0,
                            'high': 0,
                            'medium': 0,
                            'low': 0
                        }
                    
                    technique_severities[technique_id][severity] = \
                        technique_severities[technique_id].get(severity, 0) + 1
            
            # Build result
            techniques = []
            for technique_id, count in technique_counts.items():
                techniques.append({
                    "technique_id": technique_id,
                    "count": count,
                    "severities": technique_severities[technique_id]
                })
            
            # Sort by count
            techniques.sort(key=lambda x: x['count'], reverse=True)
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "total_techniques": len(techniques),
                    "techniques": techniques
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "get_findings_by_technique":
        try:
            technique_id = arguments.get("technique_id") if arguments else None
            
            if not technique_id:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "technique_id is required"}, indent=2)
                )]
            
            findings = data_service.get_findings()
            
            matching_findings = []
            
            for finding in findings:
                predicted_techniques = finding.get('predicted_techniques', [])
                
                for tech in predicted_techniques:
                    if tech.get('technique_id') == technique_id:
                        matching_findings.append(finding)
                        break
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "technique_id": technique_id,
                    "total": len(matching_findings),
                    "findings": matching_findings
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "get_tactics_summary":
        try:
            findings = data_service.get_findings()
            
            # Map techniques to tactics (simplified - in production, use ATT&CK data)
            technique_to_tactic = {
                'T1071': 'Command and Control',
                'T1573': 'Command and Control',
                'T1059': 'Execution',
                'T1055': 'Defense Evasion',
                'T1036': 'Defense Evasion',
                # Add more mappings as needed
            }
            
            tactic_counts = {}
            
            for finding in findings:
                predicted_techniques = finding.get('predicted_techniques', [])
                
                for tech in predicted_techniques:
                    technique_id = tech.get('technique_id', '')
                    
                    # Extract base technique (without sub-technique)
                    base_technique = technique_id.split('.')[0]
                    
                    # Get tactic
                    tactic = technique_to_tactic.get(base_technique, 'Unknown')
                    tactic_counts[tactic] = tactic_counts.get(tactic, 0) + 1
            
            tactics = [
                {"tactic": tactic, "count": count}
                for tactic, count in sorted(
                    tactic_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "tactics": tactics
                }, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "create_attack_layer":
        try:
            name_arg = arguments.get("name") if arguments else None
            description = arguments.get("description", "") if arguments else ""
            case_id = arguments.get("case_id") if arguments else None
            finding_ids = arguments.get("finding_ids") if arguments else None
            
            if not name_arg:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "name is required"}, indent=2)
                )]
            
            # Gather findings
            findings = []
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
            elif finding_ids:
                findings = [data_service.get_finding(fid) for fid in finding_ids]
                findings = [f for f in findings if f is not None]
            else:
                # Use all findings if none specified
                findings = data_service.get_findings()
            
            if not findings:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "No findings found"}, indent=2)
                )]
            
            # Build layer from findings
            technique_data = {}
            
            for finding in findings:
                predicted_techniques = finding.get('predicted_techniques', [])
                severity = finding.get('severity', 'medium')
                
                for tech in predicted_techniques:
                    technique_id = tech.get('technique_id')
                    confidence = tech.get('confidence', 0)
                    
                    if not technique_id:
                        continue
                    
                    if technique_id not in technique_data:
                        technique_data[technique_id] = {
                            'techniqueID': technique_id,
                            'score': 0,
                            'count': 0,
                            'color': '',
                            'comment': ''
                        }
                    
                    technique_data[technique_id]['count'] += 1
                    technique_data[technique_id]['score'] = max(
                        technique_data[technique_id]['score'],
                        confidence
                    )
            
            # Assign colors based on count
            max_count = max([t['count'] for t in technique_data.values()]) if technique_data else 1
            for tech_id, data in technique_data.items():
                count = data['count']
                if count >= max_count * 0.75:
                    data['color'] = '#ff0000'  # Red for high activity
                elif count >= max_count * 0.5:
                    data['color'] = '#ff9900'  # Orange for medium
                else:
                    data['color'] = '#ffff00'  # Yellow for low
                
                data['comment'] = f"Detected {count} time(s) with max confidence {data['score']:.2f}"
            
            # Create layer structure
            layer = {
                "name": name_arg,
                "version": "4.5",
                "domain": "enterprise-attack",
                "description": description or f"ATT&CK layer generated from {len(findings)} findings",
                "techniques": list(technique_data.values())
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "layer": layer,
                    "technique_count": len(technique_data),
                    "finding_count": len(findings),
                    "message": f"Created ATT&CK layer with {len(technique_data)} techniques from {len(findings)} findings"
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
    """Run the ATT&CK Layer MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="attack-layer-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

