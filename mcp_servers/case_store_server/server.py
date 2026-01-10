"""
Case Store MCP Server

Manages investigation cases for the AI SOC.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
import uuid
import os

from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(open('/tmp/case-store.log', 'w'))]
)
logger = logging.getLogger(__name__)

mcp = FastMCP("case-store")

DATA_DIR = Path(os.environ.get("DEEPTEMPO_DATA_DIR", Path(__file__).parent.parent.parent / "data"))
CASES_FILE = DATA_DIR / "cases.json"


def load_cases():
    """Load cases from JSON file."""
    if CASES_FILE.exists():
        with open(CASES_FILE, 'r') as f:
            data = json.load(f)
            # Handle both formats: {"cases": [...]} or [...]
            if isinstance(data, dict) and 'cases' in data:
                return data['cases']
            elif isinstance(data, list):
                return data
            else:
                return []
    return []


def save_cases(cases):
    """Save cases to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CASES_FILE, 'w') as f:
        json.dump(cases, f, indent=2)


@mcp.tool()
def list_cases(status: str = None, priority: str = None, **kwargs) -> str:
    """
    List investigation cases.
    
    Args:
        status: Filter by status (open, in_progress, closed)
        priority: Filter by priority (critical, high, medium, low)
    
    Returns:
        JSON string with matching cases
    """
    cases = load_cases()
    if status:
        cases = [c for c in cases if c.get('status') == status]
    if priority:
        cases = [c for c in cases if c.get('priority') == priority]
    return json.dumps({"total": len(cases), "cases": cases}, indent=2)


@mcp.tool()
def get_case(case_id: str, **kwargs) -> str:
    """
    Get a specific case by ID.
    
    Args:
        case_id: The case ID to retrieve
    
    Returns:
        JSON string with the case details
    """
    cases = load_cases()
    for c in cases:
        if c.get('case_id') == case_id:
            return json.dumps(c, indent=2)
    return json.dumps({"error": f"Case {case_id} not found"})


@mcp.tool()
def create_case(title: str, finding_ids: list, priority: str = "medium", description: str = "", **kwargs) -> str:
    """
    Create a new investigation case.
    
    Args:
        title: Title of the case
        finding_ids: List of finding IDs to include in the case
        priority: Priority level (critical, high, medium, low)
        description: Description of the case
    
    Returns:
        JSON string with the created case
    """
    cases = load_cases()
    case_id = f"case-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:8]}"
    new_case = {
        "case_id": case_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "open",
        "finding_ids": finding_ids,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    cases.append(new_case)
    save_cases(cases)
    return json.dumps(new_case, indent=2)


@mcp.tool()
def update_case(case_id: str, status: str = None, priority: str = None, notes: str = None, **kwargs) -> str:
    """
    Update an existing case.
    
    Args:
        case_id: The case ID to update
        status: New status (open, in_progress, closed)
        priority: New priority (critical, high, medium, low)
        notes: Notes to add to the case
    
    Returns:
        JSON string with the updated case
    """
    cases = load_cases()
    for c in cases:
        if c.get('case_id') == case_id:
            if status:
                c['status'] = status
            if priority:
                c['priority'] = priority
            if notes:
                c.setdefault('notes', []).append({
                    "timestamp": datetime.now().isoformat(),
                    "text": notes
                })
            c['updated_at'] = datetime.now().isoformat()
            save_cases(cases)
            return json.dumps(c, indent=2)
    return json.dumps({"error": f"Case {case_id} not found"})


if __name__ == "__main__":
    logger.info("Starting Case Store Server")
    mcp.run()
