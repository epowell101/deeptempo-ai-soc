#!/usr/bin/env python3
"""
Unified SOC MCP Server

This server exposes different tools based on the current mode:
- rules_only: Basic alert tools (no embeddings, no correlation)
- loglm: Full LogLM capabilities (embeddings, similarity search, correlation)

Mode is controlled via a config file that can be toggled from the Streamlit dashboard.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# Configuration
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent.parent.parent / "data"))
SCENARIO_DIR = DATA_DIR / "scenarios" / "default_attack"
MODE_FILE = DATA_DIR / "current_mode.txt"

# Initialize server
server = Server("unified-soc")


def get_current_mode() -> str:
    """Get the current SOC mode from config file."""
    if MODE_FILE.exists():
        return MODE_FILE.read_text().strip()
    return "loglm"  # Default to LogLM mode


def load_alerts():
    """Load rules-only alerts."""
    alerts_file = SCENARIO_DIR / "rules_output" / "alerts.json"
    if alerts_file.exists():
        with open(alerts_file) as f:
            return json.load(f)
    return []


def load_findings():
    """Load LogLM findings."""
    findings_file = SCENARIO_DIR / "loglm_output" / "findings.json"
    if findings_file.exists():
        with open(findings_file) as f:
            return json.load(f)
    return []


def load_incidents():
    """Load LogLM incidents."""
    incidents_file = SCENARIO_DIR / "loglm_output" / "incidents.json"
    if incidents_file.exists():
        with open(incidents_file) as f:
            return json.load(f)
    return []


def load_embeddings():
    """Load embeddings for similarity search."""
    embeddings_file = SCENARIO_DIR / "loglm_output" / "embeddings.json"
    if embeddings_file.exists():
        with open(embeddings_file) as f:
            return json.load(f)
    return {}


def load_evaluation():
    """Load evaluation results."""
    eval_file = SCENARIO_DIR / "evaluation_results.json"
    if eval_file.exists():
        with open(eval_file) as f:
            return json.load(f)
    return {}


def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# ============================================================
# COMMON TOOLS (available in both modes)
# ============================================================

@server.list_tools()
async def list_tools():
    """List available tools based on current mode."""
    mode = get_current_mode()
    
    common_tools = [
        Tool(
            name="get_soc_mode",
            description="Get the current SOC mode (rules_only or loglm)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_raw_logs",
            description="Get raw log events from the scenario",
            inputSchema={
                "type": "object",
                "properties": {
                    "log_type": {
                        "type": "string",
                        "enum": ["conn", "dns", "all"],
                        "description": "Type of logs to retrieve"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of logs to return",
                        "default": 100
                    }
                }
            }
        ),
        Tool(
            name="get_evaluation_metrics",
            description="Get evaluation metrics comparing detection methods",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]
    
    if mode == "rules_only":
        # Rules-only tools
        rules_tools = [
            Tool(
                name="list_alerts",
                description="List security alerts from Sigma rule matches. Returns uncorrelated alerts.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "severity": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Filter by severity"
                        },
                        "rule_name": {
                            "type": "string",
                            "description": "Filter by rule name (partial match)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of alerts to return",
                            "default": 50
                        }
                    }
                }
            ),
            Tool(
                name="get_alert_details",
                description="Get details for a specific alert",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "alert_id": {
                            "type": "string",
                            "description": "The alert ID"
                        }
                    },
                    "required": ["alert_id"]
                }
            ),
            Tool(
                name="get_rule_statistics",
                description="Get statistics about which rules are firing",
                inputSchema={"type": "object", "properties": {}}
            ),
        ]
        return common_tools + rules_tools
    
    else:  # loglm mode
        # LogLM tools
        loglm_tools = [
            Tool(
                name="list_findings",
                description="List security findings with LogLM enrichment. Findings are correlated and include MITRE ATT&CK classification.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "severity": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Filter by severity"
                        },
                        "technique": {
                            "type": "string",
                            "description": "Filter by MITRE technique ID"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of findings to return",
                            "default": 50
                        }
                    }
                }
            ),
            Tool(
                name="get_finding_details",
                description="Get details for a specific finding including MITRE predictions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "finding_id": {
                            "type": "string",
                            "description": "The finding ID"
                        }
                    },
                    "required": ["finding_id"]
                }
            ),
            Tool(
                name="list_incidents",
                description="List correlated security incidents. LogLM automatically groups related findings into incidents.",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="get_incident_details",
                description="Get details for a specific incident including all related findings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "incident_id": {
                            "type": "string",
                            "description": "The incident ID"
                        }
                    },
                    "required": ["incident_id"]
                }
            ),
            Tool(
                name="nearest_neighbors",
                description="Find similar findings using embedding similarity. This enables hunting for related threats.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "finding_id": {
                            "type": "string",
                            "description": "The finding ID to find neighbors for"
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of neighbors to return",
                            "default": 5
                        }
                    },
                    "required": ["finding_id"]
                }
            ),
            Tool(
                name="technique_rollup",
                description="Get MITRE ATT&CK technique statistics across all findings",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="get_attack_narrative",
                description="Get a human-readable narrative of the detected attack",
                inputSchema={"type": "object", "properties": {}}
            ),
        ]
        return common_tools + loglm_tools


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    mode = get_current_mode()
    
    # Common tools
    if name == "get_soc_mode":
        mode_descriptions = {
            "rules_only": "Rules-Only Mode: You have access to Sigma rule alerts but NO embedding-based similarity search, NO automatic correlation, and NO MITRE ATT&CK classification. You must manually investigate and correlate alerts.",
            "loglm": "LogLM-Enhanced Mode: You have access to DeepTempo LogLM findings with embeddings, automatic correlation into incidents, MITRE ATT&CK classification, and similarity search capabilities."
        }
        return [TextContent(
            type="text",
            text=json.dumps({
                "mode": mode,
                "description": mode_descriptions.get(mode, "Unknown mode")
            }, indent=2)
        )]
    
    elif name == "get_raw_logs":
        log_type = arguments.get("log_type", "all")
        limit = arguments.get("limit", 100)
        
        logs = []
        if log_type in ["conn", "all"]:
            conn_file = SCENARIO_DIR / "raw_logs" / "zeek_conn.json"
            if conn_file.exists():
                with open(conn_file) as f:
                    logs.extend(json.load(f))
        
        if log_type in ["dns", "all"]:
            dns_file = SCENARIO_DIR / "raw_logs" / "zeek_dns.json"
            if dns_file.exists():
                with open(dns_file) as f:
                    logs.extend(json.load(f))
        
        logs.sort(key=lambda x: x.get("ts", ""))
        return [TextContent(
            type="text",
            text=json.dumps({
                "total_logs": len(logs),
                "returned": min(limit, len(logs)),
                "logs": logs[:limit]
            }, indent=2)
        )]
    
    elif name == "get_evaluation_metrics":
        eval_results = load_evaluation()
        return [TextContent(
            type="text",
            text=json.dumps(eval_results, indent=2)
        )]
    
    # Rules-only tools
    elif name == "list_alerts" and mode == "rules_only":
        alerts = load_alerts()
        severity = arguments.get("severity")
        rule_name = arguments.get("rule_name")
        limit = arguments.get("limit", 50)
        
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]
        if rule_name:
            alerts = [a for a in alerts if rule_name.lower() in a.get("rule_name", "").lower()]
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "mode": "rules_only",
                "total_alerts": len(alerts),
                "returned": min(limit, len(alerts)),
                "note": "These are uncorrelated alerts. You must manually investigate to determine if they are related.",
                "alerts": alerts[:limit]
            }, indent=2)
        )]
    
    elif name == "get_alert_details" and mode == "rules_only":
        alerts = load_alerts()
        alert_id = arguments.get("alert_id")
        alert = next((a for a in alerts if a.get("id") == alert_id), None)
        
        if alert:
            return [TextContent(type="text", text=json.dumps(alert, indent=2))]
        return [TextContent(type="text", text=f"Alert {alert_id} not found")]
    
    elif name == "get_rule_statistics" and mode == "rules_only":
        stats_file = SCENARIO_DIR / "rules_output" / "rule_stats.json"
        if stats_file.exists():
            with open(stats_file) as f:
                stats = json.load(f)
            return [TextContent(type="text", text=json.dumps(stats, indent=2))]
        return [TextContent(type="text", text="No rule statistics available")]
    
    # LogLM tools
    elif name == "list_findings" and mode == "loglm":
        findings = load_findings()
        severity = arguments.get("severity")
        technique = arguments.get("technique")
        limit = arguments.get("limit", 50)
        
        if severity:
            findings = [f for f in findings if f.get("severity") == severity]
        if technique:
            findings = [f for f in findings if any(
                p.get("technique_id") == technique for p in f.get("mitre_predictions", [])
            )]
        
        # Remove embeddings from response
        findings_clean = []
        for f in findings[:limit]:
            f_copy = {k: v for k, v in f.items() if k != "embedding" and k != "raw_event"}
            findings_clean.append(f_copy)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "mode": "loglm",
                "total_findings": len(findings),
                "returned": len(findings_clean),
                "note": "Findings are automatically correlated and enriched with MITRE ATT&CK classification.",
                "findings": findings_clean
            }, indent=2)
        )]
    
    elif name == "get_finding_details" and mode == "loglm":
        findings = load_findings()
        finding_id = arguments.get("finding_id")
        finding = next((f for f in findings if f.get("id") == finding_id), None)
        
        if finding:
            f_copy = {k: v for k, v in finding.items() if k != "embedding"}
            return [TextContent(type="text", text=json.dumps(f_copy, indent=2))]
        return [TextContent(type="text", text=f"Finding {finding_id} not found")]
    
    elif name == "list_incidents" and mode == "loglm":
        incidents = load_incidents()
        
        # Clean up for response
        incidents_clean = []
        for inc in incidents:
            inc_copy = {k: v for k, v in inc.items() if k != "embedding"}
            incidents_clean.append(inc_copy)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "mode": "loglm",
                "total_incidents": len(incidents_clean),
                "note": "Incidents are automatically correlated groups of related findings.",
                "incidents": incidents_clean
            }, indent=2)
        )]
    
    elif name == "get_incident_details" and mode == "loglm":
        incidents = load_incidents()
        incident_id = arguments.get("incident_id")
        incident = next((i for i in incidents if i.get("id") == incident_id), None)
        
        if incident:
            # Get related findings
            findings = load_findings()
            related = [f for f in findings if f.get("id") in incident.get("finding_ids", [])]
            
            inc_copy = {k: v for k, v in incident.items() if k != "embedding"}
            inc_copy["related_findings"] = [
                {k: v for k, v in f.items() if k not in ["embedding", "raw_event"]}
                for f in related[:20]  # Limit to 20 findings
            ]
            
            return [TextContent(type="text", text=json.dumps(inc_copy, indent=2))]
        return [TextContent(type="text", text=f"Incident {incident_id} not found")]
    
    elif name == "nearest_neighbors" and mode == "loglm":
        finding_id = arguments.get("finding_id")
        k = arguments.get("k", 5)
        
        embeddings = load_embeddings()
        findings = load_findings()
        
        if finding_id not in embeddings:
            return [TextContent(type="text", text=f"Finding {finding_id} not found")]
        
        target_embedding = embeddings[finding_id]
        
        # Calculate similarities
        similarities = []
        for fid, emb in embeddings.items():
            if fid != finding_id:
                sim = cosine_similarity(target_embedding, emb)
                similarities.append((fid, sim))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top k neighbors
        neighbors = []
        for fid, sim in similarities[:k]:
            finding = next((f for f in findings if f.get("id") == fid), None)
            if finding:
                neighbors.append({
                    "finding_id": fid,
                    "similarity": round(sim, 4),
                    "title": finding.get("title"),
                    "severity": finding.get("severity"),
                    "technique": finding.get("mitre_predictions", [{}])[0].get("technique_name")
                })
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "query_finding": finding_id,
                "neighbors": neighbors,
                "note": "Similar findings based on LogLM embedding similarity. Use this to hunt for related threats."
            }, indent=2)
        )]
    
    elif name == "technique_rollup" and mode == "loglm":
        stats_file = SCENARIO_DIR / "loglm_output" / "technique_stats.json"
        if stats_file.exists():
            with open(stats_file) as f:
                stats = json.load(f)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "techniques": stats,
                    "note": "MITRE ATT&CK techniques detected across all findings"
                }, indent=2)
            )]
        return [TextContent(type="text", text="No technique statistics available")]
    
    elif name == "get_attack_narrative" and mode == "loglm":
        incidents = load_incidents()
        main_incident = next((i for i in incidents if i.get("severity") == "critical"), None)
        
        if main_incident:
            narrative = {
                "title": main_incident.get("title"),
                "severity": main_incident.get("severity"),
                "summary": main_incident.get("summary"),
                "phases_detected": main_incident.get("phases_detected"),
                "techniques": main_incident.get("techniques"),
                "affected_hosts": main_incident.get("affected_hosts"),
                "finding_count": main_incident.get("finding_count"),
                "recommendation": "Immediate containment recommended. Isolate affected hosts and block C2 communication."
            }
            return [TextContent(type="text", text=json.dumps(narrative, indent=2))]
        return [TextContent(type="text", text="No attack narrative available")]
    
    # Tool not available in current mode
    return [TextContent(
        type="text",
        text=f"Tool '{name}' is not available in {mode} mode. Current mode: {mode}"
    )]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
