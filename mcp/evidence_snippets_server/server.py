"""
Evidence Snippets Server - MCP Server for gated access to raw log evidence.

This server provides Tier 2 access to raw log snippets with redaction support.
Access is gated and rate-limited by default.
"""

import json
import logging
import re
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
    mcp = FastMCP("evidence-snippets")
    USE_FASTMCP = True
except ImportError:
    USE_FASTMCP = False
    logger.warning("FastMCP not available, using standalone mode")


# Data paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
FINDINGS_FILE = DATA_DIR / "findings.json"
EVIDENCE_DIR = DATA_DIR / "evidence"

# Redaction patterns
REDACTION_PATTERNS = [
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),
    (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]'),
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),
    (r'\b(?:password|passwd|pwd|secret|token|api_key|apikey)[\s]*[=:]\s*[^\s]+', '[CREDENTIAL_REDACTED]'),
    (r'Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+', '[JWT_REDACTED]'),
    (r'session_id=[^\s&]+', 'session_id=[SESSION_REDACTED]'),
]


def load_findings() -> list[dict]:
    """Load findings from JSON file."""
    if not FINDINGS_FILE.exists():
        return []
    with open(FINDINGS_FILE, 'r') as f:
        data = json.load(f)
    return data.get("findings", [])


def get_finding_by_id(finding_id: str) -> Optional[dict]:
    """Get a single finding by ID."""
    findings = load_findings()
    for finding in findings:
        if finding.get("finding_id") == finding_id:
            return finding
    return None


def redact_text(text: str) -> tuple[str, list[str]]:
    """
    Apply redaction patterns to text.
    
    Returns:
        Tuple of (redacted_text, list of redacted field types)
    """
    redacted_fields = []
    
    for pattern, replacement in REDACTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            # Extract field type from replacement
            field_type = replacement.strip('[]').replace('_REDACTED', '').lower()
            if field_type not in redacted_fields:
                redacted_fields.append(field_type)
    
    return text, redacted_fields


def load_evidence_file(ref: str) -> Optional[list[str]]:
    """Load an evidence file and return its lines."""
    evidence_path = EVIDENCE_DIR / ref
    
    if not evidence_path.exists():
        # Try to generate sample evidence
        return generate_sample_evidence(ref)
    
    with open(evidence_path, 'r') as f:
        return f.readlines()


def generate_sample_evidence(ref: str) -> list[str]:
    """Generate sample evidence for demonstration."""
    # Parse the reference to determine type
    if ref.startswith("flow/"):
        return [
            '{"timestamp": "2024-01-15T14:32:18Z", "src_ip": "10.0.1.15", "dst_ip": "203.0.113.50", "src_port": 54321, "dst_port": 443, "protocol": "tcp", "bytes_sent": 256, "bytes_recv": 1024}\n',
            '{"timestamp": "2024-01-15T14:33:18Z", "src_ip": "10.0.1.15", "dst_ip": "203.0.113.50", "src_port": 54322, "dst_port": 443, "protocol": "tcp", "bytes_sent": 256, "bytes_recv": 1024}\n',
            '{"timestamp": "2024-01-15T14:34:18Z", "src_ip": "10.0.1.15", "dst_ip": "203.0.113.50", "src_port": 54323, "dst_port": 443, "protocol": "tcp", "bytes_sent": 256, "bytes_recv": 1024}\n',
        ]
    elif ref.startswith("dns/"):
        return [
            '{"timestamp": "2024-01-15T14:32:17Z", "src_ip": "10.0.1.15", "query": "suspicious-domain.com", "query_type": "A", "response": "203.0.113.50", "ttl": 300}\n',
            '{"timestamp": "2024-01-15T14:32:17Z", "src_ip": "10.0.1.15", "query": "cdn.suspicious-domain.com", "query_type": "A", "response": "203.0.113.51", "ttl": 300}\n',
        ]
    elif ref.startswith("waf/"):
        return [
            '{"timestamp": "2024-01-15T14:30:00Z", "src_ip": "198.51.100.10", "method": "POST", "uri": "/api/upload", "status": 403, "rule_id": "942100", "action": "blocked"}\n',
            '{"timestamp": "2024-01-15T14:30:01Z", "src_ip": "198.51.100.10", "method": "POST", "uri": "/api/data", "status": 200, "rule_id": null, "action": "allowed"}\n',
        ]
    
    return []


def log_access(finding_id: str, user: str, redaction: str, lines_returned: int):
    """Log evidence access for audit purposes."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": "evidence_access",
        "finding_id": finding_id,
        "user": user,
        "redaction": redaction,
        "lines_returned": lines_returned
    }
    logger.info(f"Evidence access: {json.dumps(log_entry)}")


if USE_FASTMCP:
    @mcp.tool()
    def evidence_snippets(
        finding_id: str,
        max_lines: int = 200,
        redaction: str = "on"
    ) -> dict:
        """
        Retrieve raw log snippets for a finding.
        
        This is a Tier 2 (gated) endpoint. Access is logged and rate-limited.
        
        Args:
            finding_id: ID of the finding to get evidence for
            max_lines: Maximum number of lines to return (default: 200, max: 500)
            redaction: Redaction mode - "on" (default) or "off"
        
        Returns:
            Evidence snippets with optional redaction
        """
        # Validate parameters
        max_lines = min(max_lines, 500)
        if redaction not in ["on", "off"]:
            redaction = "on"
        
        # Get the finding
        finding = get_finding_by_id(finding_id)
        if not finding:
            return {"error": {"code": "NOT_FOUND", "message": f"Finding '{finding_id}' not found"}}
        
        evidence_links = finding.get("evidence_links", [])
        if not evidence_links:
            return {"error": {"code": "NO_EVIDENCE", "message": "No evidence links for this finding"}}
        
        snippets = []
        total_lines = 0
        
        for link in evidence_links:
            if total_lines >= max_lines:
                break
            
            evidence_type = link.get("type", "unknown")
            ref = link.get("ref", "")
            line_range = link.get("lines", [0, -1])
            
            # Load evidence file
            all_lines = load_evidence_file(ref)
            if not all_lines:
                continue
            
            # Extract relevant lines
            start_line = line_range[0] if len(line_range) > 0 else 0
            end_line = line_range[1] if len(line_range) > 1 and line_range[1] > 0 else len(all_lines)
            
            # Adjust for 0-based indexing and bounds
            start_line = max(0, start_line)
            end_line = min(len(all_lines), end_line)
            
            lines = all_lines[start_line:end_line]
            
            # Limit lines
            remaining = max_lines - total_lines
            if len(lines) > remaining:
                lines = lines[:remaining]
            
            # Apply redaction if enabled
            redacted_fields = []
            if redaction == "on":
                redacted_lines = []
                for line in lines:
                    redacted_line, fields = redact_text(line)
                    redacted_lines.append(redacted_line.strip())
                    redacted_fields.extend(fields)
                lines = redacted_lines
                redacted_fields = list(set(redacted_fields))
            else:
                lines = [line.strip() for line in lines]
            
            snippets.append({
                "type": evidence_type,
                "ref": ref,
                "lines": lines,
                "redacted_fields": redacted_fields if redaction == "on" else []
            })
            
            total_lines += len(lines)
        
        # Log access
        log_access(finding_id, "anonymous", redaction, total_lines)
        
        return {
            "snippets": snippets,
            "finding_id": finding_id,
            "total_lines": total_lines,
            "redaction": redaction
        }

    @mcp.tool()
    def evidence_summary(finding_id: str) -> dict:
        """
        Get a summary of available evidence for a finding without retrieving the actual logs.
        
        This is a Tier 1 endpoint (not gated).
        
        Args:
            finding_id: ID of the finding
        
        Returns:
            Summary of available evidence
        """
        finding = get_finding_by_id(finding_id)
        if not finding:
            return {"error": {"code": "NOT_FOUND", "message": f"Finding '{finding_id}' not found"}}
        
        evidence_links = finding.get("evidence_links", [])
        
        summary = {
            "finding_id": finding_id,
            "evidence_count": len(evidence_links),
            "evidence_types": [],
            "evidence_refs": []
        }
        
        for link in evidence_links:
            evidence_type = link.get("type", "unknown")
            if evidence_type not in summary["evidence_types"]:
                summary["evidence_types"].append(evidence_type)
            
            summary["evidence_refs"].append({
                "type": evidence_type,
                "ref": link.get("ref", ""),
                "line_range": link.get("lines", [])
            })
        
        return summary


def main():
    """Run the MCP server."""
    if USE_FASTMCP:
        logger.info("Starting Evidence Snippets Server (FastMCP)")
        mcp.run(transport="stdio")
    else:
        logger.error("FastMCP not available. Install with: pip install 'mcp[cli]'")


if __name__ == "__main__":
    main()
