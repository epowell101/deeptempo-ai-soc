#!/usr/bin/env python3
"""
Rules-Only Detection Pipeline

Simulates traditional SIEM detection using Sigma-like rules.
Generates alerts that are:
- Noisy (many false positives)
- Uncorrelated (each alert is independent)
- Missing context (no attack narrative)

Also exposes detailed rule information including:
- Rule logic (human-readable)
- Thresholds and conditions
- Evasion risk assessment
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

SCENARIO_DIR = Path(__file__).parent.parent / "data" / "scenarios" / "default_attack"


# Sigma-like detection rules with detailed metadata
DETECTION_RULES = [
    {
        "id": "rule_001",
        "name": "Outbound Connection to Rare External IP",
        "description": "Detects connections to external IPs not in whitelist",
        "severity": "medium",
        "tactic": "Command and Control",
        "technique": "T1071.001",
        "false_positive_rate": 0.15,
        "evasion_risk": "HIGH",
        "evasion_method": "Use legitimate cloud infrastructure IPs (AWS, Azure, Cloudflare)",
        "logic_human": "IF destination IP is external AND NOT in known-good list THEN alert",
        "threshold": "Any single connection",
        "condition": lambda e: (
            e.get("service") in ["ssl", "http"] and
            not e.get("id.resp_h", "").startswith("10.") and
            not e.get("id.resp_h", "").startswith("192.168.") and
            e.get("id.resp_h") not in [
                "8.8.8.8", "8.8.4.4", "1.1.1.1",
                "142.250.80.46", "142.250.80.78",
                "157.240.1.35", "157.240.1.63",
                "52.94.236.248", "54.239.28.85",
                "13.107.42.14", "20.190.151.68",
                # Legitimate cloud IPs that attackers abuse
                "13.225.78.45", "104.18.32.68", "151.101.1.140",
                "52.84.150.23", "172.67.182.31",
            ]
        )
    },
    {
        "id": "rule_002", 
        "name": "Suspicious DNS Query - Long Subdomain",
        "description": "Detects DNS queries with unusually long subdomains (potential tunneling)",
        "severity": "medium",
        "tactic": "Command and Control",
        "technique": "T1071.004",
        "false_positive_rate": 0.05,
        "evasion_risk": "MEDIUM",
        "evasion_method": "Keep subdomains under 20 characters, use multiple short queries",
        "logic_human": "IF DNS query subdomain length > 20 characters THEN alert",
        "threshold": "Subdomain > 20 chars",
        "condition": lambda e: (
            "query" in e and
            len(e.get("query", "").split(".")[0]) > 20
        )
    },
    {
        "id": "rule_003",
        "name": "Suspicious DNS Query - TXT Record",
        "description": "Detects TXT record queries which may indicate DNS tunneling",
        "severity": "low",
        "tactic": "Command and Control",
        "technique": "T1071.004",
        "false_positive_rate": 0.08,
        "evasion_risk": "LOW",
        "evasion_method": "Use A/AAAA records instead of TXT, encode data in subdomain",
        "logic_human": "IF DNS query type = TXT THEN alert",
        "threshold": "Any TXT query",
        "condition": lambda e: e.get("qtype") == "TXT"
    },
    {
        "id": "rule_004",
        "name": "Internal RDP Connection",
        "description": "Detects RDP connections between internal hosts",
        "severity": "low",
        "tactic": "Lateral Movement",
        "technique": "T1021.001",
        "false_positive_rate": 0.20,
        "evasion_risk": "MEDIUM",
        "evasion_method": "Use WMI, WinRM, or PowerShell Remoting instead of RDP",
        "logic_human": "IF destination port = 3389 AND both IPs are internal THEN alert",
        "threshold": "Any RDP connection",
        "condition": lambda e: (
            e.get("id.resp_p") == 3389 and
            e.get("id.orig_h", "").startswith("10.") and
            e.get("id.resp_h", "").startswith("10.")
        )
    },
    {
        "id": "rule_005",
        "name": "Internal SMB Connection",
        "description": "Detects SMB connections between internal hosts",
        "severity": "low",
        "tactic": "Lateral Movement",
        "technique": "T1021.002",
        "false_positive_rate": 0.25,
        "evasion_risk": "MEDIUM",
        "evasion_method": "Use WMI (port 135), WinRM (5985/5986), or SSH",
        "logic_human": "IF destination port = 445 AND both IPs are internal THEN alert",
        "threshold": "Any SMB connection",
        "condition": lambda e: (
            e.get("id.resp_p") == 445 and
            e.get("id.orig_h", "").startswith("10.") and
            e.get("id.resp_h", "").startswith("10.")
        )
    },
    {
        "id": "rule_006",
        "name": "Large Outbound Data Transfer",
        "description": "Detects connections with large outbound byte count",
        "severity": "medium",
        "tactic": "Exfiltration",
        "technique": "T1041",
        "false_positive_rate": 0.10,
        "evasion_risk": "HIGH",
        "evasion_method": "Chunk data into transfers < 500KB, spread over hours/days",
        "logic_human": "IF outbound bytes > 500KB AND destination is external THEN alert",
        "threshold": "> 500,000 bytes",
        "condition": lambda e: (
            e.get("orig_bytes", 0) > 500000 and
            not e.get("id.resp_h", "").startswith("10.")
        )
    },
    {
        "id": "rule_007",
        "name": "Connection to Known Bad Port",
        "description": "Detects connections to suspicious ports commonly used by malware",
        "severity": "high",
        "tactic": "Command and Control",
        "technique": "T1571",
        "false_positive_rate": 0.03,
        "evasion_risk": "LOW",
        "evasion_method": "Use standard ports (443, 80, 53) for C2 communication",
        "logic_human": "IF destination port IN [4444, 5555, 6666, 8888, 9999, 1337] THEN alert",
        "threshold": "Any connection to listed ports",
        "condition": lambda e: e.get("id.resp_p") in [4444, 5555, 6666, 8888, 9999, 1337]
    },
    {
        "id": "rule_008",
        "name": "Periodic Beaconing Pattern",
        "description": "Detects regular interval connections (potential C2)",
        "severity": "medium",
        "tactic": "Command and Control",
        "technique": "T1071.001",
        "false_positive_rate": 0.12,
        "evasion_risk": "HIGH",
        "evasion_method": "Add jitter to beacon intervals, vary connection duration",
        "logic_human": "IF SSL connection AND duration < 5s AND small payload AND external THEN alert",
        "threshold": "Duration < 5s, payload < 1KB",
        "condition": lambda e: (
            e.get("service") == "ssl" and
            e.get("duration", 0) < 5 and
            e.get("orig_bytes", 0) < 1000 and
            not e.get("id.resp_h", "").startswith("10.")
        )
    },
    {
        "id": "rule_009",
        "name": "DNS Query to Suspicious Domain Pattern",
        "description": "Detects DNS queries to domains matching suspicious naming patterns",
        "severity": "high",
        "tactic": "Command and Control",
        "technique": "T1071.004",
        "false_positive_rate": 0.02,
        "evasion_risk": "MEDIUM",
        "evasion_method": "Use innocuous domain names that mimic legitimate services",
        "logic_human": "IF DNS query contains patterns like 'data-sync', 'cdn-update' THEN alert",
        "threshold": "Pattern match in domain",
        "condition": lambda e: (
            "query" in e and
            any(pattern in e.get("query", "") for pattern in [
                "data-sync", "cdn-update", "api-metrics",
                "update-service", "cloud-sync"
            ])
        )
    },
    {
        "id": "rule_010",
        "name": "Workstation to Server Direct Connection",
        "description": "Detects direct connections from workstations to servers",
        "severity": "low",
        "tactic": "Lateral Movement",
        "technique": "T1021",
        "false_positive_rate": 0.30,
        "evasion_risk": "HIGH",
        "evasion_method": "Route through jump hosts, use legitimate admin tools",
        "logic_human": "IF source hostname starts with 'workstation' AND dest is server subnet THEN alert",
        "threshold": "Any direct connection",
        "condition": lambda e: (
            e.get("hostname", "").startswith("workstation") and
            e.get("id.resp_h", "").startswith("10.0.2.")
        )
    },
    {
        "id": "rule_011",
        "name": "External Connection to Web Server",
        "description": "Detects external connections to internal web servers",
        "severity": "low",
        "tactic": "Initial Access",
        "technique": "T1190",
        "false_positive_rate": 0.40,
        "evasion_risk": "LOW",
        "evasion_method": "Blend with legitimate web traffic, use common user agents",
        "logic_human": "IF source is external AND dest is web server AND port is HTTP/HTTPS THEN alert",
        "threshold": "Any external web connection",
        "condition": lambda e: (
            not e.get("id.orig_h", "").startswith("10.") and
            e.get("id.resp_h") == "10.0.2.20" and
            e.get("id.resp_p") in [80, 443, 8080]
        )
    },
    {
        "id": "rule_012",
        "name": "Failed Connection Attempt",
        "description": "Detects rejected or reset connections (potential scanning)",
        "severity": "low",
        "tactic": "Discovery",
        "technique": "T1046",
        "false_positive_rate": 0.15,
        "evasion_risk": "MEDIUM",
        "evasion_method": "Slow down scanning, use passive reconnaissance",
        "logic_human": "IF connection state is REJ, RSTO, or RSTOS0 THEN alert",
        "threshold": "Any failed connection",
        "condition": lambda e: e.get("conn_state") in ["REJ", "RSTO", "RSTOS0"]
    },
]


def get_rule_details() -> List[Dict]:
    """Get detailed information about all rules (without lambda functions)."""
    rules_info = []
    for rule in DETECTION_RULES:
        rules_info.append({
            "id": rule["id"],
            "name": rule["name"],
            "description": rule["description"],
            "severity": rule["severity"],
            "tactic": rule["tactic"],
            "technique": rule.get("technique", "Unknown"),
            "false_positive_rate": rule["false_positive_rate"],
            "evasion_risk": rule["evasion_risk"],
            "evasion_method": rule["evasion_method"],
            "logic_human": rule["logic_human"],
            "threshold": rule["threshold"]
        })
    return rules_info


def apply_rules(events: List[Dict], rules: List[Dict]) -> List[Dict]:
    """
    Apply detection rules to events and generate alerts.
    
    This simulates a traditional SIEM - each rule fires independently,
    creating many alerts without correlation.
    """
    alerts = []
    alert_idx = 0
    
    for event in events:
        for rule in rules:
            try:
                if rule["condition"](event):
                    alert = {
                        "id": f"alert_{alert_idx:05d}",
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "description": rule["description"],
                        "severity": rule["severity"],
                        "tactic": rule["tactic"],
                        "technique": rule.get("technique", "Unknown"),
                        "timestamp": event.get("ts"),
                        "source_ip": event.get("id.orig_h"),
                        "dest_ip": event.get("id.resp_h"),
                        "dest_port": event.get("id.resp_p"),
                        "hostname": event.get("hostname"),
                        "user": event.get("user"),
                        "event_id": event.get("id"),
                        "raw_event": event
                    }
                    alerts.append(alert)
                    alert_idx += 1
            except Exception:
                continue
    
    return alerts


def generate_rules_output():
    """Generate alerts from rules and save to rules_output directory."""
    print("=" * 60)
    print("Running Rules-Only Detection")
    print("=" * 60)
    
    # Load raw logs
    conn_file = SCENARIO_DIR / "raw_logs" / "zeek_conn.json"
    dns_file = SCENARIO_DIR / "raw_logs" / "zeek_dns.json"
    
    with open(conn_file) as f:
        conn_events = json.load(f)
    
    with open(dns_file) as f:
        dns_events = json.load(f)
    
    all_events = conn_events + dns_events
    print(f"\nLoaded {len(all_events)} events")
    
    # Apply rules
    alerts = apply_rules(all_events, DETECTION_RULES)
    print(f"Generated {len(alerts)} alerts")
    
    # Calculate rule statistics
    rule_stats = {}
    for rule in DETECTION_RULES:
        rule_alerts = [a for a in alerts if a["rule_id"] == rule["id"]]
        rule_stats[rule["id"]] = {
            "name": rule["name"],
            "description": rule["description"],
            "severity": rule["severity"],
            "tactic": rule["tactic"],
            "technique": rule.get("technique", "Unknown"),
            "alert_count": len(rule_alerts),
            "false_positive_rate": rule["false_positive_rate"],
            "evasion_risk": rule["evasion_risk"],
            "evasion_method": rule["evasion_method"],
            "logic_human": rule["logic_human"],
            "threshold": rule["threshold"]
        }
    
    # Sort alerts by timestamp
    alerts.sort(key=lambda x: x["timestamp"])
    
    # Save outputs
    output_dir = SCENARIO_DIR / "rules_output"
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "alerts.json", "w") as f:
        json.dump(alerts, f, indent=2)
    
    with open(output_dir / "rule_stats.json", "w") as f:
        json.dump(rule_stats, f, indent=2)
    
    # Save detailed rule definitions
    with open(output_dir / "rule_definitions.json", "w") as f:
        json.dump(get_rule_details(), f, indent=2)
    
    # Print summary
    print(f"\n" + "=" * 60)
    print("Rules-Only Detection Summary")
    print("=" * 60)
    print(f"\nTotal alerts: {len(alerts)}")
    print(f"Rules triggered: {len([r for r in rule_stats.values() if r['alert_count'] > 0])}/{len(DETECTION_RULES)}")
    
    print(f"\nTop alerting rules:")
    sorted_rules = sorted(rule_stats.items(), key=lambda x: x[1]["alert_count"], reverse=True)
    for rule_id, stats in sorted_rules[:5]:
        print(f"  {stats['name']}: {stats['alert_count']} alerts")
    
    print(f"\nRules by evasion risk:")
    high_risk = [r for r in rule_stats.values() if r["evasion_risk"] == "HIGH"]
    med_risk = [r for r in rule_stats.values() if r["evasion_risk"] == "MEDIUM"]
    low_risk = [r for r in rule_stats.values() if r["evasion_risk"] == "LOW"]
    print(f"  HIGH risk (easily evaded): {len(high_risk)} rules")
    print(f"  MEDIUM risk: {len(med_risk)} rules")
    print(f"  LOW risk: {len(low_risk)} rules")
    
    # Check for evasive events
    gt_file = SCENARIO_DIR / "ground_truth.json"
    if gt_file.exists():
        with open(gt_file) as f:
            ground_truth = json.load(f)
        
        evasive_events = [eid for eid, info in ground_truth["events"].items() 
                         if info.get("evasive", False)]
        detected_evasive = [a for a in alerts if a["event_id"] in evasive_events]
        
        print(f"\nEvasive attack detection:")
        print(f"  Total evasive events: {len(evasive_events)}")
        print(f"  Detected by rules: {len(detected_evasive)}")
        print(f"  Missed by rules: {len(evasive_events) - len(detected_evasive)}")
        print(f"  Evasion success rate: {(len(evasive_events) - len(detected_evasive)) / len(evasive_events) * 100:.1f}%")
    
    return alerts, rule_stats


if __name__ == "__main__":
    generate_rules_output()
