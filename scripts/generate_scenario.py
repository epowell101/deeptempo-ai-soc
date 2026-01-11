#!/usr/bin/env python3
"""
Generate a realistic attack scenario with ground truth labels.

This script creates:
1. Raw flow logs (Zeek conn.log format)
2. Raw DNS logs (Zeek dns.log format)
3. Ground truth labels for evaluation
4. Rules-only alerts (Sigma rule matches)
5. LogLM findings (with embeddings and MITRE predictions)
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
ATTACK_EVENTS = 127
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

# Attack infrastructure
C2_SERVER = "203.0.113.50"
ATTACKER_IPS = ["198.51.100.10", "198.51.100.25"]
EXFIL_DOMAINS = ["data-sync.org", "cdn-update.net", "api-metrics.io"]

# Attack timeline (phases with timestamps)
ATTACK_PHASES = [
    {
        "phase": 1,
        "name": "Initial Compromise",
        "start_offset_hours": 2.13,  # 02:08
        "techniques": ["T1078"],
        "description": "Credential theft and initial access"
    },
    {
        "phase": 2,
        "name": "C2 Establishment", 
        "start_offset_hours": 2.13,  # 02:08
        "end_offset_hours": 2.2,     # 02:12
        "techniques": ["T1071.001", "T1573.001", "T1071.004"],
        "description": "Command and control channel setup"
    },
    {
        "phase": 3,
        "name": "Lateral Movement",
        "start_offset_hours": 2.2,   # 02:12
        "end_offset_hours": 10.68,   # 10:41
        "techniques": ["T1021.001", "T1021.002"],
        "description": "Spreading through the network"
    },
    {
        "phase": 4,
        "name": "Data Access & Exfiltration",
        "start_offset_hours": 2.67,  # 02:40
        "end_offset_hours": 6.27,    # 06:16
        "techniques": ["T1048.003", "T1041"],
        "description": "Accessing and stealing sensitive data"
    },
    {
        "phase": 5,
        "name": "Persistence & Continued Access",
        "start_offset_hours": 4.28,  # 04:17
        "end_offset_hours": 18.33,   # 18:20
        "techniques": ["T1190", "T1133"],
        "description": "Maintaining access and continued exploitation"
    }
]


def generate_uid() -> str:
    """Generate a Zeek-style UID."""
    return f"C{uuid.uuid4().hex[:15]}"


def generate_benign_conn_log(timestamp: datetime, idx: int) -> Dict[str, Any]:
    """Generate a benign connection log entry."""
    src_host = random.choice(INTERNAL_HOSTS)
    
    # Decide connection type
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
        dst_ip = random.choice(EXTERNAL_BENIGN)
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


def generate_attack_events() -> tuple[List[Dict], List[Dict], Dict]:
    """Generate attack traffic with ground truth labels."""
    conn_events = []
    dns_events = []
    ground_truth = {
        "events": {},
        "attack_timeline": [],
        "incidents": [{
            "id": "INC-001",
            "name": "Multi-stage C2 and Data Exfiltration",
            "severity": "critical",
            "event_ids": [],
            "techniques": []
        }]
    }
    
    compromised_host = INTERNAL_HOSTS[0]  # workstation-042
    event_idx = 5000  # Start after benign events
    
    # Phase 1: Initial Compromise (02:08)
    phase1_time = BASE_TIME + timedelta(hours=2, minutes=8)
    
    # Suspicious auth event (simulated as connection to DC)
    event = {
        "id": f"conn_{event_idx:05d}",
        "ts": phase1_time.isoformat(),
        "uid": generate_uid(),
        "id.orig_h": compromised_host["ip"],
        "id.orig_p": random.randint(49152, 65535),
        "id.resp_h": "10.0.2.30",  # File server (simulating DC)
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
        "description": "Credential abuse - initial access"
    }
    ground_truth["incidents"][0]["event_ids"].append(event["id"])
    event_idx += 1
    
    # Phase 2: C2 Establishment (02:08 - 02:12)
    # C2 beaconing - periodic connections
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
            "description": "C2 beacon over HTTPS"
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # DNS tunneling setup
    for i in range(10):
        tunnel_time = phase1_time + timedelta(minutes=i, seconds=random.randint(0, 30))
        subdomain = ''.join(random.choices('abcdef0123456789', k=32))
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
            "description": "DNS tunneling for C2"
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # Phase 3: Lateral Movement (02:12 - 10:41)
    lateral_targets = [
        INTERNAL_HOSTS[1],  # workstation-055
        INTERNAL_HOSTS[3],  # laptop-sales-03
        INTERNAL_HOSTS[4],  # server-db-01
    ]
    
    phase3_start = BASE_TIME + timedelta(hours=2, minutes=12)
    for i, target in enumerate(lateral_targets):
        move_time = phase3_start + timedelta(minutes=i * 15 + random.randint(0, 10))
        
        # RDP or SMB connection
        proto_choice = random.choice(["rdp", "smb"])
        if proto_choice == "rdp":
            port = 3389
            service = "rdp"
            technique = "T1021.001"
        else:
            port = 445
            service = "smb"
            technique = "T1021.002"
        
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": move_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": compromised_host["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": target["ip"],
            "id.resp_p": port,
            "proto": "tcp",
            "service": service,
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
            "description": f"Lateral movement to {target['hostname']}"
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # Additional lateral movement later in the day
    for i in range(5):
        late_move_time = BASE_TIME + timedelta(hours=random.uniform(4, 10))
        src = random.choice([INTERNAL_HOSTS[0], INTERNAL_HOSTS[1]])
        dst = random.choice([h for h in INTERNAL_HOSTS if h != src])
        
        event = {
            "id": f"conn_{event_idx:05d}",
            "ts": late_move_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": src["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": dst["ip"],
            "id.resp_p": random.choice([445, 3389]),
            "proto": "tcp",
            "service": random.choice(["smb", "rdp"]),
            "duration": round(random.uniform(30, 300), 3),
            "orig_bytes": random.randint(5000, 50000),
            "resp_bytes": random.randint(10000, 100000),
            "conn_state": "SF",
            "hostname": src["hostname"],
            "user": src["user"]
        }
        conn_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 3,
            "technique": "T1021.002",
            "description": f"Lateral movement from {src['hostname']} to {dst['hostname']}"
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # Phase 4: Data Exfiltration (02:40 - 06:16)
    db_server = INTERNAL_HOSTS[4]  # server-db-01
    
    # Large data transfer to C2
    exfil_times = [
        BASE_TIME + timedelta(hours=2, minutes=40),
        BASE_TIME + timedelta(hours=3, minutes=45),
        BASE_TIME + timedelta(hours=6, minutes=16),
    ]
    
    for exfil_time in exfil_times:
        # Connection from DB server to C2
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
            "orig_bytes": random.randint(1000000, 10000000),  # Large upload
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
            "description": "Data exfiltration over C2 channel"
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # DNS exfiltration
    for i in range(20):
        dns_exfil_time = BASE_TIME + timedelta(hours=random.uniform(3, 6))
        encoded_data = ''.join(random.choices('abcdef0123456789', k=60))
        event = {
            "id": f"dns_{event_idx:05d}",
            "ts": dns_exfil_time.isoformat(),
            "uid": generate_uid(),
            "id.orig_h": db_server["ip"],
            "id.orig_p": random.randint(49152, 65535),
            "id.resp_h": "8.8.8.8",
            "id.resp_p": 53,
            "proto": "udp",
            "query": f"{encoded_data}.{random.choice(EXFIL_DOMAINS)}",
            "qtype": "TXT",
            "rcode": 0,
            "rcode_name": "NOERROR",
            "hostname": db_server["hostname"],
            "user": db_server["user"]
        }
        dns_events.append(event)
        ground_truth["events"][event["id"]] = {
            "label": "malicious",
            "attack_phase": 4,
            "technique": "T1048.003",
            "description": "Data exfiltration via DNS"
        }
        ground_truth["incidents"][0]["event_ids"].append(event["id"])
        event_idx += 1
    
    # Phase 5: Web exploitation attempts (04:17 - 18:20)
    web_server = INTERNAL_HOSTS[5]  # server-web-02
    
    for attacker_ip in ATTACKER_IPS:
        for i in range(15):
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
                "description": f"Web exploitation attempt from {attacker_ip}"
            }
            ground_truth["incidents"][0]["event_ids"].append(event["id"])
            event_idx += 1
    
    # Continued C2 beaconing throughout the day
    for hour in range(3, 19):
        for beacon in range(4):  # 4 beacons per hour
            beacon_time = BASE_TIME + timedelta(hours=hour, minutes=beacon * 15 + random.randint(-5, 5))
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
                "duration": round(random.uniform(0.5, 3), 3),
                "orig_bytes": random.randint(200, 800),
                "resp_bytes": random.randint(500, 3000),
                "conn_state": "SF",
                "hostname": compromised_host["hostname"],
                "user": compromised_host["user"]
            }
            conn_events.append(event)
            ground_truth["events"][event["id"]] = {
                "label": "malicious",
                "attack_phase": 2,
                "technique": "T1071.001",
                "description": "Continued C2 beaconing"
            }
            ground_truth["incidents"][0]["event_ids"].append(event["id"])
            event_idx += 1
    
    # Build attack timeline
    for phase in ATTACK_PHASES:
        phase_events = [
            eid for eid, info in ground_truth["events"].items()
            if info.get("attack_phase") == phase["phase"]
        ]
        ground_truth["attack_timeline"].append({
            "phase": phase["phase"],
            "name": phase["name"],
            "start_time": (BASE_TIME + timedelta(hours=phase["start_offset_hours"])).isoformat(),
            "event_ids": phase_events,
            "techniques": phase["techniques"]
        })
    
    # Collect all techniques
    all_techniques = set()
    for event_info in ground_truth["events"].values():
        if event_info["label"] == "malicious":
            all_techniques.add(event_info["technique"])
    ground_truth["incidents"][0]["techniques"] = list(all_techniques)
    
    return conn_events, dns_events, ground_truth


def generate_scenario():
    """Generate the complete scenario with all data."""
    print("Generating attack scenario...")
    
    # Generate benign traffic
    print(f"  Generating {TOTAL_BENIGN_EVENTS} benign events...")
    benign_conn = []
    benign_dns = []
    ground_truth = {"events": {}}
    
    for i in range(TOTAL_BENIGN_EVENTS):
        # Spread events across 24 hours
        timestamp = BASE_TIME + timedelta(seconds=random.uniform(0, 86400))
        
        if random.random() < 0.3:  # 30% DNS
            event = generate_benign_dns_log(timestamp, i)
            benign_dns.append(event)
        else:
            event = generate_benign_conn_log(timestamp, i)
            benign_conn.append(event)
        
        ground_truth["events"][event["id"]] = {"label": "benign"}
    
    # Generate attack traffic
    print(f"  Generating attack events...")
    attack_conn, attack_dns, attack_ground_truth = generate_attack_events()
    
    # Merge ground truth
    ground_truth["events"].update(attack_ground_truth["events"])
    ground_truth["attack_timeline"] = attack_ground_truth["attack_timeline"]
    ground_truth["incidents"] = attack_ground_truth["incidents"]
    
    # Combine and sort by timestamp
    all_conn = benign_conn + attack_conn
    all_dns = benign_dns + attack_dns
    all_conn.sort(key=lambda x: x["ts"])
    all_dns.sort(key=lambda x: x["ts"])
    
    # Calculate statistics
    malicious_count = sum(1 for e in ground_truth["events"].values() if e["label"] == "malicious")
    benign_count = sum(1 for e in ground_truth["events"].values() if e["label"] == "benign")
    
    # Create manifest
    manifest = {
        "name": "Multi-Stage Attack: C2 and Data Exfiltration",
        "description": "16-hour attack scenario demonstrating credential theft, C2 establishment, lateral movement, and data exfiltration via DNS tunneling",
        "log_types": ["zeek_conn", "zeek_dns"],
        "duration_hours": 16,
        "total_events": len(all_conn) + len(all_dns),
        "malicious_events": malicious_count,
        "benign_events": benign_count,
        "attack_phases": len(ATTACK_PHASES),
        "created": datetime.now().isoformat(),
        "author": "DeepTempo AI SOC Demo"
    }
    
    # Save files
    print("  Saving files...")
    
    # Raw logs
    with open(SCENARIO_DIR / "raw_logs" / "zeek_conn.json", "w") as f:
        json.dump(all_conn, f, indent=2)
    
    with open(SCENARIO_DIR / "raw_logs" / "zeek_dns.json", "w") as f:
        json.dump(all_dns, f, indent=2)
    
    # Ground truth
    with open(SCENARIO_DIR / "ground_truth.json", "w") as f:
        json.dump(ground_truth, f, indent=2)
    
    # Manifest
    with open(SCENARIO_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nScenario generated successfully!")
    print(f"  Total events: {manifest['total_events']}")
    print(f"  Malicious: {malicious_count}")
    print(f"  Benign: {benign_count}")
    print(f"  Attack phases: {len(ATTACK_PHASES)}")
    print(f"  Output: {SCENARIO_DIR}")
    
    return manifest, ground_truth


if __name__ == "__main__":
    generate_scenario()
