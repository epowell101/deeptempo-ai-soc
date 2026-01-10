"""
DeepTempo Findings Server - MCP Server for accessing findings and embeddings.

This is a simplified file-based implementation for demonstration purposes.
Production deployments should use PostgreSQL + pgvector.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np

# Configure logging to stderr (not stdout, which is used for MCP communication)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Try to import FastMCP, fall back to basic implementation if not available
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("deeptempo-findings")
    USE_FASTMCP = True
except ImportError:
    USE_FASTMCP = False
    logger.warning("FastMCP not available, using standalone mode")


# Data paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
FINDINGS_FILE = DATA_DIR / "findings.json"


def load_findings() -> list[dict]:
    """Load findings from JSON file."""
    if not FINDINGS_FILE.exists():
        logger.warning(f"Findings file not found: {FINDINGS_FILE}")
        return []
    
    with open(FINDINGS_FILE, 'r') as f:
        data = json.load(f)
    
    return data.get("findings", [])


def save_findings(findings: list[dict]) -> None:
    """Save findings to JSON file."""
    FINDINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FINDINGS_FILE, 'w') as f:
        json.dump({"findings": findings}, f, indent=2)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def get_finding_by_id(finding_id: str) -> Optional[dict]:
    """Get a single finding by ID."""
    findings = load_findings()
    for finding in findings:
        if finding.get("finding_id") == finding_id:
            return finding
    return None


def filter_findings(
    findings: list[dict],
    data_source: Optional[str] = None,
    time_range: Optional[dict] = None,
    min_anomaly_score: Optional[float] = None,
    techniques: Optional[list[str]] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None
) -> list[dict]:
    """Filter findings based on criteria."""
    filtered = findings
    
    if data_source:
        filtered = [f for f in filtered if f.get("data_source") == data_source]
    
    if time_range:
        start = time_range.get("start")
        end = time_range.get("end")
        if start:
            filtered = [f for f in filtered if f.get("timestamp", "") >= start]
        if end:
            filtered = [f for f in filtered if f.get("timestamp", "") <= end]
    
    if min_anomaly_score is not None:
        filtered = [f for f in filtered if f.get("anomaly_score", 0) >= min_anomaly_score]
    
    if techniques:
        def has_technique(finding):
            preds = finding.get("mitre_predictions", {})
            return any(t in preds for t in techniques)
        filtered = [f for f in filtered if has_technique(f)]
    
    if status:
        filtered = [f for f in filtered if f.get("status") == status]
    
    if severity:
        filtered = [f for f in filtered if f.get("severity") == severity]
    
    return filtered


# MCP Tool Implementations

if USE_FASTMCP:
    @mcp.tool()
    def get_finding(finding_id: str) -> dict:
        """
        Retrieve a single finding by ID.
        
        Args:
            finding_id: Unique identifier of the finding
        
        Returns:
            The finding object or error if not found
        """
        finding = get_finding_by_id(finding_id)
        if finding:
            return {"finding": finding}
        return {"error": {"code": "NOT_FOUND", "message": f"Finding '{finding_id}' not found"}}

    @mcp.tool()
    def nearest_neighbors(
        query: str,
        k: int = 10,
        filters: Optional[dict] = None
    ) -> dict:
        """
        Find findings with similar embeddings.
        
        Args:
            query: Finding ID or embedding vector (as JSON string)
            k: Number of neighbors to return (default: 10)
            filters: Optional filters (data_source, time_range, min_anomaly_score, techniques)
        
        Returns:
            List of similar findings with similarity scores
        """
        findings = load_findings()
        
        # Get query embedding
        if query.startswith("["):
            # Query is an embedding vector
            query_embedding = np.array(json.loads(query))
            query_finding_id = None
        else:
            # Query is a finding ID
            query_finding = get_finding_by_id(query)
            if not query_finding:
                return {"error": {"code": "NOT_FOUND", "message": f"Finding '{query}' not found"}}
            query_embedding = np.array(query_finding.get("embedding", []))
            query_finding_id = query
        
        if len(query_embedding) == 0:
            return {"error": {"code": "INVALID_PARAMETER", "message": "No embedding found"}}
        
        # Apply filters
        if filters:
            findings = filter_findings(
                findings,
                data_source=filters.get("data_source"),
                time_range=filters.get("time_range"),
                min_anomaly_score=filters.get("min_anomaly_score"),
                techniques=filters.get("techniques")
            )
        
        # Calculate similarities
        results = []
        for finding in findings:
            # Skip the query finding itself
            if finding.get("finding_id") == query_finding_id:
                continue
            
            embedding = finding.get("embedding", [])
            if len(embedding) == 0:
                continue
            
            similarity = cosine_similarity(query_embedding, np.array(embedding))
            results.append({
                "finding": finding,
                "similarity_score": round(similarity, 4)
            })
        
        # Sort by similarity and take top k
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        results = results[:k]
        
        return {
            "neighbors": results,
            "query_finding_id": query_finding_id,
            "total_searched": len(findings)
        }

    @mcp.tool()
    def technique_rollup(
        time_window: dict,
        scope: Optional[dict] = None,
        min_confidence: float = 0.5
    ) -> dict:
        """
        Aggregate MITRE ATT&CK techniques over a time window.
        
        Args:
            time_window: Object with 'start' and 'end' ISO timestamps
            scope: Optional scope filters (src_ips, dst_ips, hostnames, data_sources)
            min_confidence: Minimum confidence threshold (default: 0.5)
        
        Returns:
            Aggregated technique statistics
        """
        findings = load_findings()
        
        # Apply time filter
        findings = filter_findings(findings, time_range=time_window)
        
        # Apply scope filters
        if scope:
            if scope.get("data_sources"):
                findings = [f for f in findings if f.get("data_source") in scope["data_sources"]]
            if scope.get("src_ips"):
                findings = [f for f in findings if f.get("entity_context", {}).get("src_ip") in scope["src_ips"]]
            if scope.get("dst_ips"):
                findings = [f for f in findings if f.get("entity_context", {}).get("dst_ip") in scope["dst_ips"]]
            if scope.get("hostnames"):
                findings = [f for f in findings if f.get("entity_context", {}).get("hostname") in scope["hostnames"]]
        
        # Aggregate techniques
        technique_data = {}
        for finding in findings:
            for technique_id, confidence in finding.get("mitre_predictions", {}).items():
                if confidence < min_confidence:
                    continue
                
                if technique_id not in technique_data:
                    technique_data[technique_id] = {
                        "finding_count": 0,
                        "confidences": [],
                        "finding_ids": []
                    }
                
                technique_data[technique_id]["finding_count"] += 1
                technique_data[technique_id]["confidences"].append(confidence)
                technique_data[technique_id]["finding_ids"].append(finding.get("finding_id"))
        
        # Build result
        techniques = []
        for technique_id, data in technique_data.items():
            techniques.append({
                "technique_id": technique_id,
                "finding_count": data["finding_count"],
                "avg_confidence": round(sum(data["confidences"]) / len(data["confidences"]), 3),
                "max_confidence": round(max(data["confidences"]), 3),
                "finding_ids": data["finding_ids"][:10]  # Limit to first 10
            })
        
        # Sort by finding count
        techniques.sort(key=lambda x: x["finding_count"], reverse=True)
        
        return {
            "techniques": techniques,
            "time_window": time_window,
            "total_findings": len(findings),
            "total_techniques": len(techniques)
        }

    @mcp.tool()
    def cluster_summary(cluster_id: str) -> dict:
        """
        Get summary information about a behavior cluster.
        
        Args:
            cluster_id: Cluster identifier
        
        Returns:
            Cluster summary with statistics
        """
        findings = load_findings()
        
        # Find findings in this cluster
        cluster_findings = [f for f in findings if f.get("cluster_id") == cluster_id]
        
        if not cluster_findings:
            return {"error": {"code": "NOT_FOUND", "message": f"Cluster '{cluster_id}' not found"}}
        
        # Aggregate data
        entities = {
            "src_ips": set(),
            "dst_ips": set(),
            "hostnames": set()
        }
        technique_scores = {}
        timestamps = []
        
        for finding in cluster_findings:
            ctx = finding.get("entity_context", {})
            if ctx.get("src_ip"):
                entities["src_ips"].add(ctx["src_ip"])
            if ctx.get("dst_ip"):
                entities["dst_ips"].add(ctx["dst_ip"])
            if ctx.get("hostname"):
                entities["hostnames"].add(ctx["hostname"])
            
            for tech, score in finding.get("mitre_predictions", {}).items():
                if tech not in technique_scores:
                    technique_scores[tech] = []
                technique_scores[tech].append(score)
            
            if finding.get("timestamp"):
                timestamps.append(finding["timestamp"])
        
        # Calculate top techniques
        top_techniques = {}
        for tech, scores in technique_scores.items():
            top_techniques[tech] = round(sum(scores) / len(scores), 3)
        top_techniques = dict(sorted(top_techniques.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return {
            "cluster": {
                "cluster_id": cluster_id,
                "finding_count": len(cluster_findings),
                "top_techniques": top_techniques,
                "entities": {
                    "src_ips": list(entities["src_ips"]),
                    "dst_ips": list(entities["dst_ips"]),
                    "hostnames": list(entities["hostnames"])
                },
                "time_range": {
                    "start": min(timestamps) if timestamps else None,
                    "end": max(timestamps) if timestamps else None
                }
            }
        }

    @mcp.tool()
    def list_findings(
        filters: Optional[dict] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "timestamp",
        sort_order: str = "desc"
    ) -> dict:
        """
        List findings with optional filtering and pagination.
        
        Args:
            filters: Optional filters (data_source, severity, status, time_range)
            limit: Maximum number of results (default: 50, max: 100)
            offset: Number of results to skip (default: 0)
            sort_by: Field to sort by (timestamp, anomaly_score, severity)
            sort_order: Sort order (asc, desc)
        
        Returns:
            List of findings with pagination info
        """
        findings = load_findings()
        
        # Apply filters
        if filters:
            findings = filter_findings(
                findings,
                data_source=filters.get("data_source"),
                time_range=filters.get("time_range"),
                status=filters.get("status"),
                severity=filters.get("severity")
            )
        
        total = len(findings)
        
        # Sort
        reverse = sort_order == "desc"
        if sort_by == "anomaly_score":
            findings.sort(key=lambda x: x.get("anomaly_score", 0), reverse=reverse)
        elif sort_by == "severity":
            severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            findings.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 0), reverse=reverse)
        else:  # timestamp
            findings.sort(key=lambda x: x.get("timestamp", ""), reverse=reverse)
        
        # Paginate
        limit = min(limit, 100)
        findings = findings[offset:offset + limit]
        
        return {
            "findings": findings,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    @mcp.tool()
    def export_attack_layer(
        time_window: dict,
        scope: Optional[dict] = None,
        layer_name: str = "DeepTempo Findings"
    ) -> dict:
        """
        Generate an ATT&CK Navigator layer JSON.
        
        Args:
            time_window: Object with 'start' and 'end' ISO timestamps
            scope: Optional scope filters
            layer_name: Name for the layer (default: "DeepTempo Findings")
        
        Returns:
            ATT&CK Navigator layer JSON
        """
        # Get technique rollup
        rollup = technique_rollup(time_window, scope, min_confidence=0.3)
        
        if "error" in rollup:
            return rollup
        
        # Build techniques list
        techniques = []
        for tech in rollup.get("techniques", []):
            # Calculate score (0-100)
            volume_factor = min(1.0, tech["finding_count"] / 10)
            confidence_factor = tech["avg_confidence"]
            score = int((volume_factor * 0.4 + confidence_factor * 0.6) * 100)
            
            techniques.append({
                "techniqueID": tech["technique_id"],
                "score": score,
                "comment": f"{tech['finding_count']} findings, avg confidence {tech['avg_confidence']}",
                "enabled": True,
                "metadata": [
                    {"name": "finding_count", "value": str(tech["finding_count"])},
                    {"name": "avg_confidence", "value": str(tech["avg_confidence"])},
                    {"name": "max_confidence", "value": str(tech["max_confidence"])}
                ],
                "showSubtechniques": True
            })
        
        # Build layer
        layer = {
            "name": layer_name,
            "versions": {
                "attack": "14",
                "navigator": "4.9.1",
                "layer": "4.5"
            },
            "domain": "enterprise-attack",
            "description": f"MITRE ATT&CK techniques detected by DeepTempo LogLM from {time_window.get('start', 'N/A')} to {time_window.get('end', 'N/A')}",
            "filters": {
                "platforms": ["Windows", "Linux", "macOS", "Network"]
            },
            "sorting": 3,
            "layout": {
                "layout": "side",
                "showID": True,
                "showName": True
            },
            "hideDisabled": False,
            "techniques": techniques,
            "gradient": {
                "colors": ["#ffffff", "#66b3ff", "#ff6666"],
                "minValue": 0,
                "maxValue": 100
            },
            "metadata": [
                {"name": "generated_by", "value": "DeepTempo AI SOC"},
                {"name": "generation_time", "value": datetime.utcnow().isoformat() + "Z"},
                {"name": "time_range_start", "value": time_window.get("start", "N/A")},
                {"name": "time_range_end", "value": time_window.get("end", "N/A")},
                {"name": "total_findings", "value": str(rollup.get("total_findings", 0))},
                {"name": "total_techniques", "value": str(rollup.get("total_techniques", 0))}
            ]
        }
        
        return {"layer": layer}


def main():
    """Run the MCP server."""
    if USE_FASTMCP:
        logger.info("Starting DeepTempo Findings Server (FastMCP)")
        mcp.run(transport="stdio")
    else:
        logger.error("FastMCP not available. Install with: pip install 'mcp[cli]'")
        print("To use this server, install the MCP SDK:")
        print("  pip install 'mcp[cli]'")


if __name__ == "__main__":
    main()
