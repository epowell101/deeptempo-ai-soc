"""
DeepTempo Offline Export Loader

This adapter loads DeepTempo findings from offline export files (JSON/JSONL).
It transforms the export format into the internal finding schema and stores
them in the file-based data store.

Usage:
    python -m adapters.deeptempo_offline_export.loader [export_file]
    
    If no export file is provided, sample data will be generated.
"""

import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
FINDINGS_FILE = DATA_DIR / "findings.json"

# MITRE ATT&CK techniques commonly detected in network security
MITRE_TECHNIQUES = {
    "T1071.001": {"name": "Web Protocols", "tactic": "command-and-control"},
    "T1071.004": {"name": "DNS", "tactic": "command-and-control"},
    "T1048.003": {"name": "Exfiltration Over Unencrypted Non-C2 Protocol", "tactic": "exfiltration"},
    "T1048.001": {"name": "Exfiltration Over Symmetric Encrypted Non-C2 Protocol", "tactic": "exfiltration"},
    "T1041": {"name": "Exfiltration Over C2 Channel", "tactic": "exfiltration"},
    "T1573.001": {"name": "Symmetric Cryptography", "tactic": "command-and-control"},
    "T1571": {"name": "Non-Standard Port", "tactic": "command-and-control"},
    "T1572": {"name": "Protocol Tunneling", "tactic": "command-and-control"},
    "T1046": {"name": "Network Service Discovery", "tactic": "discovery"},
    "T1018": {"name": "Remote System Discovery", "tactic": "discovery"},
    "T1059.001": {"name": "PowerShell", "tactic": "execution"},
    "T1059.003": {"name": "Windows Command Shell", "tactic": "execution"},
    "T1190": {"name": "Exploit Public-Facing Application", "tactic": "initial-access"},
    "T1133": {"name": "External Remote Services", "tactic": "initial-access"},
    "T1021.001": {"name": "Remote Desktop Protocol", "tactic": "lateral-movement"},
    "T1021.002": {"name": "SMB/Windows Admin Shares", "tactic": "lateral-movement"},
}


def generate_embedding(seed: int = None, dim: int = 768) -> list[float]:
    """
    Generate a random embedding vector.
    
    In production, these would come from DeepTempo's LogLM.
    For demonstration, we generate random vectors with some structure.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Generate base vector
    embedding = np.random.randn(dim).astype(np.float32)
    
    # Normalize to unit length
    embedding = embedding / np.linalg.norm(embedding)
    
    return embedding.tolist()


def generate_similar_embedding(base: list[float], similarity: float = 0.9) -> list[float]:
    """Generate an embedding similar to the base embedding."""
    base_arr = np.array(base)
    noise = np.random.randn(len(base)).astype(np.float32)
    noise = noise / np.linalg.norm(noise)
    
    # Interpolate between base and noise
    new_embedding = similarity * base_arr + (1 - similarity) * noise
    new_embedding = new_embedding / np.linalg.norm(new_embedding)
    
    return new_embedding.tolist()


def generate_sample_findings(count: int = 50) -> list[dict]:
    """
    Generate sample findings for demonstration.
    
    Creates a mix of:
    - C2 beaconing patterns
    - DNS anomalies
    - WAF attack attempts
    - Data exfiltration indicators
    """
    findings = []
    base_time = datetime.utcnow() - timedelta(hours=24)
    
    # Sample entities
    internal_ips = ["10.0.1.15", "10.0.1.22", "10.0.1.45", "10.0.2.10", "10.0.2.33"]
    external_ips = ["203.0.113.50", "203.0.113.100", "198.51.100.10", "198.51.100.25"]
    hostnames = ["workstation-042", "workstation-055", "server-db-01", "server-web-02", "laptop-sales-03"]
    users = ["jsmith", "agarcia", "mwilson", "tjohnson", "klee"]
    domains = ["suspicious-domain.com", "cdn-update.net", "api-service.io", "data-sync.org"]
    
    # Generate C2 beaconing cluster (similar embeddings)
    c2_base_embedding = generate_embedding(seed=42)
    c2_cluster_id = "c-beaconing-001"
    
    for i in range(15):
        timestamp = base_time + timedelta(minutes=i * 60 + random.randint(0, 5))
        src_ip = internal_ips[0]  # Same source for beaconing
        dst_ip = external_ips[0]
        
        finding = {
            "finding_id": f"f-{timestamp.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}",
            "embedding": generate_similar_embedding(c2_base_embedding, similarity=0.92 + random.random() * 0.05),
            "mitre_predictions": {
                "T1071.001": round(0.80 + random.random() * 0.15, 3),
                "T1573.001": round(0.50 + random.random() * 0.20, 3),
            },
            "anomaly_score": round(0.75 + random.random() * 0.20, 3),
            "entity_context": {
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": random.randint(50000, 60000),
                "dst_port": 443,
                "hostname": hostnames[0],
                "user": users[0],
                "protocol": "tcp"
            },
            "evidence_links": [
                {
                    "type": "flow",
                    "ref": f"flow/{timestamp.strftime('%Y-%m-%d')}/chunk_{random.randint(1, 100):03d}.json",
                    "lines": [random.randint(1000, 2000), random.randint(2001, 2020)]
                }
            ],
            "timestamp": timestamp.isoformat() + "Z",
            "data_source": "flow",
            "cluster_id": c2_cluster_id,
            "severity": "high",
            "status": "new"
        }
        findings.append(finding)
    
    # Generate DNS anomaly cluster
    dns_base_embedding = generate_embedding(seed=123)
    dns_cluster_id = "c-dns-tunnel-001"
    
    for i in range(10):
        timestamp = base_time + timedelta(minutes=i * 30 + random.randint(0, 10))
        src_ip = random.choice(internal_ips)
        
        finding = {
            "finding_id": f"f-{timestamp.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}",
            "embedding": generate_similar_embedding(dns_base_embedding, similarity=0.88 + random.random() * 0.08),
            "mitre_predictions": {
                "T1071.004": round(0.70 + random.random() * 0.20, 3),
                "T1048.003": round(0.40 + random.random() * 0.25, 3),
            },
            "anomaly_score": round(0.60 + random.random() * 0.25, 3),
            "entity_context": {
                "src_ip": src_ip,
                "query_name": f"{uuid.uuid4().hex[:12]}.{random.choice(domains)}",
                "query_type": "TXT" if random.random() > 0.5 else "A",
                "hostname": random.choice(hostnames)
            },
            "evidence_links": [
                {
                    "type": "dns",
                    "ref": f"dns/{timestamp.strftime('%Y-%m-%d')}/chunk_{random.randint(1, 50):03d}.json",
                    "lines": [random.randint(500, 1000), random.randint(1001, 1010)]
                }
            ],
            "timestamp": timestamp.isoformat() + "Z",
            "data_source": "dns",
            "cluster_id": dns_cluster_id,
            "severity": "medium",
            "status": "new"
        }
        findings.append(finding)
    
    # Generate WAF attack attempts
    waf_base_embedding = generate_embedding(seed=456)
    
    for i in range(10):
        timestamp = base_time + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
        src_ip = random.choice(external_ips)
        
        finding = {
            "finding_id": f"f-{timestamp.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}",
            "embedding": generate_similar_embedding(waf_base_embedding, similarity=0.85 + random.random() * 0.10),
            "mitre_predictions": {
                "T1190": round(0.75 + random.random() * 0.20, 3),
                "T1059.001": round(0.30 + random.random() * 0.30, 3),
            },
            "anomaly_score": round(0.70 + random.random() * 0.25, 3),
            "entity_context": {
                "src_ip": src_ip,
                "dst_ip": random.choice(internal_ips[3:]),  # Servers
                "method": random.choice(["POST", "PUT", "GET"]),
                "uri": random.choice(["/api/upload", "/admin/config", "/api/execute", "/data/export"]),
                "status_code": random.choice([200, 403, 500]),
                "user_agent": "Mozilla/5.0 (compatible; scanner/1.0)"
            },
            "evidence_links": [
                {
                    "type": "waf",
                    "ref": f"waf/{timestamp.strftime('%Y-%m-%d')}/chunk_{random.randint(1, 30):03d}.json",
                    "lines": [random.randint(100, 500), random.randint(501, 510)]
                }
            ],
            "timestamp": timestamp.isoformat() + "Z",
            "data_source": "waf",
            "cluster_id": None,
            "severity": random.choice(["medium", "high"]),
            "status": "new"
        }
        findings.append(finding)
    
    # Generate lateral movement indicators
    lateral_base_embedding = generate_embedding(seed=789)
    
    for i in range(8):
        timestamp = base_time + timedelta(hours=random.randint(8, 18), minutes=random.randint(0, 59))
        src_ip = random.choice(internal_ips[:3])
        dst_ip = random.choice(internal_ips[3:])
        
        finding = {
            "finding_id": f"f-{timestamp.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}",
            "embedding": generate_similar_embedding(lateral_base_embedding, similarity=0.80 + random.random() * 0.12),
            "mitre_predictions": {
                "T1021.002": round(0.65 + random.random() * 0.25, 3),
                "T1018": round(0.45 + random.random() * 0.30, 3),
            },
            "anomaly_score": round(0.55 + random.random() * 0.30, 3),
            "entity_context": {
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": random.randint(50000, 60000),
                "dst_port": random.choice([445, 3389, 5985]),
                "hostname": random.choice(hostnames[:3]),
                "user": random.choice(users),
                "protocol": "tcp"
            },
            "evidence_links": [
                {
                    "type": "flow",
                    "ref": f"flow/{timestamp.strftime('%Y-%m-%d')}/chunk_{random.randint(1, 100):03d}.json",
                    "lines": [random.randint(2000, 3000), random.randint(3001, 3015)]
                }
            ],
            "timestamp": timestamp.isoformat() + "Z",
            "data_source": "flow",
            "cluster_id": "c-lateral-001",
            "severity": "medium",
            "status": "new"
        }
        findings.append(finding)
    
    # Generate some low-severity noise
    for i in range(7):
        timestamp = base_time + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
        data_source = random.choice(["flow", "dns", "waf"])
        
        finding = {
            "finding_id": f"f-{timestamp.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}",
            "embedding": generate_embedding(),
            "mitre_predictions": {
                random.choice(list(MITRE_TECHNIQUES.keys())): round(0.30 + random.random() * 0.25, 3),
            },
            "anomaly_score": round(0.30 + random.random() * 0.25, 3),
            "entity_context": {
                "src_ip": random.choice(internal_ips),
                "dst_ip": random.choice(external_ips) if data_source != "dns" else None,
                "hostname": random.choice(hostnames)
            },
            "evidence_links": [
                {
                    "type": data_source,
                    "ref": f"{data_source}/{timestamp.strftime('%Y-%m-%d')}/chunk_{random.randint(1, 100):03d}.json",
                    "lines": [random.randint(100, 500), random.randint(501, 510)]
                }
            ],
            "timestamp": timestamp.isoformat() + "Z",
            "data_source": data_source,
            "cluster_id": None,
            "severity": "low",
            "status": "new"
        }
        findings.append(finding)
    
    # Sort by timestamp
    findings.sort(key=lambda x: x["timestamp"])
    
    return findings


def load_export_file(file_path: Path) -> list[dict]:
    """
    Load findings from a DeepTempo export file.
    
    Supports:
    - JSON file with {"findings": [...]}
    - JSONL file with one finding per line
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Export file not found: {file_path}")
    
    findings = []
    
    if file_path.suffix == ".jsonl":
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    findings.append(json.loads(line))
    else:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                findings = data
            elif isinstance(data, dict) and "findings" in data:
                findings = data["findings"]
            else:
                raise ValueError("Invalid export format")
    
    return findings


def transform_finding(raw: dict) -> dict:
    """
    Transform a raw DeepTempo export finding to internal schema.
    
    This handles any format differences between export and internal schema.
    """
    # For now, assume export format matches internal schema
    # In production, this would handle version differences
    
    # Ensure required fields
    if "finding_id" not in raw:
        raw["finding_id"] = f"f-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    
    if "status" not in raw:
        raw["status"] = "new"
    
    if "severity" not in raw:
        # Calculate severity from anomaly score
        score = raw.get("anomaly_score", 0.5)
        if score >= 0.8:
            raw["severity"] = "critical"
        elif score >= 0.6:
            raw["severity"] = "high"
        elif score >= 0.4:
            raw["severity"] = "medium"
        else:
            raw["severity"] = "low"
    
    return raw


def save_findings(findings: list[dict]) -> None:
    """Save findings to the data store."""
    FINDINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(FINDINGS_FILE, 'w') as f:
        json.dump({"findings": findings}, f, indent=2)
    
    logger.info(f"Saved {len(findings)} findings to {FINDINGS_FILE}")


def load_findings() -> list[dict]:
    """Load existing findings from the data store."""
    if not FINDINGS_FILE.exists():
        return []
    
    with open(FINDINGS_FILE, 'r') as f:
        data = json.load(f)
    
    return data.get("findings", [])


def main(export_file: Optional[str] = None):
    """
    Main entry point for the loader.
    
    Args:
        export_file: Path to DeepTempo export file. If None, generates sample data.
    """
    if export_file:
        logger.info(f"Loading findings from: {export_file}")
        raw_findings = load_export_file(Path(export_file))
        findings = [transform_finding(f) for f in raw_findings]
    else:
        logger.info("No export file provided, generating sample data...")
        findings = generate_sample_findings(50)
    
    # Save to data store
    save_findings(findings)
    
    # Print summary
    print(f"\n{'='*60}")
    print("DeepTempo Findings Loaded")
    print(f"{'='*60}")
    print(f"Total findings: {len(findings)}")
    
    # Count by data source
    by_source = {}
    for f in findings:
        source = f.get("data_source", "unknown")
        by_source[source] = by_source.get(source, 0) + 1
    
    print(f"\nBy data source:")
    for source, count in sorted(by_source.items()):
        print(f"  {source}: {count}")
    
    # Count by severity
    by_severity = {}
    for f in findings:
        severity = f.get("severity", "unknown")
        by_severity[severity] = by_severity.get(severity, 0) + 1
    
    print(f"\nBy severity:")
    for severity in ["critical", "high", "medium", "low"]:
        count = by_severity.get(severity, 0)
        print(f"  {severity}: {count}")
    
    # Count clusters
    clusters = set(f.get("cluster_id") for f in findings if f.get("cluster_id"))
    print(f"\nClusters identified: {len(clusters)}")
    
    print(f"\nData saved to: {FINDINGS_FILE}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import sys
    export_file = sys.argv[1] if len(sys.argv) > 1 else None
    main(export_file)
