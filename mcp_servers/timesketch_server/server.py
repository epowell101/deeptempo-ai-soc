"""
Timesketch MCP Server for DeepTempo AI SOC

Provides Claude with tools to interact with Timesketch for timeline
visualization and forensic analysis of security findings.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(open('/tmp/timesketch-server.log', 'w'))]
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("timesketch")

# Data directory for findings
DATA_DIR = Path(os.environ.get("DEEPTEMPO_DATA_DIR", PROJECT_ROOT / "data"))
FINDINGS_FILE = DATA_DIR / "findings.json"
TIMESKETCH_STATE_FILE = DATA_DIR / "timesketch_state.json"

# Timesketch configuration from environment
TIMESKETCH_HOST = os.environ.get("TIMESKETCH_HOST", "http://localhost:5000")
TIMESKETCH_USER = os.environ.get("TIMESKETCH_USER", "dev")
TIMESKETCH_PASSWORD = os.environ.get("TIMESKETCH_PASSWORD", "dev")
MOCK_MODE = os.environ.get("TIMESKETCH_MOCK", "true").lower() == "true"

# Global adapter instance
_adapter = None


def get_adapter():
    """Get or create the Timesketch adapter."""
    global _adapter
    if _adapter is None:
        from adapters.timesketch_adapter import TimesketchAdapter
        _adapter = TimesketchAdapter(
            host_uri=TIMESKETCH_HOST,
            username=TIMESKETCH_USER,
            password=TIMESKETCH_PASSWORD,
            mock_mode=MOCK_MODE
        )
        _adapter.connect()
    return _adapter


def load_findings() -> list:
    """Load findings from JSON file."""
    if FINDINGS_FILE.exists():
        with open(FINDINGS_FILE, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and "findings" in data:
                return data["findings"]
            return data if isinstance(data, list) else []
    return []


def load_timesketch_state() -> dict:
    """Load Timesketch state (sketches, timelines created)."""
    if TIMESKETCH_STATE_FILE.exists():
        with open(TIMESKETCH_STATE_FILE, 'r') as f:
            return json.load(f)
    return {"sketches": [], "last_sync": None}


def save_timesketch_state(state: dict):
    """Save Timesketch state."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(TIMESKETCH_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


@mcp.tool()
def create_timesketch_sketch(name: str, description: str = "") -> str:
    """
    Create a new Timesketch sketch for investigating security findings.
    
    A sketch is a workspace in Timesketch where you can analyze timelines
    and collaborate on forensic investigations.
    
    Args:
        name: Name for the sketch (e.g., "Beaconing Investigation 2026-01-10")
        description: Optional description of the investigation
    
    Returns:
        JSON with sketch details including ID and URL
    """
    try:
        adapter = get_adapter()
        result = adapter.create_sketch(name, description)
        
        if result:
            # Save to state
            state = load_timesketch_state()
            state["sketches"].append(result)
            save_timesketch_state(state)
            
            return json.dumps({
                "success": True,
                "sketch": result,
                "message": f"Created sketch '{name}'. View at: {result['url']}"
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": "Failed to create sketch"
            })
    except Exception as e:
        logger.error(f"Error creating sketch: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_timesketch_sketches() -> str:
    """
    List all available Timesketch sketches.
    
    Returns:
        JSON array of sketches with their IDs, names, and URLs
    """
    try:
        adapter = get_adapter()
        sketches = adapter.list_sketches()
        
        return json.dumps({
            "total": len(sketches),
            "sketches": sketches
        }, indent=2)
    except Exception as e:
        logger.error(f"Error listing sketches: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def upload_findings_to_timesketch(
    sketch_id: int,
    timeline_name: str = "DeepTempo Findings",
    severity_filter: Optional[str] = None,
    cluster_filter: Optional[str] = None
) -> str:
    """
    Upload DeepTempo LogLM findings to a Timesketch sketch as a timeline.
    
    This converts security findings into timeline events that can be
    visualized and analyzed in Timesketch.
    
    Args:
        sketch_id: ID of the target sketch
        timeline_name: Name for the timeline (default: "DeepTempo Findings")
        severity_filter: Optional filter by severity (critical, high, medium, low)
        cluster_filter: Optional filter by cluster ID
    
    Returns:
        JSON with upload results including event count and timeline URL
    """
    try:
        adapter = get_adapter()
        findings = load_findings()
        
        # Apply filters
        if severity_filter:
            findings = [f for f in findings if f.get("severity") == severity_filter]
        if cluster_filter:
            findings = [f for f in findings if f.get("cluster_id") == cluster_filter]
        
        if not findings:
            return json.dumps({
                "success": False,
                "error": "No findings match the specified filters"
            })
        
        result = adapter.upload_findings_as_timeline(sketch_id, findings, timeline_name)
        
        if result:
            timeline_url = adapter.get_timeline_url(sketch_id)
            return json.dumps({
                "success": True,
                "timeline": result,
                "event_count": result.get("event_count", len(findings)),
                "url": timeline_url,
                "message": f"Uploaded {len(findings)} findings to timeline '{timeline_name}'. View at: {timeline_url}"
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": "Failed to upload findings"
            })
    except Exception as e:
        logger.error(f"Error uploading findings: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def search_timesketch(
    sketch_id: int,
    query: str,
    max_results: int = 50
) -> str:
    """
    Search for events in a Timesketch sketch.
    
    Use this to find specific events, filter by MITRE techniques,
    or search for activity related to specific hosts or users.
    
    Args:
        sketch_id: ID of the sketch to search
        query: Search query (e.g., "T1071" for technique, "workstation-042" for host)
        max_results: Maximum number of results (default: 50)
    
    Returns:
        JSON array of matching events
    """
    try:
        adapter = get_adapter()
        results = adapter.search_events(sketch_id, query, max_results=max_results)
        
        return json.dumps({
            "query": query,
            "total": len(results),
            "events": results
        }, indent=2)
    except Exception as e:
        logger.error(f"Error searching: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_timesketch_url(sketch_id: int) -> str:
    """
    Get the URL to view a Timesketch sketch in the web UI.
    
    Use this to provide links to the analyst for visual investigation.
    
    Args:
        sketch_id: ID of the sketch
    
    Returns:
        JSON with the sketch URL
    """
    try:
        adapter = get_adapter()
        url = adapter.get_sketch_url(sketch_id)
        timeline_url = adapter.get_timeline_url(sketch_id)
        
        return json.dumps({
            "sketch_url": url,
            "explore_url": timeline_url,
            "message": f"View sketch at: {url}"
        }, indent=2)
    except Exception as e:
        logger.error(f"Error getting URL: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def sync_findings_to_timesketch(
    sketch_name: str = "DeepTempo AI SOC Investigation"
) -> str:
    """
    One-click sync: Create a sketch and upload all current findings.
    
    This is a convenience function that:
    1. Creates a new sketch (or uses existing)
    2. Uploads all DeepTempo findings as a timeline
    3. Returns the URL for immediate viewing
    
    Args:
        sketch_name: Name for the sketch
    
    Returns:
        JSON with sketch and timeline details, plus URL
    """
    try:
        adapter = get_adapter()
        findings = load_findings()
        
        if not findings:
            return json.dumps({
                "success": False,
                "error": "No findings available. Run demo.py first to generate sample data."
            })
        
        # Create sketch
        sketch = adapter.create_sketch(
            name=sketch_name,
            description=f"Auto-synced from DeepTempo AI SOC on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        if not sketch:
            return json.dumps({
                "success": False,
                "error": "Failed to create sketch"
            })
        
        # Upload findings
        timeline = adapter.upload_findings_as_timeline(
            sketch["id"],
            findings,
            f"DeepTempo Findings ({len(findings)} events)"
        )
        
        # Save state
        state = load_timesketch_state()
        state["sketches"].append(sketch)
        state["last_sync"] = datetime.now().isoformat()
        save_timesketch_state(state)
        
        url = adapter.get_timeline_url(sketch["id"])
        
        return json.dumps({
            "success": True,
            "sketch": sketch,
            "timeline": timeline,
            "findings_count": len(findings),
            "url": url,
            "message": f"Synced {len(findings)} findings to Timesketch. View timeline at: {url}"
        }, indent=2)
    except Exception as e:
        logger.error(f"Error syncing: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_timesketch_status() -> str:
    """
    Check Timesketch connection status and configuration.
    
    Returns:
        JSON with connection status, host, and mode (mock/live)
    """
    try:
        adapter = get_adapter()
        state = load_timesketch_state()
        
        return json.dumps({
            "connected": adapter.is_connected(),
            "host": TIMESKETCH_HOST,
            "mode": "mock" if MOCK_MODE else "live",
            "sketches_created": len(state.get("sketches", [])),
            "last_sync": state.get("last_sync"),
            "note": "Running in mock mode - no actual Timesketch server required" if MOCK_MODE else "Connected to live Timesketch server"
        }, indent=2)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting Timesketch MCP Server")
    mcp.run()
