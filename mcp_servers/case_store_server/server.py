"""Case Store MCP Server."""

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
    if CASES_FILE.exists():
        with open(CASES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_cases(cases):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CASES_FILE, 'w') as f:
        json.dump(cases, f, indent=2)

@mcp.tool()
def list_cases(status: str = None, priority: str = None) -> str:
    """List investigation cases."""
    cases = load_cases()
    if status:
        cases = [c for c in cases if c.get('status') == status]
    if priority:
        cases = [c for c in cases if c.get('priority') == priority]
    return json.dumps({"cases": cases}, indent=2)

@mcp.tool()
def create_case(title: str, finding_ids: list, priority: str = "medium", description: str = "") -> str:
    """Create a new investigation case."""
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
def update_case(case_id: str, status: str = None, priority: str = None, notes: str = None) -> str:
    """Update an existing case."""
    cases = load_cases()
    for c in cases:
        if c.get('case_id') == case_id:
            if status:
                c['status'] = status
            if priority:
                c['priority'] = priority
            if notes:
                c.setdefault('notes', []).append({"timestamp": datetime.now().isoformat(), "text": notes})
            c['updated_at'] = datetime.now().isoformat()
            save_cases(cases)
            return json.dumps(c, indent=2)
    return json.dumps({"error": f"Case {case_id} not found"})

if __name__ == "__main__":
    logger.info("Starting Case Store Server")
    mcp.run()
