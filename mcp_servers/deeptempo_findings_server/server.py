"""
DeepTempo Findings MCP Server

Exposes DeepTempo LogLM findings to Claude via MCP protocol.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

import numpy as np
from mcp.server.fastmcp import FastMCP

# Custom JSON encoder to handle numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def json_dumps(obj, **kwargs):
    """JSON dumps with numpy support."""
    return json.dumps(obj, cls=NumpyEncoder, **kwargs)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(open('/tmp/deeptempo-findings.log', 'w'))]
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("deeptempo-findings")

# Data directory
DATA_DIR = Path(os.environ.get("DEEPTEMPO_DATA_DIR", Path(__file__).parent.parent.parent / "data"))
FINDINGS_FILE = DATA_DIR / "findings.json"


def load_findings() -> list:
    """Load findings from JSON file."""
    if FINDINGS_FILE.exists():
        with open(FINDINGS_FILE, 'r') as f:
            data = json.load(f)
            # Handle both formats: {"findings": [...]} or [...]
            if isinstance(data, dict) and 'findings' in data:
                return data['findings']
            elif isinstance(data, list):
                return data
            else:
                logger.error(f"Unexpected data format: {type(data)}")
                return []
    return []


def cosine_similarity(a: list, b: list) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


@mcp.tool()
def list_findings(
    severity: Optional[str] = None,
    data_source: Optional[str] = None,
    cluster_id: Optional[str] = None,
    min_anomaly_score: Optional[float] = None,
    time_range: Optional[str] = None,
    limit: int = 50,
    **kwargs
) -> str:
    """
    List security findings from DeepTempo LogLM.
    
    Args:
        severity: Filter by severity (critical, high, medium, low)
        data_source: Filter by data source (flow, dns, waf, etc.)
        cluster_id: Filter by cluster ID
        min_anomaly_score: Minimum anomaly score (0.0-1.0)
        time_range: Time range filter (e.g., "last_24h", "last_7d")
        limit: Maximum number of findings to return
    
    Returns:
        JSON string with matching findings
    """
    logger.info(f"list_findings called with severity={severity}, data_source={data_source}, limit={limit}")
    
    try:
        findings = load_findings()
        logger.info(f"Loaded {len(findings)} findings from {FINDINGS_FILE}")
        
        if severity:
            findings = [f for f in findings if f.get('severity') == severity]
        if data_source:
            findings = [f for f in findings if f.get('data_source') == data_source]
        if cluster_id:
            findings = [f for f in findings if f.get('cluster_id') == cluster_id]
        if min_anomaly_score is not None:
            findings = [f for f in findings if f.get('anomaly_score', 0) >= min_anomaly_score]
        
        results = []
        for f in findings[:limit]:
            f_copy = {k: v for k, v in f.items() if k != 'embedding'}
            results.append(f_copy)
        
        return json_dumps({
            "total": len(findings),
            "returned": len(results),
            "findings": results
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in list_findings: {e}")
        return json_dumps({"error": str(e)})


@mcp.tool()
def get_finding(finding_id: str, **kwargs) -> str:
    """
    Get a specific finding by ID.
    
    Args:
        finding_id: The finding ID to retrieve
    
    Returns:
        JSON string with the finding details
    """
    try:
        findings = load_findings()
        
        for f in findings:
            if f.get('finding_id') == finding_id:
                f_copy = {k: v for k, v in f.items() if k != 'embedding'}
                return json_dumps(f_copy, indent=2)
        
        return json_dumps({"error": f"Finding {finding_id} not found"})
    except Exception as e:
        logger.error(f"Error in get_finding: {e}")
        return json_dumps({"error": str(e)})


@mcp.tool()
def nearest_neighbors(finding_id: str, k: int = 10, **kwargs) -> str:
    """
    Find similar findings using embedding similarity.
    
    Args:
        finding_id: The finding ID to find neighbors for
        k: Number of neighbors to return
    
    Returns:
        JSON string with similar findings and similarity scores
    """
    try:
        findings = load_findings()
        
        seed = None
        for f in findings:
            if f.get('finding_id') == finding_id:
                seed = f
                break
        
        if not seed or 'embedding' not in seed:
            return json_dumps({"error": f"Finding {finding_id} not found or has no embedding"})
        
        similarities = []
        for f in findings:
            if f.get('finding_id') != finding_id and 'embedding' in f:
                sim = cosine_similarity(seed['embedding'], f['embedding'])
                similarities.append({
                    "finding_id": f['finding_id'],
                    "similarity": round(float(sim), 4),
                    "cluster_id": f.get('cluster_id'),
                    "severity": f.get('severity'),
                    "data_source": f.get('data_source'),
                    "anomaly_score": float(f.get('anomaly_score', 0))
                })
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return json_dumps({
            "seed_finding": finding_id,
            "neighbors": similarities[:k]
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in nearest_neighbors: {e}")
        return json_dumps({"error": str(e)})


@mcp.tool()
def technique_rollup(min_confidence: float = 0.5, **kwargs) -> str:
    """
    Get MITRE ATT&CK technique statistics across all findings.
    
    Args:
        min_confidence: Minimum confidence threshold for techniques
    
    Returns:
        JSON string with technique counts and average confidence
    """
    try:
        findings = load_findings()
        
        technique_stats = {}
        for f in findings:
            for technique, confidence in f.get('mitre_predictions', {}).items():
                if confidence >= min_confidence:
                    if technique not in technique_stats:
                        technique_stats[technique] = {"count": 0, "total_confidence": 0}
                    technique_stats[technique]["count"] += 1
                    technique_stats[technique]["total_confidence"] += confidence
        
        results = []
        for technique, stats in technique_stats.items():
            results.append({
                "technique": technique,
                "count": int(stats["count"]),
                "avg_confidence": round(float(stats["total_confidence"] / stats["count"]), 3)
            })
        
        results.sort(key=lambda x: x['count'], reverse=True)
        
        return json_dumps({
            "min_confidence": min_confidence,
            "techniques": results
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in technique_rollup: {e}")
        return json_dumps({"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting DeepTempo Findings Server")
    mcp.run()
