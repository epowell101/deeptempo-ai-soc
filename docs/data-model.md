# Data Model

This document describes the data model for the DeepTempo Embeddings-First AI SOC.

## Core Entities

### Finding

A **Finding** is the primary object in the SOC. It represents a behavioral observation from DeepTempo's LogLM, enriched with embeddings and MITRE ATT&CK predictions.

```json
{
    "finding_id": "f-2024-01-15-001",
    "embedding": [0.123, -0.456, 0.789, ...],
    "mitre_predictions": {
        "T1071.001": 0.85,
        "T1048.003": 0.72,
        "T1059.001": 0.45
    },
    "anomaly_score": 0.92,
    "entity_context": {
        "src_ip": "10.0.1.15",
        "dst_ip": "203.0.113.50",
        "src_port": 54321,
        "dst_port": 443,
        "hostname": "workstation-042",
        "user": "jsmith",
        "app": "curl",
        "domain": "suspicious-domain.com"
    },
    "evidence_links": [
        {
            "type": "flow",
            "ref": "flow/2024-01-15/chunk_042.json",
            "lines": [1520, 1535]
        },
        {
            "type": "dns",
            "ref": "dns/2024-01-15/chunk_012.json",
            "lines": [890, 892]
        }
    ],
    "timestamp": "2024-01-15T14:32:18Z",
    "data_source": "flow",
    "cluster_id": "c-beaconing-001",
    "severity": "high",
    "status": "new"
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `finding_id` | string | Unique identifier for the finding |
| `embedding` | float[] | 768-dimensional vector from LogLM |
| `mitre_predictions` | object | Map of MITRE technique IDs to confidence scores (0-1) |
| `anomaly_score` | float | Overall anomaly score from LogLM (0-1) |
| `entity_context` | object | Contextual information about involved entities |
| `evidence_links` | array | Pointers to raw log evidence |
| `timestamp` | string | ISO 8601 timestamp of the finding |
| `data_source` | string | Source data type: "flow", "dns", or "waf" |
| `cluster_id` | string | Optional cluster assignment |
| `severity` | string | Severity level: "low", "medium", "high", "critical" |
| `status` | string | Status: "new", "investigating", "resolved", "false_positive" |

### Evidence Link

An **Evidence Link** points to a slice of raw log data without including the full log content.

```json
{
    "type": "flow",
    "ref": "flow/2024-01-15/chunk_042.json",
    "lines": [1520, 1535],
    "hash": "sha256:abc123..."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Evidence type: "flow", "dns", "waf" |
| `ref` | string | Reference path to the evidence file |
| `lines` | int[] | Start and end line numbers (inclusive) |
| `hash` | string | Optional hash for integrity verification |

### Case

A **Case** represents an investigation that groups related findings.

```json
{
    "case_id": "case-2024-01-15-001",
    "title": "Potential C2 Beaconing from Workstation-042",
    "description": "Multiple findings indicate possible command and control activity",
    "finding_ids": [
        "f-2024-01-15-001",
        "f-2024-01-15-002",
        "f-2024-01-15-003"
    ],
    "status": "investigating",
    "priority": "high",
    "assignee": "analyst@example.com",
    "created_at": "2024-01-15T15:00:00Z",
    "updated_at": "2024-01-15T16:30:00Z",
    "tags": ["c2", "beaconing", "workstation"],
    "notes": [
        {
            "author": "analyst@example.com",
            "timestamp": "2024-01-15T15:30:00Z",
            "content": "Initial triage complete. Confirmed suspicious activity."
        }
    ],
    "mitre_techniques": ["T1071.001", "T1048.003"],
    "timeline": [
        {
            "timestamp": "2024-01-15T14:32:18Z",
            "event": "First finding detected"
        },
        {
            "timestamp": "2024-01-15T14:45:00Z",
            "event": "Related DNS activity observed"
        }
    ]
}
```

### Cluster

A **Cluster** groups findings with similar behavioral patterns.

```json
{
    "cluster_id": "c-beaconing-001",
    "label": "Periodic Beaconing Pattern",
    "description": "Findings exhibiting regular interval communication patterns",
    "centroid": [0.234, -0.567, 0.890, ...],
    "finding_count": 15,
    "finding_ids": ["f-2024-01-15-001", "f-2024-01-15-002", ...],
    "top_techniques": {
        "T1071.001": 0.82,
        "T1573.001": 0.65
    },
    "entities": {
        "src_ips": ["10.0.1.15", "10.0.1.22"],
        "dst_ips": ["203.0.113.50"],
        "hostnames": ["workstation-042", "workstation-055"]
    },
    "time_range": {
        "start": "2024-01-15T14:00:00Z",
        "end": "2024-01-15T18:00:00Z"
    }
}
```

### ATT&CK Layer

An **ATT&CK Layer** is the export format for MITRE ATT&CK Navigator visualization.

```json
{
    "name": "DeepTempo Findings - 2024-01-15",
    "version": "4.5",
    "domain": "enterprise-attack",
    "description": "MITRE ATT&CK techniques observed in DeepTempo findings",
    "filters": {
        "platforms": ["Windows", "Linux", "macOS"]
    },
    "sorting": 3,
    "layout": {
        "layout": "side",
        "showID": true,
        "showName": true
    },
    "hideDisabled": false,
    "techniques": [
        {
            "techniqueID": "T1071.001",
            "tactic": "command-and-control",
            "score": 85,
            "color": "#ff6666",
            "comment": "15 findings with high confidence",
            "enabled": true,
            "metadata": [
                {
                    "name": "finding_count",
                    "value": "15"
                }
            ]
        }
    ],
    "gradient": {
        "colors": ["#ffffff", "#ff6666"],
        "minValue": 0,
        "maxValue": 100
    },
    "metadata": [
        {
            "name": "generated_by",
            "value": "DeepTempo AI SOC"
        },
        {
            "name": "time_range",
            "value": "2024-01-15T00:00:00Z to 2024-01-15T23:59:59Z"
        }
    ]
}
```

## Entity Context Fields

The `entity_context` object varies by data source:

### Flow Context

```json
{
    "src_ip": "10.0.1.15",
    "dst_ip": "203.0.113.50",
    "src_port": 54321,
    "dst_port": 443,
    "protocol": "tcp",
    "bytes_sent": 1024,
    "bytes_recv": 4096,
    "packets_sent": 10,
    "packets_recv": 25,
    "duration_ms": 5000,
    "hostname": "workstation-042",
    "user": "jsmith"
}
```

### DNS Context

```json
{
    "src_ip": "10.0.1.15",
    "query_name": "suspicious-domain.com",
    "query_type": "A",
    "response_code": "NOERROR",
    "response_ips": ["203.0.113.50"],
    "ttl": 300,
    "hostname": "workstation-042"
}
```

### WAF Context

```json
{
    "src_ip": "203.0.113.100",
    "dst_ip": "10.0.2.50",
    "method": "POST",
    "uri": "/api/upload",
    "status_code": 200,
    "user_agent": "curl/7.68.0",
    "rule_matched": "942100",
    "rule_category": "SQL Injection",
    "action": "blocked"
}
```

## MITRE ATT&CK Techniques

The system tracks the following technique categories:

| Tactic | Example Techniques |
|--------|-------------------|
| Initial Access | T1190, T1133 |
| Execution | T1059.001, T1059.003 |
| Persistence | T1053, T1136 |
| Defense Evasion | T1027, T1070 |
| Discovery | T1046, T1082 |
| Lateral Movement | T1021, T1570 |
| Collection | T1005, T1074 |
| Command and Control | T1071.001, T1573 |
| Exfiltration | T1048, T1041 |

## Severity Calculation

Severity is calculated based on:

1. **Anomaly Score**: Higher scores indicate more unusual behavior
2. **MITRE Confidence**: Higher confidence in technique predictions
3. **Technique Severity**: Some techniques are inherently more severe
4. **Entity Sensitivity**: Critical assets increase severity

```python
def calculate_severity(finding: dict) -> str:
    score = finding["anomaly_score"]
    max_mitre = max(finding["mitre_predictions"].values(), default=0)
    
    combined = (score * 0.6) + (max_mitre * 0.4)
    
    if combined >= 0.8:
        return "critical"
    elif combined >= 0.6:
        return "high"
    elif combined >= 0.4:
        return "medium"
    else:
        return "low"
```

## JSON Schemas

Full JSON schemas are available in the `data/schemas/` directory:

- `finding.schema.json` - Finding schema
- `case.schema.json` - Case schema
- `cluster.schema.json` - Cluster schema
- `attack-layer.schema.json` - ATT&CK Navigator layer schema
