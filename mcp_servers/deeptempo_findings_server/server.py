"""
DeepTempo Findings MCP Server

Exposes DeepTempo LogLM findings and cases to Claude via MCP protocol.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

import numpy as np
from mcp.server.fastmcp import FastMCP

# Custom JSON encoder to handle numpy types and datetime
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, datetime):
            return obj.isoformat() + 'Z'
        return super().default(obj)

def json_dumps(obj, **kwargs):
    """JSON dumps with numpy and datetime support."""
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


# ========== Case Management Tools ==========


def get_db_service():
    """Get database service instance."""
    try:
        from database.service import DatabaseService
        return DatabaseService()
    except Exception as e:
        logger.error(f"Error loading database service: {e}")
        raise


@mcp.tool()
def list_cases(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    limit: int = 50,
    **kwargs
) -> str:
    """
    List investigation cases with optional filters.
    
    Args:
        status: Filter by status (new, in_progress, resolved, closed)
        priority: Filter by priority (low, medium, high, critical)
        assignee: Filter by assignee name
        limit: Maximum number of cases to return
    
    Returns:
        JSON string with matching cases
    """
    logger.info(f"list_cases called with status={status}, priority={priority}, limit={limit}")
    
    try:
        db_service = get_db_service()
        cases = db_service.get_cases(
            status=status,
            priority=priority,
            assignee=assignee,
            limit=limit
        )
        
        results = []
        for case in cases:
            # Get finding count
            finding_ids = [f.finding_id for f in case.findings] if hasattr(case, 'findings') else []
            
            results.append({
                "case_id": case.case_id,
                "title": case.title,
                "description": case.description,
                "status": case.status,
                "priority": case.priority,
                "assignee": case.assignee,
                "tags": case.tags or [],
                "finding_count": len(finding_ids),
                "created_at": case.created_at,
                "updated_at": case.updated_at
            })
        
        return json_dumps({
            "total": len(results),
            "cases": results
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in list_cases: {e}")
        return json_dumps({"error": str(e)})


@mcp.tool()
def get_case(case_id: str, include_findings: bool = True, **kwargs) -> str:
    """
    Get detailed information about a specific case.
    
    Args:
        case_id: The case ID to retrieve
        include_findings: Include full finding details (default: True)
    
    Returns:
        JSON string with case details including findings, notes, and timeline
    """
    logger.info(f"get_case called with case_id={case_id}")
    
    try:
        db_service = get_db_service()
        case = db_service.get_case(case_id, include_findings=include_findings)
        
        if not case:
            return json_dumps({"error": f"Case {case_id} not found"})
        
        # Build response
        result = {
            "case_id": case.case_id,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "priority": case.priority,
            "assignee": case.assignee,
            "tags": case.tags or [],
            "notes": case.notes or [],
            "timeline": case.timeline or [],
            "activities": case.activities or [],
            "resolution_steps": case.resolution_steps or [],
            "mitre_techniques": case.mitre_techniques or [],
            "created_at": case.created_at,
            "updated_at": case.updated_at
        }
        
        # Add findings if requested
        if include_findings and hasattr(case, 'findings'):
            result["findings"] = []
            for finding in case.findings:
                result["findings"].append({
                    "finding_id": finding.finding_id,
                    "severity": finding.severity,
                    "data_source": finding.data_source,
                    "anomaly_score": float(finding.anomaly_score) if finding.anomaly_score else 0,
                    "timestamp": finding.timestamp,
                    "status": finding.status
                })
        else:
            result["finding_ids"] = [f.finding_id for f in case.findings] if hasattr(case, 'findings') else []
        
        return json_dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_case: {e}")
        return json_dumps({"error": str(e)})


@mcp.tool()
def create_case(
    title: str,
    finding_ids: list,
    description: str = "",
    priority: str = "medium",
    status: str = "new",
    assignee: Optional[str] = None,
    tags: Optional[list] = None,
    **kwargs
) -> str:
    """
    Create a new investigation case.
    
    Args:
        title: Case title (required)
        finding_ids: List of finding IDs to include in the case (required)
        description: Detailed case description
        priority: Case priority (low, medium, high, critical)
        status: Initial status (new, in_progress, resolved, closed)
        assignee: Person assigned to the case
        tags: List of tags for categorization
    
    Returns:
        JSON string with created case details
    """
    logger.info(f"create_case called: {title}")
    
    try:
        import uuid
        from datetime import datetime
        
        db_service = get_db_service()
        
        # Generate case ID
        case_id = f"case-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        
        # Create case
        case = db_service.create_case(
            case_id=case_id,
            title=title,
            finding_ids=finding_ids,
            description=description,
            status=status,
            priority=priority,
            assignee=assignee,
            tags=tags or []
        )
        
        if not case:
            return json_dumps({"error": "Failed to create case"})
        
        return json_dumps({
            "success": True,
            "case_id": case.case_id,
            "title": case.title,
            "status": case.status,
            "priority": case.priority,
            "finding_count": len(finding_ids),
            "created_at": case.created_at
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in create_case: {e}")
        return json_dumps({"error": str(e)})


@mcp.tool()
def update_case(
    case_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    tags: Optional[list] = None,
    add_note: Optional[str] = None,
    **kwargs
) -> str:
    """
    Update an existing case.
    
    Args:
        case_id: Case ID to update (required)
        title: New title
        description: New description
        status: New status (new, in_progress, resolved, closed)
        priority: New priority (low, medium, high, critical)
        assignee: New assignee
        tags: New tags list
        add_note: Add a note to the case
    
    Returns:
        JSON string with update status
    """
    logger.info(f"update_case called: {case_id}")
    
    try:
        db_service = get_db_service()
        
        # Get current case to preserve existing data
        case = db_service.get_case(case_id)
        if not case:
            return json_dumps({"error": f"Case {case_id} not found"})
        
        # Prepare updates
        updates = {}
        if title is not None:
            updates['title'] = title
        if description is not None:
            updates['description'] = description
        if status is not None:
            updates['status'] = status
        if priority is not None:
            updates['priority'] = priority
        if assignee is not None:
            updates['assignee'] = assignee
        if tags is not None:
            updates['tags'] = tags
        
        # Handle note addition
        if add_note:
            existing_notes = case.notes or []
            existing_notes.append({
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'note': add_note
            })
            updates['notes'] = existing_notes
        
        # Perform update
        success = db_service.update_case(case_id, **updates)
        
        if success:
            return json_dumps({
                "success": True,
                "case_id": case_id,
                "message": "Case updated successfully"
            }, indent=2)
        else:
            return json_dumps({"error": "Failed to update case"})
    except Exception as e:
        logger.error(f"Error in update_case: {e}")
        return json_dumps({"error": str(e)})


@mcp.tool()
def add_finding_to_case(case_id: str, finding_id: str, **kwargs) -> str:
    """
    Add a finding to an existing case.
    
    Args:
        case_id: Case ID (required)
        finding_id: Finding ID to add (required)
    
    Returns:
        JSON string with operation status
    """
    logger.info(f"add_finding_to_case called: {case_id} + {finding_id}")
    
    try:
        db_service = get_db_service()
        success = db_service.add_finding_to_case(case_id, finding_id)
        
        if success:
            return json_dumps({
                "success": True,
                "message": f"Added finding {finding_id} to case {case_id}"
            }, indent=2)
        else:
            return json_dumps({"error": "Failed to add finding to case"})
    except Exception as e:
        logger.error(f"Error in add_finding_to_case: {e}")
        return json_dumps({"error": str(e)})


@mcp.tool()
def remove_finding_from_case(case_id: str, finding_id: str, **kwargs) -> str:
    """
    Remove a finding from a case.
    
    Args:
        case_id: Case ID (required)
        finding_id: Finding ID to remove (required)
    
    Returns:
        JSON string with operation status
    """
    logger.info(f"remove_finding_from_case called: {case_id} - {finding_id}")
    
    try:
        db_service = get_db_service()
        success = db_service.remove_finding_from_case(case_id, finding_id)
        
        if success:
            return json_dumps({
                "success": True,
                "message": f"Removed finding {finding_id} from case {case_id}"
            }, indent=2)
        else:
            return json_dumps({"error": "Failed to remove finding from case"})
    except Exception as e:
        logger.error(f"Error in remove_finding_from_case: {e}")
        return json_dumps({"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting DeepTempo Findings & Cases Server")
    mcp.run()
