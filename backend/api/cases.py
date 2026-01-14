"""Cases API endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

from services.database_data_service import DatabaseDataService
from services.report_service import ReportService, REPORTLAB_AVAILABLE

router = APIRouter()
# Use DatabaseDataService which automatically uses PostgreSQL if available, falls back to JSON
data_service = DatabaseDataService()
if REPORTLAB_AVAILABLE:
    report_service = ReportService()
else:
    report_service = None


class CaseCreate(BaseModel):
    """Case creation request."""
    title: str
    description: str = ""
    finding_ids: List[str]
    priority: str = "medium"
    status: str = "open"


class CaseUpdate(BaseModel):
    """Case update request."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    assignee: Optional[str] = None


class ActivityAdd(BaseModel):
    """Add activity to case."""
    activity_type: str  # e.g., "note", "status_change", "finding_added", "action_taken"
    description: str
    details: Optional[Dict[str, Any]] = None


class ResolutionStepAdd(BaseModel):
    """Add resolution step to case."""
    description: str
    action_taken: str
    result: Optional[str] = None


@router.get("/")
async def get_cases(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    force_refresh: bool = False
):
    """
    Get all cases with optional filters.
    
    Args:
        status: Filter by status
        priority: Filter by priority
        force_refresh: Force refresh from disk
    
    Returns:
        List of cases
    """
    cases = data_service.get_cases(force_refresh=force_refresh)
    
    # Apply filters
    if status:
        cases = [c for c in cases if c.get('status') == status]
    if priority:
        cases = [c for c in cases if c.get('priority') == priority]
    
    return {"cases": cases, "total": len(cases)}


@router.get("/{case_id}")
async def get_case(case_id: str):
    """
    Get a specific case by ID.
    
    Args:
        case_id: The case ID
    
    Returns:
        Case details
    """
    case = data_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/")
async def create_case(case_data: CaseCreate):
    """
    Create a new case.
    
    Args:
        case_data: Case creation data
    
    Returns:
        Created case
    """
    case = data_service.create_case(
        title=case_data.title,
        finding_ids=case_data.finding_ids,
        priority=case_data.priority,
        description=case_data.description,
        status=case_data.status
    )
    
    if not case:
        raise HTTPException(status_code=500, detail="Failed to create case")
    
    return case


@router.patch("/{case_id}")
async def update_case(case_id: str, case_data: CaseUpdate):
    """
    Update an existing case.
    
    Args:
        case_id: The case ID
        case_data: Case update data
    
    Returns:
        Success status
    """
    # Build updates dict
    updates = {}
    if case_data.title is not None:
        updates['title'] = case_data.title
    if case_data.description is not None:
        updates['description'] = case_data.description
    if case_data.status is not None:
        updates['status'] = case_data.status
    if case_data.priority is not None:
        updates['priority'] = case_data.priority
    if case_data.notes is not None:
        updates['notes'] = case_data.notes
    
    success = data_service.update_case(case_id, **updates)
    
    if not success:
        raise HTTPException(status_code=404, detail="Case not found or update failed")
    
    return {"success": True}


@router.post("/{case_id}/activities")
async def add_case_activity(case_id: str, activity: ActivityAdd):
    """
    Add an activity/action to a case.
    
    Args:
        case_id: The case ID
        activity: Activity data
    
    Returns:
        Updated case
    """
    case = data_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Get or initialize activities list
    activities = case.get('activities', [])
    
    # Add new activity
    new_activity = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'activity_type': activity.activity_type,
        'description': activity.description,
        'details': activity.details or {}
    }
    activities.append(new_activity)
    
    # Update case
    success = data_service.update_case(case_id, activities=activities)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add activity")
    
    return data_service.get_case(case_id)


@router.post("/{case_id}/resolution-steps")
async def add_resolution_step(case_id: str, step: ResolutionStepAdd):
    """
    Add a resolution step to a case.
    
    Args:
        case_id: The case ID
        step: Resolution step data
    
    Returns:
        Updated case
    """
    case = data_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Get or initialize resolution steps list
    resolution_steps = case.get('resolution_steps', [])
    
    # Add new step
    new_step = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'description': step.description,
        'action_taken': step.action_taken,
        'result': step.result
    }
    resolution_steps.append(new_step)
    
    # Update case
    success = data_service.update_case(case_id, resolution_steps=resolution_steps)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add resolution step")
    
    return data_service.get_case(case_id)


@router.post("/{case_id}/findings/{finding_id}")
async def add_finding_to_case(case_id: str, finding_id: str):
    """
    Add a finding to a case.
    
    Args:
        case_id: The case ID
        finding_id: The finding ID to add
    
    Returns:
        Updated case
    """
    case = data_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    finding_ids = case.get('finding_ids', [])
    if finding_id not in finding_ids:
        finding_ids.append(finding_id)
        success = data_service.update_case(case_id, finding_ids=finding_ids)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add finding")
    
    return data_service.get_case(case_id)


@router.delete("/{case_id}/findings/{finding_id}")
async def remove_finding_from_case(case_id: str, finding_id: str):
    """
    Remove a finding from a case.
    
    Args:
        case_id: The case ID
        finding_id: The finding ID to remove
    
    Returns:
        Updated case
    """
    case = data_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    finding_ids = case.get('finding_ids', [])
    if finding_id in finding_ids:
        finding_ids.remove(finding_id)
        success = data_service.update_case(case_id, finding_ids=finding_ids)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove finding")
    
    return data_service.get_case(case_id)


@router.post("/{case_id}/generate-report")
async def generate_case_report(case_id: str):
    """
    Generate a PDF report for a case.
    
    Args:
        case_id: The case ID
    
    Returns:
        Report file information
    """
    if not report_service:
        raise HTTPException(
            status_code=501,
            detail="Report generation requires reportlab. Install with: pip install reportlab"
        )
    
    case = data_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Get associated findings
    finding_ids = case.get('finding_ids', [])
    findings = [data_service.get_finding(fid) for fid in finding_ids]
    findings = [f for f in findings if f]  # Filter out None values
    
    # Generate report filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{case_id}_report_{timestamp}.pdf"
    output_path = Path("TestOutputs") / filename
    output_path.parent.mkdir(exist_ok=True)
    
    # Generate the report
    success = report_service.generate_case_report(output_path, case, findings)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to generate report")
    
    return {
        "success": True,
        "filename": filename,
        "path": str(output_path),
        "case_id": case_id
    }


@router.delete("/{case_id}")
async def delete_case(case_id: str):
    """
    Delete a case.
    
    Args:
        case_id: The case ID
    
    Returns:
        Success status
    """
    case = data_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    success = data_service.delete_case(case_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete case")
    
    return {"success": True}


@router.get("/stats/summary")
async def get_cases_summary():
    """
    Get summary statistics for cases.
    
    Returns:
        Summary statistics
    """
    cases = data_service.get_cases()
    
    # Calculate statistics
    status_counts = {}
    priority_counts = {}
    total_count = len(cases)
    
    for case in cases:
        status = case.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        priority = case.get('priority', 'unknown')
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    return {
        "total": total_count,
        "by_status": status_counts,
        "by_priority": priority_counts
    }

