#!/usr/bin/env python3
"""
LogLM Detection Pipeline

Simulates DeepTempo LogLM detection which:
- Identifies MALICIOUS BEHAVIORS (not just anomalies)
- Generates embeddings for similarity search
- Auto-correlates related events into incidents
- Provides MITRE ATT&CK classification
- Has high precision (few false positives)
"""

import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set
import hashlib

SCENARIO_DIR = Path(__file__).parent.parent / "data" / "scenarios" / "default_attack"

# MITRE ATT&CK technique details
MITRE_TECHNIQUES = {
    "T1078": {
        "name": "Valid Accounts",
        "tactic": "Initial Access",
        "description": "Adversaries may obtain and abuse credentials of existing accounts"
    },
    "T1071.001": {
        "name": "Web Protocols",
        "tactic": "Command and Control",
        "description": "Adversaries may communicate using application layer protocols"
    },
    "T1071.004": {
        "name": "DNS",
        "tactic": "Command and Control",
        "description": "Adversaries may communicate using the DNS protocol"
    },
    "T1573.001": {
        "name": "Encrypted Channel",
        "tactic": "Command and Control",
        "description": "Adversaries may employ encryption to conceal C2 traffic"
    },
    "T1021.001": {
        "name": "Remote Desktop Protocol",
        "tactic": "Lateral Movement",
        "description": "Adversaries may use RDP to move laterally"
    },
    "T1021.002": {
        "name": "SMB/Windows Admin Shares",
        "tactic": "Lateral Movement",
        "description": "Adversaries may use SMB to move laterally"
    },
    "T1048.003": {
        "name": "Exfiltration Over Unencrypted Non-C2 Protocol",
        "tactic": "Exfiltration",
        "description": "Adversaries may steal data via DNS"
    },
    "T1041": {
        "name": "Exfiltration Over C2 Channel",
        "tactic": "Exfiltration",
        "description": "Adversaries may steal data over the C2 channel"
    },
    "T1190": {
        "name": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
        "description": "Adversaries may exploit vulnerabilities in internet-facing systems"
    },
}


def generate_embedding(event: Dict, technique: str) -> List[float]:
    """
    Generate a simulated embedding for an event.
    
    In reality, LogLM would generate this from the log content.
    Here we create embeddings that cluster similar events together.
    """
    # Create a seed based on technique and key event features
    seed_str = f"{technique}_{event.get('id.resp_h', '')}_{event.get('service', '')}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    
    np.random.seed(seed)
    
    # Base embedding for the technique
    base = np.random.randn(768) * 0.3
    
    # Add some noise for variation
    np.random.seed(None)
    noise = np.random.randn(768) * 0.1
    
    embedding = base + noise
    
    # Normalize
    embedding = embedding / np.linalg.norm(embedding)
    
    return embedding.tolist()


def detect_malicious_behaviors(events: List[Dict], ground_truth: Dict) -> List[Dict]:
    """
    Simulate LogLM detection of malicious behaviors.
    
    LogLM identifies MALICIOUS patterns, not just anomalies.
    It has high precision because it's trained on security-specific data.
    """
    findings = []
    finding_idx = 0
    
    # Get malicious event IDs from ground truth
    malicious_events = {
        eid: info for eid, info in ground_truth["events"].items()
        if info["label"] == "malicious"
    }
    
    # Create event lookup
    event_lookup = {e["id"]: e for e in events}
    
    # Process each malicious event
    for event_id, truth in malicious_events.items():
        if event_id not in event_lookup:
            continue
            
        event = event_lookup[event_id]
        technique = truth["technique"]
        
        # LogLM generates a finding for each malicious behavior
        finding = {
            "id": f"finding_{finding_idx:05d}",
            "timestamp": event.get("ts"),
            "title": generate_finding_title(event, technique),
            "description": truth["description"],
            "severity": calculate_severity(technique),
            "confidence": calculate_confidence(technique),
            "source_ip": event.get("id.orig_h"),
            "dest_ip": event.get("id.resp_h"),
            "dest_port": event.get("id.resp_p"),
            "hostname": event.get("hostname"),
            "user": event.get("user"),
            "event_ids": [event_id],
            "attack_phase": truth["attack_phase"],
            "mitre_predictions": [
                {
                    "technique_id": technique,
                    "technique_name": MITRE_TECHNIQUES[technique]["name"],
                    "tactic": MITRE_TECHNIQUES[technique]["tactic"],
                    "confidence": calculate_confidence(technique)
                }
            ],
            "embedding": generate_embedding(event, technique),
            "raw_event": event
        }
        
        findings.append(finding)
        finding_idx += 1
    
    # Add a few false positives (but very few - LogLM has high precision)
    # About 3% false positive rate
    benign_events = [e for e in events if ground_truth["events"].get(e["id"], {}).get("label") == "benign"]
    num_fps = max(1, int(len(findings) * 0.03))
    
    np.random.seed(42)
    fp_events = np.random.choice(len(benign_events), size=min(num_fps, len(benign_events)), replace=False)
    
    for idx in fp_events:
        event = benign_events[idx]
        # False positives are low confidence
        finding = {
            "id": f"finding_{finding_idx:05d}",
            "timestamp": event.get("ts"),
            "title": f"Suspicious activity from {event.get('hostname', 'unknown')}",
            "description": "Potentially suspicious network behavior detected",
            "severity": "low",
            "confidence": 0.45,  # Low confidence = likely FP
            "source_ip": event.get("id.orig_h"),
            "dest_ip": event.get("id.resp_h"),
            "dest_port": event.get("id.resp_p"),
            "hostname": event.get("hostname"),
            "user": event.get("user"),
            "event_ids": [event["id"]],
            "attack_phase": None,
            "mitre_predictions": [
                {
                    "technique_id": "T1071.001",
                    "technique_name": "Web Protocols",
                    "tactic": "Command and Control",
                    "confidence": 0.45
                }
            ],
            "embedding": generate_embedding(event, "T1071.001"),
            "raw_event": event
        }
        findings.append(finding)
        finding_idx += 1
    
    return findings


def generate_finding_title(event: Dict, technique: str) -> str:
    """Generate a descriptive title for a finding."""
    tech_info = MITRE_TECHNIQUES[technique]
    hostname = event.get("hostname", "unknown")
    dest = event.get("id.resp_h", "unknown")
    
    titles = {
        "T1078": f"Credential abuse detected on {hostname}",
        "T1071.001": f"C2 communication from {hostname} to {dest}",
        "T1071.004": f"DNS tunneling detected from {hostname}",
        "T1573.001": f"Encrypted C2 channel from {hostname}",
        "T1021.001": f"RDP lateral movement from {hostname}",
        "T1021.002": f"SMB lateral movement from {hostname}",
        "T1048.003": f"Data exfiltration via DNS from {hostname}",
        "T1041": f"Data exfiltration over C2 from {hostname}",
        "T1190": f"Web exploitation attempt targeting {dest}",
    }
    
    return titles.get(technique, f"{tech_info['name']} detected")


def calculate_severity(technique: str) -> str:
    """Calculate severity based on technique."""
    high_severity = ["T1041", "T1048.003", "T1078"]
    critical_techniques = []
    
    if technique in critical_techniques:
        return "critical"
    elif technique in high_severity:
        return "high"
    else:
        return "medium"


def calculate_confidence(technique: str) -> float:
    """Calculate confidence score for technique detection."""
    # LogLM has high confidence for behaviors it's trained on
    confidence_map = {
        "T1078": 0.85,
        "T1071.001": 0.89,
        "T1071.004": 0.82,
        "T1573.001": 0.78,
        "T1021.001": 0.86,
        "T1021.002": 0.84,
        "T1048.003": 0.81,
        "T1041": 0.88,
        "T1190": 0.79,
    }
    base = confidence_map.get(technique, 0.75)
    # Add small random variation
    return round(base + np.random.uniform(-0.05, 0.05), 2)


def correlate_into_incidents(findings: List[Dict]) -> List[Dict]:
    """
    Auto-correlate findings into incidents.
    
    LogLM groups related findings based on:
    - Embedding similarity
    - Temporal proximity
    - Entity relationships
    """
    incidents = []
    
    # Group by attack phase (simulating correlation)
    phase_groups = {}
    for finding in findings:
        phase = finding.get("attack_phase")
        if phase is not None:
            if phase not in phase_groups:
                phase_groups[phase] = []
            phase_groups[phase].append(finding)
    
    # Create incidents from correlated findings
    # Main incident: the multi-stage attack
    main_incident_findings = []
    for phase in sorted(phase_groups.keys()):
        main_incident_findings.extend(phase_groups[phase])
    
    if main_incident_findings:
        # Calculate incident embedding (average of finding embeddings)
        embeddings = [f["embedding"] for f in main_incident_findings]
        incident_embedding = np.mean(embeddings, axis=0).tolist()
        
        # Get all techniques
        techniques = set()
        for f in main_incident_findings:
            for pred in f["mitre_predictions"]:
                techniques.add(pred["technique_id"])
        
        incidents.append({
            "id": "INC-001",
            "title": "Multi-Stage Attack: C2, Lateral Movement, and Data Exfiltration",
            "severity": "critical",
            "status": "open",
            "created_at": main_incident_findings[0]["timestamp"],
            "updated_at": main_incident_findings[-1]["timestamp"],
            "finding_ids": [f["id"] for f in main_incident_findings],
            "finding_count": len(main_incident_findings),
            "techniques": list(techniques),
            "phases_detected": list(phase_groups.keys()),
            "affected_hosts": list(set(f["hostname"] for f in main_incident_findings if f.get("hostname"))),
            "embedding": incident_embedding,
            "summary": generate_incident_summary(main_incident_findings)
        })
    
    # Separate incident for web exploitation (different attack vector)
    web_findings = [f for f in findings if f.get("attack_phase") == 5]
    if web_findings:
        incidents.append({
            "id": "INC-002",
            "title": "Web Application Exploitation Attempts",
            "severity": "high",
            "status": "open",
            "created_at": web_findings[0]["timestamp"],
            "updated_at": web_findings[-1]["timestamp"],
            "finding_ids": [f["id"] for f in web_findings],
            "finding_count": len(web_findings),
            "techniques": ["T1190"],
            "phases_detected": [5],
            "affected_hosts": ["server-web-02"],
            "embedding": np.mean([f["embedding"] for f in web_findings], axis=0).tolist(),
            "summary": f"Detected {len(web_findings)} web exploitation attempts from external IPs targeting server-web-02"
        })
    
    # Low confidence findings as separate incident
    low_conf_findings = [f for f in findings if f.get("confidence", 1) < 0.5]
    if low_conf_findings:
        incidents.append({
            "id": "INC-003",
            "title": "Suspicious Activity - Requires Investigation",
            "severity": "low",
            "status": "open",
            "created_at": low_conf_findings[0]["timestamp"],
            "updated_at": low_conf_findings[-1]["timestamp"],
            "finding_ids": [f["id"] for f in low_conf_findings],
            "finding_count": len(low_conf_findings),
            "techniques": [],
            "phases_detected": [],
            "affected_hosts": list(set(f["hostname"] for f in low_conf_findings if f.get("hostname"))),
            "embedding": np.mean([f["embedding"] for f in low_conf_findings], axis=0).tolist() if low_conf_findings else [],
            "summary": "Low confidence detections that may be false positives"
        })
    
    return incidents


def generate_incident_summary(findings: List[Dict]) -> str:
    """Generate a human-readable incident summary."""
    phases = sorted(set(f["attack_phase"] for f in findings if f.get("attack_phase")))
    hosts = set(f["hostname"] for f in findings if f.get("hostname"))
    
    phase_names = {
        1: "initial compromise",
        2: "C2 establishment",
        3: "lateral movement",
        4: "data exfiltration",
        5: "web exploitation"
    }
    
    phase_str = ", ".join(phase_names.get(p, f"phase {p}") for p in phases)
    
    return (
        f"Detected multi-stage attack spanning {len(phases)} phases: {phase_str}. "
        f"Affected {len(hosts)} hosts. "
        f"Attack originated from workstation-042 and spread to critical servers including server-db-01. "
        f"Data exfiltration detected via both C2 channel and DNS tunneling."
    )


def generate_loglm_output():
    """Generate LogLM findings and incidents."""
    print("Running LogLM detection...")
    
    # Load raw logs
    conn_file = SCENARIO_DIR / "raw_logs" / "zeek_conn.json"
    dns_file = SCENARIO_DIR / "raw_logs" / "zeek_dns.json"
    gt_file = SCENARIO_DIR / "ground_truth.json"
    
    with open(conn_file) as f:
        conn_events = json.load(f)
    
    with open(dns_file) as f:
        dns_events = json.load(f)
    
    with open(gt_file) as f:
        ground_truth = json.load(f)
    
    all_events = conn_events + dns_events
    print(f"  Loaded {len(all_events)} events")
    
    # Detect malicious behaviors
    findings = detect_malicious_behaviors(all_events, ground_truth)
    print(f"  Generated {len(findings)} findings")
    
    # Correlate into incidents
    incidents = correlate_into_incidents(findings)
    print(f"  Correlated into {len(incidents)} incidents")
    
    # Sort findings by timestamp
    findings.sort(key=lambda x: x["timestamp"])
    
    # Calculate technique statistics
    technique_stats = {}
    for finding in findings:
        for pred in finding["mitre_predictions"]:
            tech_id = pred["technique_id"]
            if tech_id not in technique_stats:
                technique_stats[tech_id] = {
                    "technique_id": tech_id,
                    "technique_name": pred["technique_name"],
                    "tactic": pred["tactic"],
                    "count": 0,
                    "avg_confidence": 0
                }
            technique_stats[tech_id]["count"] += 1
            technique_stats[tech_id]["avg_confidence"] += pred["confidence"]
    
    for tech in technique_stats.values():
        tech["avg_confidence"] = round(tech["avg_confidence"] / tech["count"], 2)
    
    # Save outputs
    output_dir = SCENARIO_DIR / "loglm_output"
    output_dir.mkdir(exist_ok=True)
    
    # Remove embeddings from saved findings to reduce file size
    findings_for_save = []
    for f in findings:
        f_copy = f.copy()
        f_copy["embedding"] = f["embedding"][:10] + ["...truncated..."]  # Keep first 10 dims for reference
        findings_for_save.append(f_copy)
    
    with open(output_dir / "findings.json", "w") as f:
        json.dump(findings_for_save, f, indent=2)
    
    # Save full embeddings separately for similarity search
    embeddings = {f["id"]: f["embedding"] for f in findings}
    with open(output_dir / "embeddings.json", "w") as f:
        json.dump(embeddings, f)
    
    with open(output_dir / "incidents.json", "w") as f:
        json.dump(incidents, f, indent=2)
    
    with open(output_dir / "technique_stats.json", "w") as f:
        json.dump(technique_stats, f, indent=2)
    
    # Print summary
    print(f"\nLogLM Detection Summary:")
    print(f"  Total findings: {len(findings)}")
    print(f"  Incidents: {len(incidents)}")
    print(f"  Techniques detected: {len(technique_stats)}")
    
    high_conf = len([f for f in findings if f.get("confidence", 0) >= 0.7])
    print(f"  High confidence findings: {high_conf}")
    
    print(f"\n  Incidents:")
    for inc in incidents:
        print(f"    {inc['id']}: {inc['title']} ({inc['severity']}, {inc['finding_count']} findings)")
    
    return findings, incidents


if __name__ == "__main__":
    generate_loglm_output()
