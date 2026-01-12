"""MCP Server for Approval Workflow management."""

import asyncio
import logging
import json
from typing import Any
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

server = Server("approval-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available approval tools."""
    return [
        types.Tool(
            name="create_approval_action",
            description="Submit an action to the approval queue. Use this when you want to propose a security action that requires approval (e.g., isolating a host, blocking an IP). Actions with confidence >= 0.90 are auto-approved.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action_type": {
                        "type": "string",
                        "enum": ["isolate_host", "block_ip", "block_domain", "quarantine_file", "disable_user", "execute_spl_query", "custom"],
                        "description": "Type of action to perform"
                    },
                    "title": {
                        "type": "string",
                        "description": "Short title for the action"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of what the action will do and why"
                    },
                    "target": {
                        "type": "string",
                        "description": "Target of the action (IP address, hostname, username, etc.)"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score (0.0-1.0). >= 0.90 auto-approves, 0.85-0.89 auto-approves with flag, 0.70-0.84 requires approval, < 0.70 monitor only",
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "reason": {
                        "type": "string",
                        "description": "Detailed reason for taking this action"
                    },
                    "evidence": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of evidence IDs (finding IDs, alert IDs, etc.) supporting this action"
                    },
                    "created_by": {
                        "type": "string",
                        "description": "Who is creating this action (agent name, analyst name, etc.)",
                        "default": "agent"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Optional action-specific parameters as JSON object"
                    }
                },
                "required": ["action_type", "title", "description", "target", "confidence", "reason", "evidence"]
            }
        ),
        types.Tool(
            name="list_approval_actions",
            description="List approval actions with optional filters. Use this to see pending actions, approved actions, or all actions in the queue.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "approved", "rejected", "executed", "failed"],
                        "description": "Filter by action status (optional)"
                    },
                    "action_type": {
                        "type": "string",
                        "enum": ["isolate_host", "block_ip", "block_domain", "quarantine_file", "disable_user", "execute_spl_query", "custom"],
                        "description": "Filter by action type (optional)"
                    },
                    "requires_approval": {
                        "type": "boolean",
                        "description": "Filter by whether approval is required (optional)"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_approval_action",
            description="Get details of a specific approval action by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action_id": {
                        "type": "string",
                        "description": "Action ID to retrieve"
                    }
                },
                "required": ["action_id"]
            }
        ),
        types.Tool(
            name="approve_action",
            description="Approve a pending action. This should only be used after careful review of the action details and evidence.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action_id": {
                        "type": "string",
                        "description": "Action ID to approve"
                    },
                    "approved_by": {
                        "type": "string",
                        "description": "Name of person/agent approving",
                        "default": "analyst"
                    }
                },
                "required": ["action_id"]
            }
        ),
        types.Tool(
            name="reject_action",
            description="Reject a pending action with a reason. Use this when an action is a false positive or not appropriate.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action_id": {
                        "type": "string",
                        "description": "Action ID to reject"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for rejection"
                    },
                    "rejected_by": {
                        "type": "string",
                        "description": "Name of person/agent rejecting",
                        "default": "analyst"
                    }
                },
                "required": ["action_id", "reason"]
            }
        ),
        types.Tool(
            name="get_approval_stats",
            description="Get statistics about approval actions (total, pending, approved, executed, etc.).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="correlate_and_create_action",
            description="Advanced tool: Correlate alerts from multiple sources, calculate confidence score, and automatically create an approval action. This is the primary tool for the auto-responder agent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "finding_id": {
                        "type": "string",
                        "description": "Primary finding ID to investigate"
                    },
                    "auto_execute": {
                        "type": "boolean",
                        "description": "Whether to auto-execute high-confidence actions (>= 0.90)",
                        "default": True
                    }
                },
                "required": ["finding_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    try:
        from services.approval_service import (
            get_approval_service, 
            ActionType, 
            ActionStatus
        )
        approval_service = get_approval_service()
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": f"Could not load approval service: {e}"}, indent=2)
        )]
    
    if name == "create_approval_action":
        try:
            action_type_str = arguments.get("action_type") if arguments else None
            title = arguments.get("title") if arguments else None
            description = arguments.get("description") if arguments else None
            target = arguments.get("target") if arguments else None
            confidence = arguments.get("confidence") if arguments else None
            reason = arguments.get("reason") if arguments else None
            evidence = arguments.get("evidence", []) if arguments else []
            created_by = arguments.get("created_by", "agent") if arguments else "agent"
            parameters = arguments.get("parameters") if arguments else None
            
            if not all([action_type_str, title, description, target, confidence is not None, reason]):
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Missing required parameters",
                        "required": ["action_type", "title", "description", "target", "confidence", "reason", "evidence"]
                    }, indent=2)
                )]
            
            # Convert action_type string to enum
            action_type = ActionType(action_type_str)
            
            # Create action
            action = approval_service.create_action(
                action_type=action_type,
                title=title,
                description=description,
                target=target,
                confidence=confidence,
                reason=reason,
                evidence=evidence,
                created_by=created_by,
                parameters=parameters
            )
            
            result = {
                "success": True,
                "action_id": action.action_id,
                "status": action.status,
                "requires_approval": action.requires_approval,
                "message": f"Action created successfully. Status: {action.status}"
            }
            
            if action.status == "approved":
                result["message"] += f" (Auto-approved due to high confidence: {confidence:.1%})"
            elif action.requires_approval:
                result["message"] += f" (Requires approval - confidence: {confidence:.1%})"
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "list_approval_actions":
        try:
            status_str = arguments.get("status") if arguments else None
            action_type_str = arguments.get("action_type") if arguments else None
            requires_approval = arguments.get("requires_approval") if arguments else None
            
            # Convert strings to enums
            status = ActionStatus(status_str) if status_str else None
            action_type = ActionType(action_type_str) if action_type_str else None
            
            actions = approval_service.list_actions(
                status=status,
                action_type=action_type,
                requires_approval=requires_approval
            )
            
            # Convert to serializable format
            actions_list = []
            for action in actions:
                actions_list.append({
                    "action_id": action.action_id,
                    "action_type": action.action_type,
                    "title": action.title,
                    "target": action.target,
                    "confidence": action.confidence,
                    "status": action.status,
                    "requires_approval": action.requires_approval,
                    "created_at": action.created_at,
                    "created_by": action.created_by,
                    "evidence_count": len(action.evidence)
                })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "count": len(actions_list),
                    "actions": actions_list
                }, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "get_approval_action":
        try:
            action_id = arguments.get("action_id") if arguments else None
            
            if not action_id:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "action_id is required"}, indent=2)
                )]
            
            action = approval_service.get_action(action_id)
            
            if not action:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": f"Action {action_id} not found"}, indent=2)
                )]
            
            # Convert to serializable format
            action_dict = {
                "action_id": action.action_id,
                "action_type": action.action_type,
                "title": action.title,
                "description": action.description,
                "target": action.target,
                "confidence": action.confidence,
                "reason": action.reason,
                "evidence": action.evidence,
                "status": action.status,
                "requires_approval": action.requires_approval,
                "created_at": action.created_at,
                "created_by": action.created_by,
                "approved_at": action.approved_at,
                "approved_by": action.approved_by,
                "executed_at": action.executed_at,
                "execution_result": action.execution_result,
                "rejection_reason": action.rejection_reason,
                "parameters": action.parameters
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "action": action_dict
                }, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "approve_action":
        try:
            action_id = arguments.get("action_id") if arguments else None
            approved_by = arguments.get("approved_by", "analyst") if arguments else "analyst"
            
            if not action_id:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "action_id is required"}, indent=2)
                )]
            
            action = approval_service.approve_action(action_id, approved_by)
            
            if not action:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": f"Action {action_id} not found"}, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "action_id": action.action_id,
                    "status": action.status,
                    "message": f"Action approved by {approved_by}"
                }, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "reject_action":
        try:
            action_id = arguments.get("action_id") if arguments else None
            reason = arguments.get("reason") if arguments else None
            rejected_by = arguments.get("rejected_by", "analyst") if arguments else "analyst"
            
            if not action_id or not reason:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "action_id and reason are required"
                    }, indent=2)
                )]
            
            action = approval_service.reject_action(action_id, reason, rejected_by)
            
            if not action:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": f"Action {action_id} not found"}, indent=2)
                )]
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "action_id": action.action_id,
                    "status": action.status,
                    "message": f"Action rejected by {rejected_by}: {reason}"
                }, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "get_approval_stats":
        try:
            stats = approval_service.get_stats()
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "stats": stats
                }, indent=2)
            )]
        
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    elif name == "correlate_and_create_action":
        try:
            from services.autonomous_response_service import get_autonomous_response_service
            
            finding_id = arguments.get("finding_id") if arguments else None
            auto_execute = arguments.get("auto_execute", True) if arguments else True
            
            if not finding_id:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "finding_id is required"}, indent=2)
                )]
            
            # Use autonomous response service
            auto_response = get_autonomous_response_service()
            result = auto_response.investigate_and_respond(finding_id, auto_execute)
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "investigation_result": result
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
    """Run the Approval MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="approval-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

