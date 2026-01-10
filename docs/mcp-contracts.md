# MCP Contracts

This document defines the Model Context Protocol (MCP) contracts for the DeepTempo AI SOC servers.

## Overview

The AI SOC exposes three MCP servers:

1. **DeepTempo Findings Server** - Primary access to findings and embeddings
2. **Evidence Snippets Server** - Gated access to raw log evidence
3. **Case Store Server** - Investigation case management

## Access Tiers

| Tier | Description | Default |
|------|-------------|---------|
| **Tier 1** | Embeddings, findings, aggregations | Enabled |
| **Tier 2** | Evidence snippets with redaction | Gated |
| **Tier 3** | Raw log export | Disabled |

## DeepTempo Findings Server

### Tools

#### `get_finding`

Retrieve a single finding by ID.

**Parameters:**
```json
{
    "finding_id": {
        "type": "string",
        "description": "Unique identifier of the finding",
        "required": true
    }
}
```

**Returns:**
```json
{
    "finding": {
        "finding_id": "f-2024-01-15-001",
        "embedding": [0.123, -0.456, ...],
        "mitre_predictions": {"T1071.001": 0.85},
        "anomaly_score": 0.92,
        "entity_context": {...},
        "timestamp": "2024-01-15T14:32:18Z"
    }
}
```

#### `nearest_neighbors`

Find findings with similar embeddings.

**Parameters:**
```json
{
    "query": {
        "type": "string | array",
        "description": "Finding ID or embedding vector",
        "required": true
    },
    "k": {
        "type": "integer",
        "description": "Number of neighbors to return",
        "default": 10
    },
    "filters": {
        "type": "object",
        "description": "Optional filters",
        "properties": {
            "data_source": {
                "type": "string",
                "enum": ["flow", "dns", "waf"]
            },
            "time_range": {
                "type": "object",
                "properties": {
                    "start": {"type": "string", "format": "date-time"},
                    "end": {"type": "string", "format": "date-time"}
                }
            },
            "min_anomaly_score": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
            },
            "techniques": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
}
```

**Returns:**
```json
{
    "neighbors": [
        {
            "finding": {...},
            "similarity_score": 0.95
        }
    ],
    "query_finding_id": "f-2024-01-15-001"
}
```

#### `technique_rollup`

Aggregate MITRE ATT&CK techniques over a time window.

**Parameters:**
```json
{
    "time_window": {
        "type": "object",
        "required": true,
        "properties": {
            "start": {"type": "string", "format": "date-time"},
            "end": {"type": "string", "format": "date-time"}
        }
    },
    "scope": {
        "type": "object",
        "description": "Optional scope filters",
        "properties": {
            "src_ips": {"type": "array", "items": {"type": "string"}},
            "dst_ips": {"type": "array", "items": {"type": "string"}},
            "hostnames": {"type": "array", "items": {"type": "string"}},
            "data_sources": {"type": "array", "items": {"type": "string"}}
        }
    },
    "min_confidence": {
        "type": "number",
        "description": "Minimum confidence threshold",
        "default": 0.5
    }
}
```

**Returns:**
```json
{
    "techniques": [
        {
            "technique_id": "T1071.001",
            "technique_name": "Application Layer Protocol: Web Protocols",
            "tactic": "command-and-control",
            "finding_count": 15,
            "avg_confidence": 0.82,
            "max_confidence": 0.95
        }
    ],
    "time_window": {...},
    "total_findings": 42
}
```

#### `cluster_summary`

Get summary information about a behavior cluster.

**Parameters:**
```json
{
    "cluster_id": {
        "type": "string",
        "description": "Cluster identifier",
        "required": true
    }
}
```

**Returns:**
```json
{
    "cluster": {
        "cluster_id": "c-beaconing-001",
        "label": "Periodic Beaconing Pattern",
        "finding_count": 15,
        "top_techniques": {"T1071.001": 0.82},
        "entities": {
            "src_ips": ["10.0.1.15"],
            "hostnames": ["workstation-042"]
        },
        "time_range": {...}
    }
}
```

#### `list_findings`

List findings with optional filtering and pagination.

**Parameters:**
```json
{
    "filters": {
        "type": "object",
        "properties": {
            "data_source": {"type": "string"},
            "severity": {"type": "string"},
            "status": {"type": "string"},
            "time_range": {"type": "object"}
        }
    },
    "limit": {
        "type": "integer",
        "default": 50,
        "maximum": 100
    },
    "offset": {
        "type": "integer",
        "default": 0
    },
    "sort_by": {
        "type": "string",
        "enum": ["timestamp", "anomaly_score", "severity"],
        "default": "timestamp"
    },
    "sort_order": {
        "type": "string",
        "enum": ["asc", "desc"],
        "default": "desc"
    }
}
```

#### `export_attack_layer`

Generate an ATT&CK Navigator layer JSON.

**Parameters:**
```json
{
    "time_window": {
        "type": "object",
        "required": true
    },
    "scope": {
        "type": "object"
    },
    "layer_name": {
        "type": "string",
        "default": "DeepTempo Findings"
    }
}
```

**Returns:**
```json
{
    "layer": {
        "name": "DeepTempo Findings",
        "version": "4.5",
        "domain": "enterprise-attack",
        "techniques": [...]
    }
}
```

### Resources

#### `findings://summary`

Get a summary of all findings.

```json
{
    "total_findings": 150,
    "by_severity": {
        "critical": 5,
        "high": 25,
        "medium": 70,
        "low": 50
    },
    "by_data_source": {
        "flow": 80,
        "dns": 45,
        "waf": 25
    },
    "time_range": {
        "earliest": "2024-01-15T00:00:00Z",
        "latest": "2024-01-15T23:59:59Z"
    }
}
```

## Evidence Snippets Server

### Tools (Tier 2 - Gated)

#### `evidence_snippets`

Retrieve raw log snippets for a finding.

**Parameters:**
```json
{
    "finding_id": {
        "type": "string",
        "required": true
    },
    "max_lines": {
        "type": "integer",
        "default": 200,
        "maximum": 500
    },
    "redaction": {
        "type": "string",
        "enum": ["on", "off"],
        "default": "on"
    }
}
```

**Returns:**
```json
{
    "snippets": [
        {
            "type": "flow",
            "lines": [
                "2024-01-15T14:32:18Z TCP 10.0.1.15:54321 -> 203.0.113.50:443 ...",
                "..."
            ],
            "redacted_fields": ["user_id", "session_token"]
        }
    ],
    "finding_id": "f-2024-01-15-001"
}
```

#### `raw_log_export` (Tier 3 - Disabled by Default)

Export raw logs for a time range.

**Parameters:**
```json
{
    "time_range": {
        "type": "object",
        "required": true
    },
    "data_source": {
        "type": "string",
        "required": true
    },
    "filters": {
        "type": "object"
    },
    "format": {
        "type": "string",
        "enum": ["json", "csv"],
        "default": "json"
    }
}
```

**Note:** This endpoint is disabled by default. Enable with `ENABLE_RAW_LOG_EXPORT=true`.

## Case Store Server

### Tools

#### `create_case`

Create a new investigation case.

**Parameters:**
```json
{
    "title": {
        "type": "string",
        "required": true
    },
    "description": {
        "type": "string"
    },
    "finding_ids": {
        "type": "array",
        "items": {"type": "string"},
        "required": true
    },
    "priority": {
        "type": "string",
        "enum": ["low", "medium", "high", "critical"],
        "default": "medium"
    },
    "assignee": {
        "type": "string"
    },
    "tags": {
        "type": "array",
        "items": {"type": "string"}
    }
}
```

**Returns:**
```json
{
    "case": {
        "case_id": "case-2024-01-15-001",
        "title": "...",
        "status": "new",
        "created_at": "2024-01-15T15:00:00Z"
    }
}
```

#### `update_case`

Update an existing case.

**Parameters:**
```json
{
    "case_id": {
        "type": "string",
        "required": true
    },
    "updates": {
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "priority": {"type": "string"},
            "assignee": {"type": "string"},
            "add_findings": {"type": "array"},
            "remove_findings": {"type": "array"},
            "add_tags": {"type": "array"},
            "remove_tags": {"type": "array"}
        }
    }
}
```

#### `add_case_note`

Add a note to a case.

**Parameters:**
```json
{
    "case_id": {
        "type": "string",
        "required": true
    },
    "content": {
        "type": "string",
        "required": true
    },
    "author": {
        "type": "string"
    }
}
```

#### `get_case`

Retrieve a case by ID.

**Parameters:**
```json
{
    "case_id": {
        "type": "string",
        "required": true
    }
}
```

#### `list_cases`

List cases with optional filtering.

**Parameters:**
```json
{
    "filters": {
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "priority": {"type": "string"},
            "assignee": {"type": "string"},
            "tags": {"type": "array"}
        }
    },
    "limit": {
        "type": "integer",
        "default": 50
    },
    "offset": {
        "type": "integer",
        "default": 0
    }
}
```

## Error Handling

All tools return errors in a consistent format:

```json
{
    "error": {
        "code": "NOT_FOUND",
        "message": "Finding with ID 'f-xxx' not found",
        "details": {}
    }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `NOT_FOUND` | Resource not found |
| `INVALID_PARAMETER` | Invalid parameter value |
| `ACCESS_DENIED` | Insufficient permissions |
| `RATE_LIMITED` | Too many requests |
| `INTERNAL_ERROR` | Server error |

## Rate Limiting

| Tier | Rate Limit |
|------|------------|
| Tier 1 | 100 requests/minute |
| Tier 2 | 20 requests/minute |
| Tier 3 | 5 requests/minute |

## Audit Logging

All MCP tool invocations are logged:

```json
{
    "timestamp": "2024-01-15T15:00:00Z",
    "tool": "evidence_snippets",
    "parameters": {"finding_id": "f-xxx", "redaction": "on"},
    "user": "analyst@example.com",
    "result": "success",
    "response_time_ms": 45
}
```
