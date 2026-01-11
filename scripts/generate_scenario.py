#!/usr/bin/env python3
"""
Generate a realistic attack scenario with ground truth labels.

This script creates:
1. Raw flow logs (Zeek conn.log format)
2. Raw DNS logs (Zeek dns.log format)
3. Ground truth labels for evaluation
4. Both detectable AND signature-evading attack patterns

The scenario includes "low and slow" attacks that evade traditional
signature-based detection but are caught by LogLM's behavioral analysis.
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
    # NEW: Evasive attack phases
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
            "description": "C2 beacon over HTTPS",
            "evasive": False
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # OBVIOUS DNS tunneling - long subdomains, TXT records
    for i in range(10):
        tunnel_time = phase1_time + timedelta(minutes=i, seconds=random.randint(0, 30))
        subdomain = ''.join(random.choices('abcdef0123456789', k=32))  # Long subdomain!
        event = {
            "id": f"dns_{event_idx:05d}",
            "ts": tunnel_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": compromised_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": "8.8.8.8",
            "id.resp_p": 53,
            "proto": "udp",
            "query": f"{subdomain}.{random.choice(EXFIL_DOMAINS)}",
            "qtype": "TXT",  # Suspicious record type!
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
            "description": "DNS tunneling for C2",
            "evasive": False
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # Phase 3: OBVIOUS Lateral Movement - RDP/SMB
    lateral_targets = [INTERNAL_HOSTS[1], INTERNAL_HOSTS[3], INTERNAL_HOSTS[4]]
    phase3_start = BASE_TIME + timedelta(hours=2, minutes=12)
    
    for i, target in enumerate(lateral_targets):
        move_time = phase3_start + timedelta(minutes=i * 15 + random.randint(0, 10))
        proto_choice = random.choice(["rdp", "smb"])
        port = 3389 if proto_choice == "rdp" else 445
        technique = "T1021.001" if proto_choice == "rdp" else "T1021.002"
        
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": move_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": compromised_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": target["ip"],
            "id.resp_p": port,
            "proto": "tcp",
            "service": proto_choice,
            "duration": round(random.uniform(60, 600), 3),
            "orig_bytes": random.randint(10000, 100000),
            "resp_bytes": random.randint(50000, 500000),
            "conn_state": "SF",
            "hostname": compromised_host["hostname"],
            "user": compromised_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 3,
            "technique": technique,
            "description": f"Lateral movement to {target['hostname']}",
            "evasive": False
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # Phase 4: OBVIOUS Data Exfiltration - large transfers
    db_server = INTERNAL_HOSTS[4]
    exfil_times = [
        BASE_TIME + timedelta(hours=2, minutes=40),
        BASE_TIME + timedelta(hours=3, minutes=45),
        BASE_TIME + timedelta(hours=6, minutes=16),
    ]
    
    for exfil_time in exfil_times:
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": exfil_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": db_server["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": C2_SERVER,
            "id.resp_p": 443,
            "proto": "tcp",
            "service": "ssl",
            "duration": round(random.uniform(30, 120), 3),
            "orig_bytes": random.randint(1000000, 10000000),  # Large upload!
            "resp_bytes": random.randint(1000, 5000),
            "conn_state": "SF",
            "hostname": db_server["hostname"],
            "user": db_server["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 4,
            "technique": "T1041",
            "description": "Data exfiltration over C2 channel",
            "evasive": False
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # Phase 5: Web exploitation
    web_server = INTERNAL_HOSTS[5]
    for attacker_ip in ATTACKER_IPS:
        for i in range(10):
            attack_time = BASE_TIME + timedelta(hours=random.uniform(4, 18))
            event = {
                "id": f"conn_{event_idx:05d}",
                "ts": attack_time.isoformat(),
                "uid": generate_uid(),
                "id.orig_h": attacker_ip,
                "id.orig_p": random.randint(49152, 65535),
                "id.resp_h": web_server["ip"],
                "id.resp_p": random.choice([80, 443, 8080]),
                "proto": "tcp",
                "service": random.choice(["http", "ssl"]),
                "duration": round(random.uniform(0.1, 5), 3),
                "orig_bytes": random.randint(500, 5000),
                "resp_bytes": random.randint(200, 50000),
                "conn_state": random.choice(["SF", "REJ", "RSTO"]),
                "hostname": "external",
                "user": "unknown"
            }
            conn_events.append(event)
            ground_truth["events"][event["id"]] = {
                "label": "malicious",
                "attack_phase": 5,
                "technique": "T1190",
                "description": f"Web exploitation attempt from {attacker_ip}",
                "evasive": False
            }
            ground_truth["incidents"][0]["event_ids"].append(event["id"])
            event_idx += 1
    
    return conn_events, dns_events, event_idx


def generate_evasive_attacks(event_idx: int, ground_truth: Dict) -> tuple[List[Dict], List[Dict], int]:
    """
    Generate attack traffic that EVADES rule-based detection.
    These attacks are designed to stay under thresholds and avoid signatures.
    LogLM catches them through behavioral analysis.
    """
    conn_events = []
    dns_events = []
    
    compromised_host = INTERNAL_HOSTS[0]  # workstation-042
    secondary_host = INTERNAL_HOSTS[1]    # workstation-055
    
    # Create a second incident for evasive attacks
    ground_truth["incidents"].append({
        "id": "INC-002",
        "name": "Low-and-Slow APT Campaign (Evasive)",
        "severity": "critical",
        "event_ids": [],
        "techniques": [],
        "evasive": True
    })
    
    # =========================================================================
    # PHASE 6: Low-and-Slow C2 via DNS
    # - Short subdomains (< 20 chars) - evades rule_002
    # - A records, not TXT - evades rule_003
    # - Queries spread over many hours - evades volume thresholds
    # =========================================================================
    print("  Generating Phase 6: Low-and-Slow DNS C2...")
    
    for hour in range(1, 20):
        # 2-4 queries per hour (very slow)
        num_queries = random.randint(2, 4)
        for _ in range(num_queries):
            query_time = BASE_TIME + timedelta(
                hours=hour, 
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            
            # Short subdomain (< 20 chars) - evades long subdomain rule
            subdomain = ''.join(random.choices('abcdefghijklmnop', k=random.randint(8, 15)))
            
            event = {
                "id": f"dns_{event_idx:05d}",
                "ts": query_time.isoformat(),
                "uid": generate_uid(),
                "id.orig_h": compromised_host["ip"],
                "id.orig_p": random.randint(49152, 65535),
                "id.resp_h": "8.8.8.8",
                "id.resp_p": 53,
                "proto": "udp",
                "query": f"{subdomain}.{random.choice(EVASIVE_C2_DOMAINS)}",
                "qtype": "A",  # A record, not TXT - evades rule_003
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
                "description": "Low-and-slow DNS C2 (evasive)",
                "evasive": True,
                "evasion_technique": "Short subdomain + A record + low volume"
            }
            ground_truth["incidents"][1]["event_ids"].append(event["id"])
            event_idx += 1
    
    # =========================================================================
    # PHASE 6 continued: HTTPS C2 via legitimate infrastructure
    # - Uses legitimate cloud IPs (Cloudflare, AWS) - evades IP reputation
    # - Long intervals with jitter - evades beaconing detection
    # - Varied connection duration - evades pattern matching
    # =========================================================================
    print("  Generating Phase 6: HTTPS C2 via legitimate infrastructure...")
    
    for hour in range(2, 20):
        # 1-2 beacons per hour (very slow, with jitter)
        num_beacons = random.randint(1, 2)
        for _ in range(num_beacons):
            beacon_time = BASE_TIME + timedelta(
                hours=hour,
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            
            event = {
                "id": f"conn_{event_idx:05d}",
                "ts": beacon_time.isoformat(),
                "uid": generate_uid(),
                "id.orig_h": compromised_host["ip"],
                "id.orig_p": random.randint(49152, 65535),
                "id.resp_h": random.choice(LEGITIMATE_CLOUD_IPS),  # Legitimate CDN!
                "id.resp_p": 443,
                "proto": "tcp",
                "service": "ssl",
                "duration": round(random.uniform(5, 45), 3),  # Varied duration (not < 5s)
                "orig_bytes": random.randint(300, 800),
                "resp_bytes": random.randint(1000, 5000),
                "conn_state": "SF",
                "hostname": compromised_host["hostname"],
                "user": compromised_host["user"]
            }
            conn_events.append(event)
            ground_truth["events"][event["id"]] = {
                "label": "malicious",
                "attack_phase": 6,
                "technique": "T1071.001",
                "description": "C2 via legitimate cloud infrastructure (evasive)",
                "evasive": True,
                "evasion_technique": "Legitimate CDN IP + varied timing + long duration"
            }
            ground_truth["incidents"][1]["event_ids"].append(event["id"])
            event_idx += 1
    
    # =========================================================================
    # PHASE 7: Staged Data Exfiltration
    # - Small transfers (< 500KB each) - evades rule_006
    # - Uses legitimate cloud storage IPs - evades IP reputation
    # - Spread over 12+ hours - evades volume thresholds
    # =========================================================================
    print("  Generating Phase 7: Staged data exfiltration...")
    
    db_server = INTERNAL_HOSTS[4]
    total_exfil_bytes = 0
    
    for hour in range(8, 20):
        # 3-5 small transfers per hour
        num_transfers = random.randint(3, 5)
        for _ in range(num_transfers):
            transfer_time = BASE_TIME + timedelta(
                hours=hour,
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            
            # Small transfer (< 500KB) - evades large transfer rule
            bytes_out = random.randint(50000, 400000)
            total_exfil_bytes += bytes_out
            
            event = {
                "id": f"conn_{event_idx:05d}",
                "ts": transfer_time.isoformat(),
                "uid": generate_uid(),
                "id.orig_h": db_server["ip"],
                "id.orig_p": random.randint(49152, 65535),
                "id.resp_h": random.choice(LEGITIMATE_CLOUD_IPS),  # Looks like cloud backup
                "id.resp_p": 443,
                "proto": "tcp",
                "service": "ssl",
                "duration": round(random.uniform(2, 15), 3),
                "orig_bytes": bytes_out,
                "resp_bytes": random.randint(500, 2000),
                "conn_state": "SF",
                "hostname": db_server["hostname"],
                "user": db_server["user"]
            }
            conn_events.append(event)
            ground_truth["events"][event["id"]] = {
                "label": "malicious",
                "attack_phase": 7,
                "technique": "T1048.001",
                "description": f"Staged exfiltration chunk ({bytes_out/1000:.0f}KB)",
                "evasive": True,
                "evasion_technique": "Small chunks + legitimate cloud IP"
            }
            ground_truth["incidents"][1]["event_ids"].append(event["id"])
            event_idx += 1
    
    print(f"    Total evasive exfiltration: {total_exfil_bytes/1000000:.1f}MB in small chunks")
    
    # =========================================================================
    # PHASE 8: Living-off-the-Land Lateral Movement
    # - Uses WMI (port 135) instead of RDP/SMB - evades rule_004, rule_005
    # - Single connection per target - no scanning pattern
    # - Hours between moves - evades velocity detection
    # =========================================================================
    print("  Generating Phase 8: Living-off-the-Land lateral movement...")
    
    lateral_targets = [
        INTERNAL_HOSTS[2],  # workstation-078
        INTERNAL_HOSTS[5],  # server-web-02
        INTERNAL_HOSTS[6],  # server-file-01
    ]
    
    for i, target in enumerate(lateral_targets):
        # Hours between each lateral move
        move_time = BASE_TIME + timedelta(hours=6 + i * 3, minutes=random.randint(0, 59))
        
        # WMI connection (not RDP/SMB)
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": move_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": compromised_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": target["ip"],
            "id.resp_p": 135,  # WMI/DCOM - not monitored by RDP/SMB rules
            "proto": "tcp",
            "service": "dce_rpc",
            "duration": round(random.uniform(1, 10), 3),
            "orig_bytes": random.randint(2000, 10000),
            "resp_bytes": random.randint(1000, 5000),
            "conn_state": "SF",
            "hostname": compromised_host["hostname"],
            "user": compromised_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 8,
            "technique": "T1047",
            "description": f"WMI lateral movement to {target['hostname']} (evasive)",
            "evasive": True,
            "evasion_technique": "WMI instead of RDP/SMB + slow timing"
        }
        ground_truth["incidents"][1]["event_ids"].append(event["id"])
        event_idx += 1
        
        # Follow-up WinRM connection (also evades RDP/SMB rules)
        winrm_time = move_time + timedelta(minutes=random.randint(5, 30))
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": winrm_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": compromised_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": target["ip"],
            "id.resp_p": 5985,  # WinRM HTTP
            "proto": "tcp",
            "service": "http",
            "duration": round(random.uniform(30, 300), 3),
            "orig_bytes": random.randint(5000, 50000),
            "resp_bytes": random.randint(10000, 100000),
            "conn_state": "SF",
            "hostname": compromised_host["hostname"],
            "user": compromised_host["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 8,
            "technique": "T1021.006",
            "description": f"WinRM session to {target['hostname']} (evasive)",
            "evasive": True,
            "evasion_technique": "WinRM instead of RDP/SMB"
        }
        ground_truth["incidents"][1]["event_ids"].append(event["id"])
        event_idx += 1
    
    # Collect techniques for evasive incident
    evasive_techniques = set()
    for event_id in ground_truth["incidents"][1]["event_ids"]:
        if event_id in ground_truth["events"]:
            evasive_techniques.add(ground_truth["events"][event_id]["technique"])
    ground_truth["incidents"][1]["techniques"] = list(evasive_techniques)
    
    return conn_events, dns_events, event_idx


def generate_attack_events() -> tuple[List[Dict], List[Dict], Dict]:
    """Generate all attack traffic with ground truth labels."""
    ground_truth = {
        "events": {},
        "attack_timeline": [],
        "incidents": [{
            "id": "INC-001",
            "name": "Multi-stage C2 and Data Exfiltration",
            "severity": "critical",
            "event_ids": [],
            "techniques": []
        }],
        "evasion_summary": {
            "total_evasive_events": 0,
            "evasion_techniques_used": []
        }
    }
    
    event_idx = 5000
    
    # Generate detectable attacks
    print("Generating detectable attack traffic...")
    det_conn, det_dns, event_idx = generate_detectable_attacks(event_idx, ground_truth)
    
    # Generate evasive attacks
    print("Generating signature-evading attack traffic...")
    eva_conn, eva_dns, event_idx = generate_evasive_attacks(event_idx, ground_truth)
    
    # Combine
    conn_events = det_conn + eva_conn
    dns_events = det_dns + eva_dns
    
    # Collect all techniques for first incident
    det_techniques = set()
    for event_id in ground_truth["incidents"][0]["event_ids"]:
        if event_id in ground_truth["events"]:
            det_techniques.add(ground_truth["events"][event_id]["technique"])
    ground_truth["incidents"][0]["techniques"] = list(det_techniques)
    
    # Build attack timeline
    for phase in ATTACK_PHASES:
        phase_events = [
            eid for eid, info in ground_truth["events"].items()
            if info.get("attack_phase") == phase["phase"]
        ]
        if phase_events:
            ground_truth["attack_timeline"].append({
                "phase": phase["phase"],
                "name": phase["name"],
                "start_time": (BASE_TIME + timedelta(hours=phase["start_offset_hours"])).isoformat(),
                "event_ids": phase_events,
                "techniques": phase["techniques"],
                "evasive": phase.get("evasive", False)
            })
    
    # Evasion summary
    evasive_events = [e for e in ground_truth["events"].values() if e.get("evasive")]
    evasion_techniques = list(set(e.get("evasion_technique", "") for e in evasive_events if e.get("evasion_technique")))
    ground_truth["evasion_summary"] = {
        "total_evasive_events": len(evasive_events),
        "evasion_techniques_used": evasion_techniques
    }
    
    return conn_events, dns_events, ground_truth


def generate_scenario():
    """Generate the complete scenario with all data."""
    print("=" * 60)
    print("Generating Attack Scenario with Evasive Patterns")
    print("=" * 60)
    
    # Create directories
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    (SCENARIO_DIR / "raw_logs").mkdir(exist_ok=True)
    (SCENARIO_DIR / "rules_output").mkdir(exist_ok=True)
    (SCENARIO_DIR / "loglm_output").mkdir(exist_ok=True)
    
    # Generate benign traffic
    print("\nGenerating benign traffic...")
    conn_events = []
    dns_events = []
    
    for i in range(TOTAL_BENIGN_EVENTS):
        timestamp = BASE_TIME + timedelta(seconds=random.uniform(0, 72000))
        
        if random.random() < 0.7:
            event = generate_benign_conn_log(timestamp, i)
            conn_events.append(event)
        else:
            event = generate_benign_dns_log(timestamp, i)
            dns_events.append(event)
    
    print(f"  Generated {len(conn_events)} benign connection events")
    print(f"  Generated {len(dns_events)} benign DNS events")
    
    # Generate attack traffic
    print("\nGenerating attack traffic...")
    attack_conn, attack_dns, ground_truth = generate_attack_events()
    
    conn_events.extend(attack_conn)
    dns_events.extend(attack_dns)
    
    # Sort by timestamp
    conn_events.sort(key=lambda x: x["ts"])
    dns_events.sort(key=lambda x: x["ts"])
    
    # Count events
    total_malicious = len([e for e in ground_truth["events"].values() if e["label"] == "malicious"])
    total_evasive = ground_truth["evasion_summary"]["total_evasive_events"]
    total_detectable = total_malicious - total_evasive
    
    print(f"\n  Total malicious events: {total_malicious}")
    print(f"    - Detectable by rules: {total_detectable}")
    print(f"    - Evasive (rules miss): {total_evasive}")
    print(f"  Evasion techniques: {len(ground_truth['evasion_summary']['evasion_techniques_used'])}")
    
    # Save raw logs
    print("\nSaving raw logs...")
    with open(SCENARIO_DIR / "raw_logs" / "zeek_conn.json", "w") as f:
        json.dump(conn_events, f, indent=2)
    
    with open(SCENARIO_DIR / "raw_logs" / "zeek_dns.json", "w") as f:
        json.dump(dns_events, f, indent=2)
    
    # Save ground truth
    with open(SCENARIO_DIR / "ground_truth.json", "w") as f:
        json.dump(ground_truth, f, indent=2)
    
    # Create manifest
    manifest = {
        "name": "Multi-Stage Attack with Evasive Patterns",
        "description": "Attack scenario including both detectable and signature-evading patterns. "
                      "Demonstrates how LogLM catches low-and-slow attacks that evade traditional rules.",
        "log_types": ["zeek_conn", "zeek_dns"],
        "duration_hours": 20,
        "total_events": len(conn_events) + len(dns_events),
        "malicious_events": total_malicious,
        "detectable_events": total_detectable,
        "evasive_events": total_evasive,
        "benign_events": TOTAL_BENIGN_EVENTS,
        "incidents": 2,
        "evasion_techniques": ground_truth["evasion_summary"]["evasion_techniques_used"],
        "created": datetime.now().isoformat(),
        "version": "2.0"
    }
    
    with open(SCENARIO_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    print("\n" + "=" * 60)
    print("Scenario Generation Complete!")
    print("=" * 60)
    print(f"\nFiles saved to: {SCENARIO_DIR}")
    print(f"\nNext steps:")
    print(f"  1. python scripts/rules_detection.py")
    print(f"  2. python scripts/loglm_detection.py")
    print(f"  3. python scripts/evaluate.py")
    print(f"  4. streamlit run streamlit_app/tale_of_two_socs.py")


if __name__ == "__main__":
    generate_scenario()
