"""
Case Store Server - MCP Server for investigation case management.

This server provides case management functionality for SOC investigations.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Try to import FastMCP
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("case-store")
    USE_FASTMCP = True
except ImportError:
    USE_FASTMCP = False
    logger.warning("FastMCP not available, using standalone mode")


# Data paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
CASES_FILE = DATA_DIR / "cases.json"


def load_cases() -> list[dict]:
    """Load cases from JSON file."""
    if not CASES_FILE.exists():
        return []
    with open(CASES_FILE, 'r') as f:
        data = json.load(f)
    return data.get("cases", [])


def save_cases(cases: list[dict]) -> None:
    """Save cases to JSON file."""
    CASES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CASES_FILE, 'w') as f:
        json.dump({"cases": cases}, f, indent=2, default=str)


def get_case_by_id(case_id: str) -> Optional[dict]:
    """Get a single case by ID."""
    cases = load_cases()
    for case in cases:
        if case.get("case_id") == case_id:
            return case
    return None


def generate_case_id() -> str:
    """Generate a unique case ID."""
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    short_uuid = str(uuid.uuid4())[:8]
    return f"case-{date_str}-{short_uuid}"


if USE_FASTMCP:
    @mcp.tool()
    def create_case(
        title: str,
        finding_ids: list[str],
        description: str = "",
        priority: str = "medium",
        assignee: str = "",
        tags: Optional[list[str]] = None
    ) -> dict:
        """
        Create a new investigation case.
        
        Args:
            title: Case title
            finding_ids: List of finding IDs to include in the case
            description: Case description (optional)
            priority: Priority level - low, medium, high, critical (default: medium)
            assignee: Assigned analyst (optional)
            tags: List of tags (optional)
        
        Returns:
            The created case object
        """
        # Validate priority
        valid_priorities = ["low", "medium", "high", "critical"]
        if priority not in valid_priorities:
            priority = "medium"
        
        # Create case
        now = datetime.utcnow().isoformat() + "Z"
        case = {
            "case_id": generate_case_id(),
            "title": title,
            "description": description,
            "finding_ids": finding_ids,
            "status": "new",
            "priority": priority,
            "assignee": assignee,
            "tags": tags or [],
            "notes": [],
            "timeline": [
                {
                    "timestamp": now,
                    "event": "Case created"
                }
            ],
            "created_at": now,
            "updated_at": now
        }
        
        # Save
        cases = load_cases()
        cases.append(case)
        save_cases(cases)
        
        logger.info(f"Created case: {case['case_id']}")
        
        return {"case": case}

    @mcp.tool()
    def update_case(case_id: str, updates: dict) -> dict:
        """
        Update an existing case.
        
        Args:
            case_id: ID of the case to update
            updates: Object with fields to update:
                - status: new, investigating, resolved, closed, false_positive
                - priority: low, medium, high, critical
                - assignee: Analyst email/name
                - add_findings: List of finding IDs to add
                - remove_findings: List of finding IDs to remove
                - add_tags: List of tags to add
                - remove_tags: List of tags to remove
        
        Returns:
            The updated case object
        """
        cases = load_cases()
        case_index = None
        
        for i, case in enumerate(cases):
            if case.get("case_id") == case_id:
                case_index = i
                break
        
        if case_index is None:
            return {"error": {"code": "NOT_FOUND", "message": f"Case '{case_id}' not found"}}
        
        case = cases[case_index]
        now = datetime.utcnow().isoformat() + "Z"
        changes = []
        
        # Apply updates
        if "status" in updates:
            valid_statuses = ["new", "investigating", "resolved", "closed", "false_positive"]
            if updates["status"] in valid_statuses:
                old_status = case.get("status")
                case["status"] = updates["status"]
                changes.append(f"Status changed from {old_status} to {updates['status']}")
        
        if "priority" in updates:
            valid_priorities = ["low", "medium", "high", "critical"]
            if updates["priority"] in valid_priorities:
                old_priority = case.get("priority")
                case["priority"] = updates["priority"]
                changes.append(f"Priority changed from {old_priority} to {updates['priority']}")
        
        if "assignee" in updates:
            old_assignee = case.get("assignee", "unassigned")
            case["assignee"] = updates["assignee"]
            changes.append(f"Assignee changed from {old_assignee} to {updates['assignee']}")
        
        if "add_findings" in updates:
            for finding_id in updates["add_findings"]:
                if finding_id not in case["finding_ids"]:
                    case["finding_ids"].append(finding_id)
                    changes.append(f"Added finding {finding_id}")
        
        if "remove_findings" in updates:
            for finding_id in updates["remove_findings"]:
                if finding_id in case["finding_ids"]:
                    case["finding_ids"].remove(finding_id)
                    changes.append(f"Removed finding {finding_id}")
        
        if "add_tags" in updates:
            for tag in updates["add_tags"]:
                if tag not in case["tags"]:
                    case["tags"].append(tag)
                    changes.append(f"Added tag '{tag}'")
        
        if "remove_tags" in updates:
            for tag in updates["remove_tags"]:
                if tag in case["tags"]:
                    case["tags"].remove(tag)
                    changes.append(f"Removed tag '{tag}'")
        
        # Update timestamp and timeline
        case["updated_at"] = now
        if changes:
            case["timeline"].append({
                "timestamp": now,
                "event": "; ".join(changes)
            })
        
        # Save
        cases[case_index] = case
        save_cases(cases)
        
        logger.info(f"Updated case: {case_id} - {changes}")
        
        return {"case": case}

    @mcp.tool()
    def add_case_note(
        case_id: str,
        content: str,
        author: str = "analyst"
    ) -> dict:
        """
        Add a note to a case.
        
        Args:
            case_id: ID of the case
            content: Note content
            author: Author of the note (default: "analyst")
        
        Returns:
            The updated case object
        """
        cases = load_cases()
        case_index = None
        
        for i, case in enumerate(cases):
            if case.get("case_id") == case_id:
                case_index = i
                break
        
        if case_index is None:
            return {"error": {"code": "NOT_FOUND", "message": f"Case '{case_id}' not found"}}
        
        case = cases[case_index]
        now = datetime.utcnow().isoformat() + "Z"
        
        # Add note
        note = {
            "author": author,
            "timestamp": now,
            "content": content
        }
        case["notes"].append(note)
        case["updated_at"] = now
        
        # Add to timeline
        case["timeline"].append({
            "timestamp": now,
            "event": f"Note added by {author}"
        })
        
        # Save
        cases[case_index] = case
        save_cases(cases)
        
        logger.info(f"Added note to case: {case_id}")
        
        return {"case": case, "note": note}

    @mcp.tool()
    def get_case(case_id: str) -> dict:
        """
        Retrieve a case by ID.
        
        Args:
            case_id: ID of the case
        
        Returns:
            The case object
        """
        case = get_case_by_id(case_id)
        if case:
            return {"case": case}
        return {"error": {"code": "NOT_FOUND", "message": f"Case '{case_id}' not found"}}

    @mcp.tool()
    def list_cases(
        filters: Optional[dict] = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """
        List cases with optional filtering.
        
        Args:
            filters: Optional filters:
                - status: Filter by status
                - priority: Filter by priority
                - assignee: Filter by assignee
                - tags: Filter by tags (any match)
            limit: Maximum number of results (default: 50)
            offset: Number of results to skip (default: 0)
        
        Returns:
            List of cases with pagination info
        """
        cases = load_cases()
        
        # Apply filters
        if filters:
            if filters.get("status"):
                cases = [c for c in cases if c.get("status") == filters["status"]]
            if filters.get("priority"):
                cases = [c for c in cases if c.get("priority") == filters["priority"]]
            if filters.get("assignee"):
                cases = [c for c in cases if c.get("assignee") == filters["assignee"]]
            if filters.get("tags"):
                filter_tags = set(filters["tags"])
                cases = [c for c in cases if filter_tags & set(c.get("tags", []))]
        
        total = len(cases)
        
        # Sort by updated_at descending
        cases.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        # Paginate
        cases = cases[offset:offset + limit]
        
        return {
            "cases": cases,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    @mcp.tool()
    def case_summary() -> dict:
        """
        Get a summary of all cases.
        
        Returns:
            Summary statistics for cases
        """
        cases = load_cases()
        
        summary = {
            "total_cases": len(cases),
            "by_status": {},
            "by_priority": {},
            "recent_cases": []
        }
        
        for case in cases:
            status = case.get("status", "unknown")
            priority = case.get("priority", "unknown")
            
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            summary["by_priority"][priority] = summary["by_priority"].get(priority, 0) + 1
        
        # Get 5 most recent cases
        sorted_cases = sorted(cases, key=lambda x: x.get("updated_at", ""), reverse=True)
        for case in sorted_cases[:5]:
            summary["recent_cases"].append({
                "case_id": case.get("case_id"),
                "title": case.get("title"),
                "status": case.get("status"),
                "priority": case.get("priority"),
                "updated_at": case.get("updated_at")
            })
        
        return summary


def main():
    """Run the MCP server."""
    if USE_FASTMCP:
        logger.info("Starting Case Store Server (FastMCP)")
        mcp.run(transport="stdio")
    else:
        logger.error("FastMCP not available. Install with: pip install 'mcp[cli]'")


if __name__ == "__main__":
    main()
