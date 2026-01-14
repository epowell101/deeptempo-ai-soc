"""Timesketch integration API endpoints."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class SketchCreate(BaseModel):
    """Sketch creation request."""
    name: str
    description: str = ""


class TimelineExport(BaseModel):
    """Timeline export request."""
    sketch_id: Optional[str] = None
    sketch_name: Optional[str] = None
    sketch_description: Optional[str] = ""
    finding_ids: Optional[List[str]] = None
    case_id: Optional[str] = None
    timeline_name: str


@router.get("/status")
async def get_timesketch_status():
    """
    Get Timesketch server status.
    
    Returns:
        Server status
    """
    try:
        from backend.api.timesketch_helper import load_timesketch_service_from_integrations
        
        # Load service from integrations config
        service = load_timesketch_service_from_integrations()
        
        if not service:
            return {"configured": False, "connected": False}
        
        success, message = service.test_connection()
        
        return {
            "configured": True,
            "connected": success,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error checking Timesketch status: {e}")
        return {
            "configured": False,
            "connected": False,
            "error": str(e)
        }


@router.get("/sketches")
async def list_sketches():
    """
    List all Timesketch sketches.
    
    Returns:
        List of sketches
    """
    try:
        from backend.api.timesketch_helper import load_timesketch_service_from_integrations
        service = load_timesketch_service_from_integrations()
        
        if not service:
            raise HTTPException(status_code=503, detail="Timesketch not configured")
        
        sketches = service.list_sketches()
        return {"sketches": sketches}
    except Exception as e:
        logger.error(f"Error listing sketches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sketches")
async def create_sketch(sketch_data: SketchCreate):
    """
    Create a new Timesketch sketch.
    
    Args:
        sketch_data: Sketch creation data
    
    Returns:
        Created sketch
    """
    try:
        from backend.api.timesketch_helper import load_timesketch_service_from_integrations
        service = load_timesketch_service_from_integrations()
        
        if not service:
            raise HTTPException(status_code=503, detail="Timesketch not configured")
        
        sketch = service.create_sketch(
            name=sketch_data.name,
            description=sketch_data.description
        )
        
        if not sketch:
            raise HTTPException(status_code=500, detail="Failed to create sketch")
        
        return sketch
    except Exception as e:
        logger.error(f"Error creating sketch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sketches/{sketch_id}")
async def get_sketch(sketch_id: int):
    """
    Get a specific sketch.
    
    Args:
        sketch_id: Sketch ID
    
    Returns:
        Sketch details
    """
    try:
        from backend.api.timesketch_helper import load_timesketch_service_from_integrations
        service = load_timesketch_service_from_integrations()
        
        if not service:
            raise HTTPException(status_code=503, detail="Timesketch not configured")
        
        sketch = service.get_sketch(sketch_id)
        
        if not sketch:
            raise HTTPException(status_code=404, detail="Sketch not found")
        
        return sketch
    except Exception as e:
        logger.error(f"Error getting sketch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docker/status")
async def get_docker_status():
    """
    Get Timesketch Docker container status.
    
    Returns:
        Docker status
    """
    try:
        from services.timesketch_docker_service import TimesketchDockerService
        
        docker_service = TimesketchDockerService()
        
        if not docker_service.is_docker_available():
            return {
                "docker_available": False,
                "daemon_running": False,
                "container_running": False
            }
        
        daemon_running = docker_service.is_docker_daemon_running()
        container_running = docker_service.is_container_running() if daemon_running else False
        
        return {
            "docker_available": True,
            "daemon_running": daemon_running,
            "container_running": container_running
        }
    except Exception as e:
        logger.error(f"Error checking Docker status: {e}")
        return {
            "docker_available": False,
            "daemon_running": False,
            "container_running": False,
            "error": str(e)
        }


@router.post("/docker/start")
async def start_docker_container(port: int = 5000):
    """
    Start Timesketch Docker container.
    
    Args:
        port: Port to expose
    
    Returns:
        Success status
    """
    try:
        from services.timesketch_docker_service import TimesketchDockerService
        
        docker_service = TimesketchDockerService()
        
        success, message = docker_service.start_container(port=port)
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return {"success": True, "message": message}
    except Exception as e:
        logger.error(f"Error starting Docker container: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/docker/stop")
async def stop_docker_container():
    """
    Stop Timesketch Docker container.
    
    Returns:
        Success status
    """
    try:
        from services.timesketch_docker_service import TimesketchDockerService
        
        docker_service = TimesketchDockerService()
        
        success, message = docker_service.stop_container()
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return {"success": True, "message": message}
    except Exception as e:
        logger.error(f"Error stopping Docker container: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_to_timesketch(export_data: TimelineExport):
    """
    Export findings or case to Timesketch timeline.
    
    Args:
        export_data: Export configuration
    
    Returns:
        Export result with sketch and timeline IDs
    """
    try:
        from backend.api.timesketch_helper import load_timesketch_service_from_integrations
        from services.timeline_service import TimelineService
        from services.data_service import DataService
        
        # Load Timesketch service
        service = load_timesketch_service_from_integrations()
        if not service:
            raise HTTPException(status_code=503, detail="Timesketch not configured")
        
        # Load data service
        data_service = DataService()
        
        # Get or create sketch
        sketch_id = export_data.sketch_id
        if not sketch_id and export_data.sketch_name:
            sketch_id = service.create_sketch(
                name=export_data.sketch_name,
                description=export_data.sketch_description
            )
            if not sketch_id:
                raise HTTPException(status_code=500, detail="Failed to create sketch")
        elif not sketch_id:
            raise HTTPException(status_code=400, detail="Either sketch_id or sketch_name must be provided")
        
        # Prepare timeline events
        events = []
        
        # Export case with findings
        if export_data.case_id:
            case = data_service.get_case(export_data.case_id)
            if not case:
                raise HTTPException(status_code=404, detail="Case not found")
            
            # Get case findings
            finding_ids = case.get('findings', [])
            findings = [data_service.get_finding(fid) for fid in finding_ids]
            findings = [f for f in findings if f is not None]
            
            # Convert to timeline events
            events = TimelineService.case_to_timeline_events(case, findings)
        
        # Export specific findings
        elif export_data.finding_ids:
            findings = [data_service.get_finding(fid) for fid in export_data.finding_ids]
            findings = [f for f in findings if f is not None]
            
            if not findings:
                raise HTTPException(status_code=404, detail="No findings found")
            
            # Convert to timeline events
            events = TimelineService.findings_to_timeline_events(findings)
        
        else:
            raise HTTPException(status_code=400, detail="Either case_id or finding_ids must be provided")
        
        if not events:
            raise HTTPException(status_code=400, detail="No events to export")
        
        # Add timeline to sketch
        timeline_id = service.add_timeline(
            sketch_id=sketch_id,
            timeline_name=export_data.timeline_name,
            events=events
        )
        
        if not timeline_id:
            raise HTTPException(status_code=500, detail="Failed to add timeline to sketch")
        
        return {
            "success": True,
            "sketch_id": sketch_id,
            "timeline_id": timeline_id,
            "event_count": len(events)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting to Timesketch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

