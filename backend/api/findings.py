"""Findings API endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import logging

from services.database_data_service import DatabaseDataService

router = APIRouter()
logger = logging.getLogger(__name__)
# Use DatabaseDataService which automatically uses PostgreSQL if available, falls back to JSON
data_service = DatabaseDataService()


class FindingFilter(BaseModel):
    """Filter parameters for findings."""
    severity: Optional[str] = None
    data_source: Optional[str] = None
    cluster_id: Optional[int] = None
    min_anomaly_score: Optional[float] = None
    limit: Optional[int] = 100


@router.get("/")
async def get_findings(
    severity: Optional[str] = Query(None),
    data_source: Optional[str] = Query(None),
    cluster_id: Optional[int] = Query(None),
    min_anomaly_score: Optional[float] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    force_refresh: bool = Query(False)
):
    """
    Get all findings with optional filters.
    
    Args:
        severity: Filter by severity (critical, high, medium, low)
        data_source: Filter by data source
        cluster_id: Filter by cluster ID
        min_anomaly_score: Filter by minimum anomaly score
        limit: Maximum number of results
        force_refresh: Force refresh from disk
    
    Returns:
        List of findings
    """
    findings = data_service.get_findings(force_refresh=force_refresh)
    
    # Apply filters
    if severity:
        findings = [f for f in findings if f.get('severity') == severity]
    if data_source:
        findings = [f for f in findings if f.get('data_source') == data_source]
    if cluster_id is not None:
        findings = [f for f in findings if f.get('cluster_id') == cluster_id]
    if min_anomaly_score is not None:
        findings = [f for f in findings if f.get('anomaly_score', 0) >= min_anomaly_score]
    
    # Apply limit
    findings = findings[:limit]
    
    return {"findings": findings, "total": len(findings)}


@router.get("/{finding_id}")
async def get_finding(finding_id: str):
    """
    Get a specific finding by ID.
    
    Args:
        finding_id: The finding ID
    
    Returns:
        Finding details
    """
    finding = data_service.get_finding(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.get("/stats/summary")
async def get_findings_summary():
    """
    Get summary statistics for findings.
    
    Returns:
        Summary statistics
    """
    findings = data_service.get_findings()
    
    # Calculate statistics
    severity_counts = {}
    data_source_counts = {}
    total_count = len(findings)
    
    for finding in findings:
        severity = finding.get('severity', 'unknown')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        data_source = finding.get('data_source', 'unknown')
        data_source_counts[data_source] = data_source_counts.get(data_source, 0) + 1
    
    return {
        "total": total_count,
        "by_severity": severity_counts,
        "by_data_source": data_source_counts
    }


@router.post("/export")
async def export_findings(output_format: str = "json"):
    """
    Export findings to a file.
    
    Args:
        output_format: Export format (json or jsonl)
    
    Returns:
        Export result
    """
    from pathlib import Path
    from datetime import datetime
    
    output_dir = Path.home() / ".deeptempo" / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"findings_export_{timestamp}.{output_format}"
    
    success = data_service.export_findings(output_path, format=output_format)
    
    if success:
        return {"success": True, "file_path": str(output_path)}
    else:
        raise HTTPException(status_code=500, detail="Export failed")


class FindingUpdate(BaseModel):
    """Schema for updating a finding."""
    mitre_predictions: Optional[Dict[str, float]] = None
    predicted_techniques: Optional[List[Dict[str, Any]]] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    anomaly_score: Optional[float] = None
    entity_context: Optional[Dict[str, Any]] = None
    cluster_id: Optional[str] = None
    evidence_links: Optional[List[str]] = None


class BulkEnrichmentRequest(BaseModel):
    """Schema for bulk enrichment request."""
    finding_ids: List[str]
    enrichment_data: Dict[str, FindingUpdate]


@router.patch("/{finding_id}")
async def update_finding(finding_id: str, update: FindingUpdate):
    """
    Update/enrich an existing finding.
    
    This endpoint allows you to add or update information on a finding,
    including MITRE ATT&CK technique mappings, severity, and other metadata.
    
    Args:
        finding_id: The finding ID to update
        update: Fields to update
    
    Returns:
        Updated finding
    
    Example:
        PATCH /api/findings/f-20260114-abc123
        {
            "mitre_predictions": {"T1071.001": 0.85, "T1048.003": 0.72},
            "predicted_techniques": [
                {"technique_id": "T1071.001", "confidence": 0.85},
                {"technique_id": "T1048.003", "confidence": 0.72}
            ],
            "severity": "high"
        }
    """
    # Get existing finding
    finding = data_service.get_finding(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # Prepare updates (exclude None values)
    updates = {}
    for key, value in update.model_dump(exclude_none=True).items():
        updates[key] = value
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    # Update the finding
    success = data_service.update_finding(finding_id, **updates)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update finding")
    
    # Return updated finding
    updated_finding = data_service.get_finding(finding_id)
    logger.info(f"Updated finding {finding_id} with {len(updates)} fields")
    
    return {
        "success": True,
        "finding": updated_finding,
        "updated_fields": list(updates.keys())
    }


@router.post("/bulk-enrich")
async def bulk_enrich_findings(request: BulkEnrichmentRequest):
    """
    Bulk enrich multiple findings with MITRE ATT&CK and other data.
    
    This endpoint allows you to enrich multiple findings at once,
    useful for batch processing or adding threat intelligence data.
    
    Args:
        request: Bulk enrichment request with finding IDs and enrichment data
    
    Returns:
        Summary of enrichment results
    
    Example:
        POST /api/findings/bulk-enrich
        {
            "finding_ids": ["f-001", "f-002"],
            "enrichment_data": {
                "f-001": {
                    "mitre_predictions": {"T1071.001": 0.85},
                    "severity": "high"
                },
                "f-002": {
                    "mitre_predictions": {"T1059.001": 0.92},
                    "severity": "critical"
                }
            }
        }
    """
    results = {
        "total": len(request.finding_ids),
        "updated": 0,
        "failed": 0,
        "not_found": 0,
        "errors": []
    }
    
    for finding_id in request.finding_ids:
        try:
            # Check if finding exists
            finding = data_service.get_finding(finding_id)
            if not finding:
                results["not_found"] += 1
                results["errors"].append(f"{finding_id}: Not found")
                continue
            
            # Get enrichment data for this finding
            enrichment = request.enrichment_data.get(finding_id)
            if not enrichment:
                continue
            
            # Prepare updates
            updates = enrichment.model_dump(exclude_none=True)
            if not updates:
                continue
            
            # Update the finding
            success = data_service.update_finding(finding_id, **updates)
            
            if success:
                results["updated"] += 1
                logger.info(f"Enriched finding {finding_id}")
            else:
                results["failed"] += 1
                results["errors"].append(f"{finding_id}: Update failed")
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"{finding_id}: {str(e)}")
            logger.error(f"Error enriching finding {finding_id}: {e}")
    
    return {
        "success": results["updated"] > 0,
        "message": f"Updated {results['updated']} of {results['total']} findings",
        "results": results
    }

