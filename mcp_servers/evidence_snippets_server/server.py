"""
Evidence Snippets MCP Server

Provides access to raw log evidence for security findings.
"""

import json
import logging
from pathlib import Path
import os

from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(open('/tmp/evidence-snippets.log', 'w'))]
)
logger = logging.getLogger(__name__)

mcp = FastMCP("evidence-snippets")

DATA_DIR = Path(os.environ.get("DEEPTEMPO_DATA_DIR", Path(__file__).parent.parent.parent / "data"))
FINDINGS_FILE = DATA_DIR / "findings.json"


def load_findings():
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
                return []
    return []


@mcp.tool()
def get_evidence(finding_id: str, **kwargs) -> str:
    """
    Get raw log evidence for a finding.
    
    Args:
        finding_id: The finding ID to get evidence for
    
    Returns:
        JSON string with the raw log evidence
    """
    findings = load_findings()
    for f in findings:
        if f.get('finding_id') == finding_id:
            return json.dumps({
                "finding_id": finding_id,
                "raw_log": f.get('raw_log', 'No raw log available'),
                "data_source": f.get('data_source'),
                "timestamp": f.get('timestamp')
            }, indent=2)
    return json.dumps({"error": f"Finding {finding_id} not found"})


@mcp.tool()
def search_evidence(query: str, limit: int = 20, **kwargs) -> str:
    """
    Search evidence by keyword.
    
    Args:
        query: Search term to look for in raw logs
        limit: Maximum number of results to return
    
    Returns:
        JSON string with matching evidence snippets
    """
    findings = load_findings()
    matches = []
    for f in findings:
        raw_log = f.get('raw_log', '')
        if query.lower() in raw_log.lower():
            matches.append({
                "finding_id": f.get('finding_id'),
                "snippet": raw_log[:200],
                "data_source": f.get('data_source')
            })
    return json.dumps({"query": query, "matches": matches[:limit]}, indent=2)


if __name__ == "__main__":
    logger.info("Starting Evidence Snippets Server")
    mcp.run()
