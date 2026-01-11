#!/usr/bin/env python3
"""
Rules-Only Detection Pipeline

Simulates traditional SIEM detection using Sigma-like rules.
Generates alerts that are:
- Noisy (many false positives)
- Uncorrelated (each alert is independent)
- Missing context (no attack narrative)
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

SCENARIO_DIR = Path(__file__).parent.parent / "data" / "scenarios" / "default_attack"


# Sigma-like detection rules
DETECTION_RULES = [
    {
        "id": "rule_001",
        "name": "Outbound Connection to Rare External IP",
        "description": "Detects connections to external IPs not in whitelist",
        "severity": "medium",
        "tactic": "Command and Control",
        "false_positive_rate": 0.15,  # 15% of benign traffic triggers this
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
            ]
        )
    },
    {
        "id": "rule_002", 
        "name": "Suspicious DNS Query - Long Subdomain",
        "description": "Detects DNS queries with unusually long subdomains (potential tunneling)",
        "severity": "medium",
        "tactic": "Command and Control",
        "false_positive_rate": 0.05,
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
        "false_positive_rate": 0.08,
        "condition": lambda e: e.get("qtype") == "TXT"
    },
    {
        "id": "rule_004",
        "name": "Internal RDP Connection",
        "description": "Detects RDP connections between internal hosts",
        "severity": "low",
        "tactic": "Lateral Movement",
        "false_positive_rate": 0.20,  # IT admins use RDP legitimately
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
        "false_positive_rate": 0.25,  # Very common in enterprise
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
        "false_positive_rate": 0.10,
        "condition": lambda e: (
            e.get("orig_bytes", 0) > 500000 and
            not e.get("id.resp_h", "").startswith("10.")
        )
    },
    {
        "id": "rule_007",
        "name": "Connection to Known Bad Port",
        "description": "Detects connections to suspicious ports",
        "severity": "high",
        "tactic": "Command and Control",
        "false_positive_rate": 0.03,
        "condition": lambda e: e.get("id.resp_p") in [4444, 5555, 6666, 8888, 9999, 1337]
    },
    {
        "id": "rule_008",
        "name": "Periodic Beaconing Pattern",
        "description": "Detects regular interval connections (potential C2)",
        "severity": "medium",
        "tactic": "Command and Control",
        "false_positive_rate": 0.12,  # Many apps beacon legitimately
        "condition": lambda e: (
            e.get("service") == "ssl" and
            e.get("duration", 0) < 5 and
            e.get("orig_bytes", 0) < 1000 and
            not e.get("id.resp_h", "").startswith("10.")
        )
    },
    {
        "id": "rule_009",
        "name": "DNS Query to Suspicious Domain",
        "description": "Detects DNS queries to domains matching suspicious patterns",
        "severity": "high",
        "tactic": "Command and Control",
        "false_positive_rate": 0.02,
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
        "name": "Workstation to Server Connection",
        "description": "Detects direct connections from workstations to servers",
        "severity": "low",
        "tactic": "Lateral Movement",
        "false_positive_rate": 0.30,  # Very common
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
        "false_positive_rate": 0.40,  # Web servers get lots of traffic
        "condition": lambda e: (
            not e.get("id.orig_h", "").startswith("10.") and
            e.get("id.resp_h") == "10.0.2.20" and
            e.get("id.resp_p") in [80, 443, 8080]
        )
    },
    {
        "id": "rule_012",
        "name": "Failed Connection Attempt",
        "description": "Detects rejected or reset connections",
        "severity": "low",
        "tactic": "Discovery",
        "false_positive_rate": 0.15,
        "condition": lambda e: e.get("conn_state") in ["REJ", "RSTO", "RSTOS0"]
    },
]


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
    print("Running rules-only detection...")
    
    # Load raw logs
    conn_file = SCENARIO_DIR / "raw_logs" / "zeek_conn.json"
    dns_file = SCENARIO_DIR / "raw_logs" / "zeek_dns.json"
    
    with open(conn_file) as f:
        conn_events = json.load(f)
    
    with open(dns_file) as f:
        dns_events = json.load(f)
    
    all_events = conn_events + dns_events
    print(f"  Loaded {len(all_events)} events")
    
    # Apply rules
    alerts = apply_rules(all_events, DETECTION_RULES)
    print(f"  Generated {len(alerts)} alerts")
    
    # Calculate rule statistics
    rule_stats = {}
    for rule in DETECTION_RULES:
        rule_alerts = [a for a in alerts if a["rule_id"] == rule["id"]]
        rule_stats[rule["id"]] = {
            "name": rule["name"],
            "severity": rule["severity"],
            "tactic": rule["tactic"],
            "alert_count": len(rule_alerts),
            "false_positive_rate": rule["false_positive_rate"]
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
    
    # Print summary
    print(f"\nRules-Only Detection Summary:")
    print(f"  Total alerts: {len(alerts)}")
    print(f"  Rules triggered: {len([r for r in rule_stats.values() if r['alert_count'] > 0])}")
    print(f"\n  Top alerting rules:")
    
    sorted_rules = sorted(rule_stats.items(), key=lambda x: x[1]["alert_count"], reverse=True)
    for rule_id, stats in sorted_rules[:5]:
        print(f"    {stats['name']}: {stats['alert_count']} alerts")
    
    return alerts, rule_stats


if __name__ == "__main__":
    generate_rules_output()
