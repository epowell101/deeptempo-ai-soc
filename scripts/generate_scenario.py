#!/usr/bin/env python3
"""
Generate a realistic attack scenario with ground truth labels.

This script creates:
1. Raw flow logs (Zeek conn.log format)
2. Raw DNS logs (Zeek dns.log format)
3. Ground truth labels for evaluation
4. Both detectable AND signature-evading attack patterns
5. FALSE POSITIVE traffic - benign activity that triggers rules

The scenario demonstrates:
- Rules generate many false positives on normal business activity
- LogLM's behavioral analysis avoids these false positives
- Evasive attacks bypass rules but are caught by LogLM
"""

import json
import random
import uuid
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Configuration
SCENARIO_DIR = Path(__file__).parent.parent / "data" / "scenarios" / "default_attack"
TOTAL_BENIGN_EVENTS = 4873
BASE_TIME = datetime(2026, 1, 9, 0, 0, 0)

# Network topology
INTERNAL_HOSTS = [
    {"ip": "10.0.1.42", "hostname": "workstation-042", "user": "jsmith", "type": "workstation"},
    {"ip": "10.0.1.55", "hostname": "workstation-055", "user": "tjohnson", "type": "workstation"},
    {"ip": "10.0.1.78", "hostname": "workstation-078", "user": "mwilson", "type": "workstation"},
    {"ip": "10.0.1.103", "hostname": "laptop-sales-03", "user": "klee", "type": "laptop"},
    {"ip": "10.0.2.10", "hostname": "server-db-01", "user": "svc_db", "type": "server"},
    {"ip": "10.0.2.20", "hostname": "server-web-02", "user": "svc_web", "type": "server"},
    {"ip": "10.0.2.30", "hostname": "server-file-01", "user": "svc_file", "type": "server"},
]

# Workstations only
WORKSTATIONS = [h for h in INTERNAL_HOSTS if h["type"] == "workstation"]
SERVERS = [h for h in INTERNAL_HOSTS if h["type"] == "server"]

EXTERNAL_BENIGN = [
    "8.8.8.8", "8.8.4.4", "1.1.1.1",  # DNS
    "142.250.80.46", "142.250.80.78",  # Google
    "157.240.1.35", "157.240.1.63",    # Meta
    "52.94.236.248", "54.239.28.85",   # AWS
    "13.107.42.14", "20.190.151.68",   # Microsoft
]

# Legitimate cloud infrastructure (used for evasion)
LEGITIMATE_CLOUD_IPS = [
    "13.225.78.45",   # AWS CloudFront
    "104.18.32.68",   # Cloudflare
    "151.101.1.140",  # Fastly
    "52.84.150.23",   # AWS CloudFront
    "172.67.182.31",  # Cloudflare
]

# NEW: External IPs that are benign but NOT in whitelist (will trigger rules)
EXTERNAL_RARE_BUT_BENIGN = [
    "185.199.108.153",  # GitHub Pages
    "104.244.42.65",    # Twitter
    "199.232.69.194",   # Verizon Media CDN
    "23.185.0.2",       # Akamai
    "192.0.78.24",      # Automattic (WordPress)
    "151.101.65.69",    # Reddit
    "198.252.206.25",   # Stack Overflow
    "140.82.113.3",     # GitHub
    "35.186.224.25",    # Google Cloud
    "34.117.59.81",     # Google Cloud
]

# Attack infrastructure
C2_SERVER = "203.0.113.50"
ATTACKER_IPS = ["198.51.100.10", "198.51.100.25"]
EXFIL_DOMAINS = ["data-sync.org", "cdn-update.net", "api-metrics.io"]

# Evasive C2 domains (look legitimate)
EVASIVE_C2_DOMAINS = [
    "status.software-update.net",
    "telemetry.app-analytics.io", 
    "cdn.content-delivery.net",
    "api.cloud-services.org",
]

# Attack timeline (phases with timestamps)
ATTACK_PHASES = [
    {
        "phase": 1,
        "name": "Initial Compromise",
        "start_offset_hours": 2.13,
        "techniques": ["T1078"],
        "description": "Credential theft and initial access"
    },
    {
        "phase": 2,
        "name": "C2 Establishment", 
        "start_offset_hours": 2.13,
        "end_offset_hours": 2.2,
        "techniques": ["T1071.001", "T1573.001", "T1071.004"],
        "description": "Command and control channel setup"
    },
    {
        "phase": 3,
        "name": "Lateral Movement",
        "start_offset_hours": 2.2,
        "end_offset_hours": 10.68,
        "techniques": ["T1021.001", "T1021.002"],
        "description": "Spreading through the network"
    },
    {
        "phase": 4,
        "name": "Data Access & Exfiltration",
        "start_offset_hours": 2.67,
        "end_offset_hours": 6.27,
        "techniques": ["T1048.003", "T1041"],
        "description": "Accessing and stealing sensitive data"
    },
    {
        "phase": 5,
        "name": "Persistence & Continued Access",
        "start_offset_hours": 4.28,
        "end_offset_hours": 18.33,
        "techniques": ["T1190", "T1133"],
        "description": "Maintaining access and continued exploitation"
    },
    # Evasive attack phases
    {
        "phase": 6,
        "name": "Low-and-Slow C2 (Evasive)",
        "start_offset_hours": 1.0,
        "end_offset_hours": 20.0,
        "techniques": ["T1071.001", "T1071.004"],
        "description": "Slow C2 beaconing that evades threshold-based rules",
        "evasive": True
    },
    {
        "phase": 7,
        "name": "Staged Exfiltration (Evasive)",
        "start_offset_hours": 8.0,
        "end_offset_hours": 20.0,
        "techniques": ["T1048.001", "T1041"],
        "description": "Slow data exfiltration under detection thresholds",
        "evasive": True
    },
    {
        "phase": 8,
        "name": "Living-off-the-Land Lateral Movement (Evasive)",
        "start_offset_hours": 6.0,
        "end_offset_hours": 16.0,
        "techniques": ["T1047", "T1021.006"],
        "description": "Lateral movement using WMI and legitimate tools",
        "evasive": True
    }
]


def generate_uid() -> str:
    """Generate a Zeek-style UID."""
    return f"C{uuid.uuid4().hex[:15]}"


def generate_benign_conn_log(timestamp: datetime, idx: int) -> Dict[str, Any]:
    """Generate a benign connection log entry."""
    src_host = random.choice(INTERNAL_HOSTS)
    
    conn_type = random.choices(
        ["dns", "https", "http", "internal"],
        weights=[30, 40, 10, 20]
    )[0]
    
    if conn_type == "dns":
        dst_ip = random.choice(["8.8.8.8", "8.8.4.4", "1.1.1.1"])
        dst_port = 53
        proto = "udp"
        service = "dns"
        duration = random.uniform(0.001, 0.1)
        bytes_sent = random.randint(40, 100)
        bytes_recv = random.randint(100, 500)
    elif conn_type == "https":
        dst_ip = random.choice(EXTERNAL_BENIGN + LEGITIMATE_CLOUD_IPS)
        dst_port = 443
        proto = "tcp"
        service = "ssl"
        duration = random.uniform(0.5, 30)
        bytes_sent = random.randint(500, 50000)
        bytes_recv = random.randint(1000, 500000)
    elif conn_type == "http":
        dst_ip = random.choice(EXTERNAL_BENIGN)
        dst_port = 80
        proto = "tcp"
        service = "http"
        duration = random.uniform(0.1, 5)
        bytes_sent = random.randint(200, 5000)
        bytes_recv = random.randint(500, 100000)
    else:  # internal
        other_hosts = [h for h in INTERNAL_HOSTS if h["ip"] != src_host["ip"]]
        dst_host = random.choice(other_hosts)
        dst_ip = dst_host["ip"]
        dst_port = random.choice([445, 139, 135, 389, 88])
        proto = "tcp"
        service = random.choice(["smb", "dce_rpc", "ldap", "kerberos"])
        duration = random.uniform(0.01, 2)
        bytes_sent = random.randint(100, 10000)
        bytes_recv = random.randint(100, 10000)
    
    return {
        "id": f"conn_{idx:05d}",
        "ts": timestamp.isoformat(),
        "uid": generate_uid(),
        "id.orig_h": src_host["ip"],
        "id.orig_p": random.randint(49152, 65535),
        "id.resp_h": dst_ip,
        "id.resp_p": dst_port,
        "proto": proto,
        "service": service,
        "duration": round(duration, 6),
        "orig_bytes": bytes_sent,
        "resp_bytes": bytes_recv,
        "conn_state": "SF",
        "hostname": src_host["hostname"],
        "user": src_host["user"]
    }


def generate_benign_dns_log(timestamp: datetime, idx: int) -> Dict[str, Any]:
    """Generate a benign DNS log entry."""
    src_host = random.choice(INTERNAL_HOSTS)
    
    domains = [
        "google.com", "www.google.com", "mail.google.com",
        "microsoft.com", "login.microsoftonline.com",
        "github.com", "api.github.com",
        "slack.com", "app.slack.com",
        "zoom.us", "us02web.zoom.us",
        "salesforce.com", "login.salesforce.com",
        "aws.amazon.com", "s3.amazonaws.com",
    ]
    
    query = random.choice(domains)
    qtype = random.choice(["A", "AAAA", "A"])
    
    return {
        "id": f"dns_{idx:05d}",
        "ts": timestamp.isoformat(),
        "uid": generate_uid(),
        "id.orig_h": src_host["ip"],
        "id.orig_p": random.randint(49152, 65535),
        "id.resp_h": "8.8.8.8",
        "id.resp_p": 53,
        "proto": "udp",
        "query": query,
        "qtype": qtype,
        "rcode": 0,
        "rcode_name": "NOERROR",
        "hostname": src_host["hostname"],
        "user": src_host["user"]
    }


def generate_false_positive_traffic(event_idx: int, ground_truth: Dict) -> tuple[List[Dict], List[Dict], int]:
    """
    Generate BENIGN traffic that will trigger rules (false positives).
    
    This simulates real-world scenarios where legitimate business activity
    triggers security rules, creating alert fatigue.
    """
    conn_events = []
    dns_events = []
    
    print("Generating false positive traffic (benign but triggers rules)...")
    
    # ============================================================
    # FP Type 1: Connections to rare but legitimate external IPs
    # Triggers: rule_001 (Outbound Connection to Rare External IP)
    # ============================================================
    print("  - Legitimate connections to rare external IPs...")
    for i in range(80):  # 80 connections to non-whitelisted IPs
        timestamp = BASE_TIME + timedelta(
            hours=random.uniform(0, 20),
            minutes=random.randint(0, 59)
        )
        src_host = random.choice(WORKSTATIONS)
        dst_ip = random.choice(EXTERNAL_RARE_BUT_BENIGN)
        
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": timestamp.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": src_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": dst_ip,
            "id.resp_p": 443,
            "proto": "tcp",
            "service": "ssl",
            "duration": round(random.uniform(1, 60), 3),
            "orig_bytes": random.randint(1000, 100000),
            "resp_bytes": random.randint(5000, 500000),
            "conn_state": "SF",
            "hostname": src_host["hostname"],
            "user": src_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "benign",
            "false_positive_type": "rare_external_ip",
            "description": f"Legitimate connection to {dst_ip} (GitHub/Reddit/etc)"
        }
        event_idx += 1
    
    # ============================================================
    # FP Type 2: Workstation to server connections (IT admin work)
    # Triggers: rule_010 (Workstation to Server Direct Connection)
    # ============================================================
    print("  - IT admin workstation to server connections...")
    for i in range(150):  # IT admins connecting to servers
        timestamp = BASE_TIME + timedelta(
            hours=random.uniform(8, 18),  # Business hours
            minutes=random.randint(0, 59)
        )
        src_host = random.choice(WORKSTATIONS)
        dst_host = random.choice(SERVERS)
        
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": timestamp.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": src_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": dst_host["ip"],
            "id.resp_p": random.choice([22, 3389, 5985, 445]),
            "proto": "tcp",
            "service": random.choice(["ssh", "rdp", "winrm", "smb"]),
            "duration": round(random.uniform(10, 3600), 3),  # Long sessions
            "orig_bytes": random.randint(5000, 500000),
            "resp_bytes": random.randint(10000, 1000000),
            "conn_state": "SF",
            "hostname": src_host["hostname"],
            "user": src_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "benign",
            "false_positive_type": "admin_activity",
            "description": f"IT admin {src_host['user']} managing {dst_host['hostname']}"
        }
        event_idx += 1
    
    # ============================================================
    # FP Type 3: Internal SMB connections (file sharing)
    # Triggers: rule_005 (Internal SMB Connection)
    # ============================================================
    print("  - Normal SMB file sharing...")
    for i in range(200):  # Normal file sharing
        timestamp = BASE_TIME + timedelta(
            hours=random.uniform(0, 20),
            minutes=random.randint(0, 59)
        )
        src_host = random.choice(INTERNAL_HOSTS)
        other_hosts = [h for h in INTERNAL_HOSTS if h["ip"] != src_host["ip"]]
        dst_host = random.choice(other_hosts)
        
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": timestamp.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": src_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": dst_host["ip"],
            "id.resp_p": 445,
            "proto": "tcp",
            "service": "smb",
            "duration": round(random.uniform(0.1, 30), 3),
            "orig_bytes": random.randint(500, 50000),
            "resp_bytes": random.randint(1000, 500000),
            "conn_state": "SF",
            "hostname": src_host["hostname"],
            "user": src_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "benign",
            "false_positive_type": "file_sharing",
            "description": f"Normal file sharing between {src_host['hostname']} and {dst_host['hostname']}"
        }
        event_idx += 1
    
    # ============================================================
    # FP Type 4: Large file uploads (cloud backup, video calls)
    # Triggers: rule_006 (Large Outbound Data Transfer)
    # ============================================================
    print("  - Large legitimate file uploads...")
    for i in range(30):  # Cloud backups, video uploads
        timestamp = BASE_TIME + timedelta(
            hours=random.uniform(0, 20),
            minutes=random.randint(0, 59)
        )
        src_host = random.choice(WORKSTATIONS)
        dst_ip = random.choice(EXTERNAL_BENIGN + EXTERNAL_RARE_BUT_BENIGN)
        
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": timestamp.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": src_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": dst_ip,
            "id.resp_p": 443,
            "proto": "tcp",
            "service": "ssl",
            "duration": round(random.uniform(30, 300), 3),
            "orig_bytes": random.randint(600000, 5000000),  # 600KB - 5MB
            "resp_bytes": random.randint(10000, 100000),
            "conn_state": "SF",
            "hostname": src_host["hostname"],
            "user": src_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "benign",
            "false_positive_type": "large_upload",
            "description": f"Cloud backup or video upload from {src_host['hostname']}"
        }
        event_idx += 1
    
    # ============================================================
    # FP Type 5: Short SSL connections (API calls, health checks)
    # Triggers: rule_008 (Periodic Beaconing Pattern)
    # ============================================================
    print("  - Short SSL connections (API calls)...")
    for i in range(100):  # API health checks, telemetry
        timestamp = BASE_TIME + timedelta(
            hours=random.uniform(0, 20),
            minutes=random.randint(0, 59)
        )
        src_host = random.choice(INTERNAL_HOSTS)
        dst_ip = random.choice(EXTERNAL_RARE_BUT_BENIGN)
        
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": timestamp.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": src_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": dst_ip,
            "id.resp_p": 443,
            "proto": "tcp",
            "service": "ssl",
            "duration": round(random.uniform(0.1, 3), 3),  # Short duration
            "orig_bytes": random.randint(100, 800),  # Small payload
            "resp_bytes": random.randint(200, 2000),
            "conn_state": "SF",
            "hostname": src_host["hostname"],
            "user": src_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "benign",
            "false_positive_type": "api_call",
            "description": f"API health check or telemetry from {src_host['hostname']}"
        }
        event_idx += 1
    
    # ============================================================
    # FP Type 6: External web traffic to internal web server
    # Triggers: rule_011 (External Connection to Web Server)
    # ============================================================
    print("  - Legitimate external web traffic...")
    for i in range(50):  # Legitimate customers/partners
        timestamp = BASE_TIME + timedelta(
            hours=random.uniform(0, 20),
            minutes=random.randint(0, 59)
        )
        # External IPs (simulated customers)
        external_ip = f"{random.randint(50, 200)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": timestamp.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": external_ip,
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": "10.0.2.20",  # Web server
            "id.resp_p": random.choice([80, 443]),
            "proto": "tcp",
            "service": random.choice(["http", "ssl"]),
            "duration": round(random.uniform(0.5, 30), 3),
            "orig_bytes": random.randint(500, 5000),
            "resp_bytes": random.randint(5000, 500000),
            "conn_state": "SF",
            "hostname": "external",
            "user": "external"
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "benign",
            "false_positive_type": "web_traffic",
            "description": f"Legitimate web traffic from {external_ip}"
        }
        event_idx += 1
    
    # ============================================================
    # FP Type 7: DNS queries with long subdomains (CDN, SaaS)
    # Triggers: rule_002 (Suspicious DNS Query - Long Subdomain)
    # ============================================================
    print("  - DNS queries with long subdomains (CDN/SaaS)...")
    long_subdomain_domains = [
        "us-east-1-prod-api-gateway.amazonaws.com",
        "login-us-west-2-prod.microsoftonline.com",
        "api-v2-production-cluster.salesforce.com",
        "cdn-static-assets-prod-us.cloudflare.com",
        "telemetry-collector-v3-prod.datadog.com",
        "auth-service-production-v2.okta.com",
    ]
    
    for i in range(25):
        timestamp = BASE_TIME + timedelta(
            hours=random.uniform(0, 20),
            minutes=random.randint(0, 59)
        )
        src_host = random.choice(INTERNAL_HOSTS)
        query = random.choice(long_subdomain_domains)
        
        event = {
            "id": f"dns_{event_idx:05d}",
            "ts": timestamp.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": src_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": "8.8.8.8",
            "id.resp_p": 53,
            "proto": "udp",
            "query": query,
            "qtype": "A",
            "rcode": 0,
            "rcode_name": "NOERROR",
            "hostname": src_host["hostname"],
            "user": src_host["user"]
        }
        dns_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "benign",
            "false_positive_type": "long_subdomain",
            "description": f"Legitimate CDN/SaaS query: {query}"
        }
        event_idx += 1
    
    # ============================================================
    # FP Type 8: TXT record queries (SPF, DKIM, verification)
    # Triggers: rule_003 (Suspicious DNS Query - TXT Record)
    # ============================================================
    print("  - TXT record queries (email verification)...")
    txt_domains = [
        "google.com", "microsoft.com", "salesforce.com",
        "_dmarc.company.com", "_spf.google.com",
    ]
    
    for i in range(15):
        timestamp = BASE_TIME + timedelta(
            hours=random.uniform(0, 20),
            minutes=random.randint(0, 59)
        )
        src_host = random.choice(INTERNAL_HOSTS)
        query = random.choice(txt_domains)
        
        event = {
            "id": f"dns_{event_idx:05d}",
            "ts": timestamp.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": src_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": "8.8.8.8",
            "id.resp_p": 53,
            "proto": "udp",
            "query": query,
            "qtype": "TXT",
            "rcode": 0,
            "rcode_name": "NOERROR",
            "hostname": src_host["hostname"],
            "user": src_host["user"]
        }
        dns_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "benign",
            "false_positive_type": "txt_query",
            "description": f"Email verification TXT query for {query}"
        }
        event_idx += 1
    
    # ============================================================
    # FP Type 9: Failed connections (network issues)
    # Triggers: rule_012 (Failed Connection Attempt)
    # ============================================================
    print("  - Failed connections (network issues)...")
    for i in range(40):
        timestamp = BASE_TIME + timedelta(
            hours=random.uniform(0, 20),
            minutes=random.randint(0, 59)
        )
        src_host = random.choice(INTERNAL_HOSTS)
        dst_ip = random.choice(EXTERNAL_BENIGN + EXTERNAL_RARE_BUT_BENIGN)
        
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": timestamp.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": src_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": dst_ip,
            "id.resp_p": random.choice([80, 443, 22]),
            "proto": "tcp",
            "service": "-",
            "duration": 0,
            "orig_bytes": 0,
            "resp_bytes": 0,
            "conn_state": random.choice(["REJ", "RSTO", "S0"]),
            "hostname": src_host["hostname"],
            "user": src_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "benign",
            "false_positive_type": "network_issue",
            "description": f"Network timeout or service unavailable"
        }
        event_idx += 1
    
    fp_count = len(conn_events) + len(dns_events)
    print(f"  Generated {fp_count} false positive events")
    
    return conn_events, dns_events, event_idx


def generate_detectable_attacks(event_idx: int, ground_truth: Dict) -> tuple[List[Dict], List[Dict], int]:
    """
    Generate attack traffic that WILL be detected by rules.
    These are the "obvious" attacks that both rules and LogLM catch.
    """
    conn_events = []
    dns_events = []
    
    compromised_host = INTERNAL_HOSTS[0]  # workstation-042
    
    # Phase 1: Initial Compromise (02:08)
    phase1_time = BASE_TIME + timedelta(hours=2, minutes=8)
    
    event = {
        "id": f"conn_{event_idx:05d}",
        "ts": phase1_time.isoformat(),
        "uid": generate_uid(),
        "id.orig_h": compromised_host["ip"],
        "id.orig_p": random.randint(49152, 65535),
        "id.resp_h": "10.0.2.30",
        "id.resp_p": 88,
        "proto": "tcp",
        "service": "kerberos",
        "duration": 0.5,
        "orig_bytes": 1500,
        "resp_bytes": 2000,
        "conn_state": "SF",
        "hostname": compromised_host["hostname"],
        "user": compromised_host["user"]
    }
    conn_events.append(event)
    ground_truth["events"][event["id"]] = {
        "label": "malicious",
        "attack_phase": 1,
        "technique": "T1078",
        "description": "Credential abuse - initial access",
        "evasive": False
    }
    ground_truth["incidents"][0]["event_ids"].append(event["id"])
    event_idx += 1
    
    # Phase 2: C2 Establishment - OBVIOUS beaconing (short intervals)
    for i in range(15):
        beacon_time = phase1_time + timedelta(seconds=i * 15 + random.randint(-2, 2))
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": beacon_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": compromised_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": C2_SERVER,
            "id.resp_p": 443,
            "proto": "tcp",
            "service": "ssl",
            "duration": round(random.uniform(0.5, 2), 3),
            "orig_bytes": random.randint(200, 500),
            "resp_bytes": random.randint(500, 2000),
            "conn_state": "SF",
            "hostname": compromised_host["hostname"],
            "user": compromised_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 2,
            "technique": "T1071.001",
            "description": "C2 beaconing",
            "evasive": False
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # DNS tunneling with OBVIOUS long subdomains
    for i in range(5):
        dns_time = phase1_time + timedelta(minutes=i * 2)
        long_subdomain = ''.join(random.choices('abcdef0123456789', k=40))
        event = {
            "id": f"dns_{event_idx:05d}",
            "ts": dns_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": compromised_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": "8.8.8.8",
            "id.resp_p": 53,
            "proto": "udp",
            "query": f"{long_subdomain}.data-sync.org",
            "qtype": "TXT",
            "rcode": 0,
            "rcode_name": "NOERROR",
            "hostname": compromised_host["hostname"],
            "user": compromised_host["user"]
        }
        dns_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 2,
            "technique": "T1071.004",
            "description": "DNS tunneling",
            "evasive": False
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # Phase 3: Lateral Movement - RDP and SMB
    phase3_time = phase1_time + timedelta(minutes=10)
    targets = [INTERNAL_HOSTS[4], INTERNAL_HOSTS[5]]  # Servers
    
    for i, target in enumerate(targets):
        lat_time = phase3_time + timedelta(minutes=i * 30)
        
        # RDP connection
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": lat_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": compromised_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": target["ip"],
            "id.resp_p": 3389,
            "proto": "tcp",
            "service": "rdp",
            "duration": round(random.uniform(300, 1800), 3),
            "orig_bytes": random.randint(50000, 200000),
            "resp_bytes": random.randint(100000, 500000),
            "conn_state": "SF",
            "hostname": compromised_host["hostname"],
            "user": compromised_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 3,
            "technique": "T1021.001",
            "description": f"RDP lateral movement to {target['hostname']}",
            "evasive": False
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # Phase 4: Data Exfiltration - LARGE transfer
    phase4_time = phase1_time + timedelta(hours=1)
    
    event = {
        "id": f"conn_{event_idx:05d}",
        "ts": phase4_time.isoformat(),
        "uid": generate_uid(),
        "id.orig_h": compromised_host["ip"],
        "id.orig_p": random.randint(49152, 65535),
        "id.resp_h": C2_SERVER,
        "id.resp_p": 443,
        "proto": "tcp",
        "service": "ssl",
        "duration": 120.5,
        "orig_bytes": 15000000,  # 15MB - obvious exfiltration
        "resp_bytes": 50000,
        "conn_state": "SF",
        "hostname": compromised_host["hostname"],
        "user": compromised_host["user"]
    }
    conn_events.append(event)
    ground_truth["events"][event["id"]] = {
        "label": "malicious",
        "attack_phase": 4,
        "technique": "T1041",
        "description": "Large data exfiltration",
        "evasive": False
    }
    ground_truth["incidents"][0]["event_ids"].append(event["id"])
    event_idx += 1
    
    # Phase 5: Persistence - Web shell access
    phase5_time = BASE_TIME + timedelta(hours=4, minutes=17)
    
    for i in range(10):
        shell_time = phase5_time + timedelta(hours=i * 1.5)
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": shell_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": random.choice(ATTACKER_IPS),
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": "10.0.2.20",
            "id.resp_p": 443,
            "proto": "tcp",
            "service": "ssl",
            "duration": round(random.uniform(5, 60), 3),
            "orig_bytes": random.randint(500, 5000),
            "resp_bytes": random.randint(1000, 50000),
            "conn_state": "SF",
            "hostname": "external",
            "user": "attacker"
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 5,
            "technique": "T1190",
            "description": "Web shell access",
            "evasive": False
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    return conn_events, dns_events, event_idx


def generate_evasive_attacks(event_idx: int, ground_truth: Dict) -> tuple[List[Dict], List[Dict], int]:
    """
    Generate signature-evading attack traffic.
    These attacks bypass traditional rules but are caught by LogLM.
    """
    conn_events = []
    dns_events = []
    
    compromised_host = INTERNAL_HOSTS[0]  # workstation-042
    
    print("Generating signature-evading attack traffic...")
    
    # ============================================================
    # EVASIVE Phase 6: Low-and-Slow DNS C2
    # Evades: Long subdomain rule, TXT record rule
    # ============================================================
    print("  Generating Phase 6: Low-and-Slow DNS C2...")
    phase6_events = []
    
    for i in range(40):  # 40 queries over 19 hours = very slow
        dns_time = BASE_TIME + timedelta(hours=1 + i * 0.475)  # ~28 min intervals
        
        # Short subdomain (under 20 chars) - evades length rule
        short_subdomain = ''.join(random.choices('abcdef0123456789', k=random.randint(8, 15)))
        domain = random.choice(EVASIVE_C2_DOMAINS)
        
        event = {
            "id": f"dns_{event_idx:05d}",
            "ts": dns_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": compromised_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": "8.8.8.8",
            "id.resp_p": 53,
            "proto": "udp",
            "query": f"{short_subdomain}.{domain}",
            "qtype": "A",  # A record, not TXT - evades TXT rule
            "rcode": 0,
            "rcode_name": "NOERROR",
            "hostname": compromised_host["hostname"],
            "user": compromised_host["user"]
        }
        dns_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 6,
            "technique": "T1071.004",
            "description": "Low-and-slow DNS C2 (short subdomain, A record)",
            "evasive": True,
            "evasion_technique": "Short subdomain + A record + low volume"
        }
        phase6_events.append(event["id"])
        event_idx += 1
    
    ground_truth["attack_timeline"].append({
        "phase": 6,
        "name": "Low-and-Slow C2 (Evasive)",
        "start_time": (BASE_TIME + timedelta(hours=1)).isoformat(),
        "event_ids": phase6_events,
        "evasive": True
    })
    
    # ============================================================
    # EVASIVE Phase 6b: HTTPS C2 via legitimate infrastructure
    # Evades: Rare IP rule (uses CDN IPs), beaconing rule (jitter)
    # ============================================================
    print("  Generating Phase 6: HTTPS C2 via legitimate infrastructure...")
    
    for i in range(30):  # 30 connections over 19 hours
        c2_time = BASE_TIME + timedelta(
            hours=1 + random.uniform(0, 19),
            minutes=random.randint(0, 59)
        )
        
        # Use legitimate cloud IPs (whitelisted)
        dst_ip = random.choice(LEGITIMATE_CLOUD_IPS)
        
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": c2_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": compromised_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": dst_ip,
            "id.resp_p": 443,
            "proto": "tcp",
            "service": "ssl",
            "duration": round(random.uniform(5, 120), 3),  # Varied duration
            "orig_bytes": random.randint(500, 5000),
            "resp_bytes": random.randint(1000, 20000),
            "conn_state": "SF",
            "hostname": compromised_host["hostname"],
            "user": compromised_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 6,
            "technique": "T1071.001",
            "description": f"C2 via legitimate CDN ({dst_ip})",
            "evasive": True,
            "evasion_technique": "Legitimate CDN IP + varied timing + long duration"
        }
        phase6_events.append(event["id"])
        event_idx += 1
    
    # ============================================================
    # EVASIVE Phase 7: Staged data exfiltration
    # Evades: Large transfer rule (chunks < 500KB)
    # ============================================================
    print("  Generating Phase 7: Staged data exfiltration...")
    phase7_events = []
    
    total_exfil = 0
    for i in range(50):  # 50 small transfers
        exfil_time = BASE_TIME + timedelta(hours=8 + i * 0.24)  # ~14 min intervals
        
        # Small chunks under threshold
        chunk_size = random.randint(50000, 200000)  # 50-200KB
        total_exfil += chunk_size
        
        dst_ip = random.choice(LEGITIMATE_CLOUD_IPS)
        
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": exfil_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": compromised_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": dst_ip,
            "id.resp_p": 443,
            "proto": "tcp",
            "service": "ssl",
            "duration": round(random.uniform(10, 60), 3),
            "orig_bytes": chunk_size,
            "resp_bytes": random.randint(1000, 5000),
            "conn_state": "SF",
            "hostname": compromised_host["hostname"],
            "user": compromised_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 7,
            "technique": "T1048.001",
            "description": f"Staged exfiltration ({chunk_size/1000:.0f}KB chunk)",
            "evasive": True,
            "evasion_technique": "Small chunks + legitimate cloud IP"
        }
        phase7_events.append(event["id"])
        event_idx += 1
    
    print(f"    Total evasive exfiltration: {total_exfil/1000000:.1f}MB in small chunks")
    
    ground_truth["attack_timeline"].append({
        "phase": 7,
        "name": "Staged Exfiltration (Evasive)",
        "start_time": (BASE_TIME + timedelta(hours=8)).isoformat(),
        "event_ids": phase7_events,
        "evasive": True
    })
    
    # ============================================================
    # EVASIVE Phase 8: Living-off-the-Land lateral movement
    # Evades: RDP/SMB rules (uses WMI/WinRM on different ports)
    # ============================================================
    print("  Generating Phase 8: Living-off-the-Land lateral movement...")
    phase8_events = []
    
    targets = [INTERNAL_HOSTS[4], INTERNAL_HOSTS[5], INTERNAL_HOSTS[6]]
    
    for target in targets:
        for i in range(5):  # Multiple sessions per target
            lat_time = BASE_TIME + timedelta(hours=6 + i * 2 + random.uniform(0, 1))
            
            # WMI (port 135) or WinRM (5985/5986) - not RDP/SMB
            port = random.choice([135, 5985, 5986])
            service = "wmi" if port == 135 else "winrm"
            
            event = {
                "id": f"conn_{event_idx:05d}",
                "ts": lat_time.isoformat(),
                "uid": generate_uid(),
                "id.orig_h": compromised_host["ip"],
                "id.orig_p": random.randint(49152, 65535),
                "id.resp_h": target["ip"],
                "id.resp_p": port,
                "proto": "tcp",
                "service": service,
                "duration": round(random.uniform(1, 30), 3),
                "orig_bytes": random.randint(1000, 10000),
                "resp_bytes": random.randint(2000, 20000),
                "conn_state": "SF",
                "hostname": compromised_host["hostname"],
                "user": compromised_host["user"]
            }
            conn_events.append(event)
            ground_truth["events"][event["id"]] = {
                "label": "malicious",
                "attack_phase": 8,
                "technique": "T1047" if port == 135 else "T1021.006",
                "description": f"{service.upper()} lateral movement to {target['hostname']}",
                "evasive": True,
                "evasion_technique": f"{service.upper()} instead of RDP/SMB + slow timing"
            }
            phase8_events.append(event["id"])
            event_idx += 1
    
    ground_truth["attack_timeline"].append({
        "phase": 8,
        "name": "Living-off-the-Land Lateral Movement (Evasive)",
        "start_time": (BASE_TIME + timedelta(hours=6)).isoformat(),
        "event_ids": phase8_events,
        "evasive": True
    })
    
    return conn_events, dns_events, event_idx


def generate_scenario():
    """Generate the complete attack scenario."""
    print("=" * 60)
    print("Generating Attack Scenario with Evasive Patterns")
    print("=" * 60)
    
    # Initialize ground truth
    ground_truth = {
        "events": {},
        "incidents": [
            {
                "id": "INC-001",
                "name": "Multi-Stage Attack",
                "severity": "critical",
                "event_ids": []
            }
        ],
        "attack_timeline": []
    }
    
    # Add standard attack phases to timeline
    for phase in ATTACK_PHASES[:5]:  # Non-evasive phases
        ground_truth["attack_timeline"].append({
            "phase": phase["phase"],
            "name": phase["name"],
            "start_time": (BASE_TIME + timedelta(hours=phase["start_offset_hours"])).isoformat(),
            "event_ids": [],
            "evasive": False
        })
    
    all_conn_events = []
    all_dns_events = []
    event_idx = 0
    
    # Generate benign traffic
    print("Generating benign traffic...")
    conn_count = int(TOTAL_BENIGN_EVENTS * 0.7)
    dns_count = TOTAL_BENIGN_EVENTS - conn_count
    
    for i in range(conn_count):
        timestamp = BASE_TIME + timedelta(
            hours=random.uniform(0, 20),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        event = generate_benign_conn_log(timestamp, event_idx)
        all_conn_events.append(event)
        ground_truth["events"][event["id"]] = {"label": "benign"}
        event_idx += 1
    
    print(f"  Generated {conn_count} benign connection events")
    
    for i in range(dns_count):
        timestamp = BASE_TIME + timedelta(
            hours=random.uniform(0, 20),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        event = generate_benign_dns_log(timestamp, event_idx)
        all_dns_events.append(event)
        ground_truth["events"][event["id"]] = {"label": "benign"}
        event_idx += 1
    
    print(f"  Generated {dns_count} benign DNS events")
    
    # Generate FALSE POSITIVE traffic
    fp_conn, fp_dns, event_idx = generate_false_positive_traffic(event_idx, ground_truth)
    all_conn_events.extend(fp_conn)
    all_dns_events.extend(fp_dns)
    
    # Generate attack traffic
    print("Generating attack traffic...")
    
    # Detectable attacks
    print("Generating detectable attack traffic...")
    attack_conn, attack_dns, event_idx = generate_detectable_attacks(event_idx, ground_truth)
    all_conn_events.extend(attack_conn)
    all_dns_events.extend(attack_dns)
    
    # Evasive attacks
    evasive_conn, evasive_dns, event_idx = generate_evasive_attacks(event_idx, ground_truth)
    all_conn_events.extend(evasive_conn)
    all_dns_events.extend(evasive_dns)
    
    # Count events
    malicious_count = sum(1 for e in ground_truth["events"].values() if e.get("label") == "malicious")
    evasive_count = sum(1 for e in ground_truth["events"].values() if e.get("evasive", False))
    detectable_count = malicious_count - evasive_count
    benign_count = sum(1 for e in ground_truth["events"].values() if e.get("label") == "benign")
    fp_count = sum(1 for e in ground_truth["events"].values() if e.get("false_positive_type"))
    
    print(f"  Total malicious events: {malicious_count}")
    print(f"    - Detectable by rules: {detectable_count}")
    print(f"    - Evasive (rules miss): {evasive_count}")
    print(f"  Total benign events: {benign_count}")
    print(f"    - Normal traffic: {benign_count - fp_count}")
    print(f"    - False positive triggers: {fp_count}")
    
    # Get unique evasion techniques
    evasion_techniques = set()
    for e in ground_truth["events"].values():
        if e.get("evasion_technique"):
            evasion_techniques.add(e["evasion_technique"])
    
    print(f"  Evasion techniques: {len(evasion_techniques)}")
    
    # Sort events by timestamp
    all_conn_events.sort(key=lambda x: x["ts"])
    all_dns_events.sort(key=lambda x: x["ts"])
    
    # Save files
    print("Saving raw logs...")
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    (SCENARIO_DIR / "raw_logs").mkdir(exist_ok=True)
    (SCENARIO_DIR / "rules_output").mkdir(exist_ok=True)
    (SCENARIO_DIR / "loglm_output").mkdir(exist_ok=True)
    
    with open(SCENARIO_DIR / "raw_logs" / "zeek_conn.json", "w") as f:
        json.dump(all_conn_events, f, indent=2)
    
    with open(SCENARIO_DIR / "raw_logs" / "zeek_dns.json", "w") as f:
        json.dump(all_dns_events, f, indent=2)
    
    with open(SCENARIO_DIR / "ground_truth.json", "w") as f:
        json.dump(ground_truth, f, indent=2)
    
    # Create manifest
    manifest = {
        "name": "Multi-Stage Attack with Evasive Patterns",
        "description": "APT-style attack with both detectable and signature-evading components, plus realistic false positive traffic",
        "duration_hours": 20,
        "total_events": len(all_conn_events) + len(all_dns_events),
        "malicious_events": malicious_count,
        "detectable_events": detectable_count,
        "evasive_events": evasive_count,
        "benign_events": benign_count,
        "false_positive_triggers": fp_count,
        "evasion_techniques": list(evasion_techniques),
        "attack_phases": 8,
        "log_types": ["zeek_conn", "zeek_dns"],
        "generated_at": datetime.now().isoformat()
    }
    
    with open(SCENARIO_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    print("=" * 60)
    print("Scenario Generation Complete!")
    print("=" * 60)
    print(f"Files saved to: {SCENARIO_DIR}")
    print("Next steps:")
    print("  1. python scripts/rules_detection.py")
    print("  2. python scripts/loglm_detection.py")
    print("  3. python scripts/evaluate.py")
    print("  4. streamlit run streamlit_app/tale_of_two_socs.py")


if __name__ == "__main__":
    generate_scenario()
