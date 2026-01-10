# DeepTempo: Embeddings-First AI SOC (Flow + DNS + WAF)

This repository is an open-source blueprint for building a **Claude-powered SOC** where:

- **DeepTempo's LogLM** provides the primitives: embeddings + anomaly signals + MITRE ATT&CK technique predictions (classifier output)
- **Claude** provides orchestration: triage narratives, workflow decisions, investigation plans
- **All glue code is open source**: skills, MCP servers, storage, adapters

## The Thesis

> **Raw logs are second best. Embeddings are the interface.**

We treat raw Flow/DNS/WAF logs as evidence-on-demand, not as the primary object of investigation. DeepTempo's LogLM transforms logs into semantic embeddings that capture behavioral patterns, enabling similarity search, clustering, and MITRE ATT&CK technique prediction.

## What You Get

### 1. Embeddings-First Investigation Workflow

- Load DeepTempo findings (today: offline export; tomorrow: API)
- Store findings + vectors in JSON files (simplified v0.1)
- Run nearest-neighbor search ("show me similar behavior")
- Roll up MITRE technique heatmaps across time/entities
- Generate an [ATT&CK Navigator](https://github.com/mitre-attack/attack-navigator) layer JSON for visualization

### 2. Claude Skills for SOC Tasks

Skills are versioned, testable "mini-runbooks" that Claude can invoke:

| Skill | Description |
|-------|-------------|
| `soc-triage` | Write an initial triage report from a finding + neighbors |
| `embedding-hunt` | Pivot from one embedding to a behavior cluster |
| `cross-signal-correlator` | Corroborate a flow-centered finding with DNS + WAF context |
| `attack-layer-exporter` | Export Navigator layer JSON |
| `response-recommender` | Generate response recommendations (never auto-exec by default) |

We follow the "skills are folders" conventions used in [anthropics/skills](https://github.com/anthropics/skills).

### 3. MCP Servers That Expose Only What Claude Needs

We provide MCP servers that default to embeddings-first endpoints, with raw logs gated behind "evidence snippet" calls.

## Quick Start

### Prerequisites

- Python 3.10+
- pip or uv package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/epowell101/deeptempo-embeddings-first-ai-soc.git
cd deeptempo-embeddings-first-ai-soc

# Install dependencies
pip install -r requirements.txt

# Or with uv
uv pip install -r requirements.txt
```

### Load Sample Findings

```bash
# Load the sample dataset
python -m adapters.deeptempo_offline_export.loader

# Verify data loaded
python -c "from adapters.deeptempo_offline_export.loader import load_findings; print(f'Loaded {len(load_findings())} findings')"
```

### Run MCP Servers

```bash
# Run the DeepTempo findings server
python -m mcp.deeptempo_findings_server.server

# In another terminal, run the evidence snippets server
python -m mcp.evidence_snippets_server.server
```

## Data Model (High Level)

A **Finding** is the SOC's primary object:

```python
{
    "finding_id": "uuid",
    "embedding": [float, ...],           # 768-dim vector from LogLM
    "mitre_predictions": {               # technique_id -> confidence score
        "T1071.001": 0.85,
        "T1048.003": 0.72
    },
    "anomaly_score": 0.92,
    "entity_context": {
        "src_ip": "10.0.1.15",
        "dst_ip": "203.0.113.50",
        "hostname": "workstation-042",
        "user": "jsmith",
        "app": "curl"
    },
    "evidence_links": [                  # Pointers to log slices (not full logs)
        {"type": "flow", "ref": "flow/2024-01-15/chunk_042.json", "lines": [1520, 1535]},
        {"type": "dns", "ref": "dns/2024-01-15/chunk_012.json", "lines": [890, 892]}
    ],
    "timestamp": "2024-01-15T14:32:18Z",
    "data_source": "flow"
}
```

## MCP Contracts (Embeddings-First)

### Tier 1 (Default)

| Endpoint | Description |
|----------|-------------|
| `get_finding(finding_id)` | Retrieve a single finding by ID |
| `nearest_neighbors(finding_id \| embedding, k, filters)` | Find similar findings |
| `technique_rollup(time_window, scope)` | Aggregate MITRE techniques over time |
| `cluster_summary(cluster_id)` | Get summary of a behavior cluster |

### Tier 2 (Gated)

| Endpoint | Description |
|----------|-------------|
| `evidence_snippets(finding_id, max_lines=200, redaction=on)` | Get raw log snippets |
| `raw_log_export(...)` | Full log export (disabled by default) |

## Why This Repo Exists

Most "AI SOC" demos make LLMs pretend to be detectors. This repo does the opposite:

- **LogLM detects** behavior and maps to MITRE
- **Claude reasons**, communicates, and orchestrates
- **You get the best of both**: accuracy + interpretability + workflow speed

## Project Structure

```
deeptempo-embeddings-first-ai-soc/
├── README.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── requirements.txt
├── docs/
│   ├── architecture.md
│   ├── data-model.md
│   ├── mcp-contracts.md
│   └── skills/
│       ├── skill-authoring-guide.md
│       └── prompt-principles.md
├── skills/                       # Claude Skills (open-source glue)
│   ├── soc-triage/
│   ├── embedding-hunt/
│   ├── cross-signal-correlator/
│   ├── attack-layer-exporter/
│   └── response-recommender/
├── mcp/                          # Model Context Protocol servers
│   ├── deeptempo-findings-server/
│   ├── evidence-snippets-server/
│   └── case-store-server/
├── services/
│   └── api/                      # FastAPI "SOC API"
├── adapters/
│   ├── deeptempo_offline_export/ # Load DeepTempo outputs from files
│   └── deeptempo_api_client/     # Future: SaaS client (same interface)
└── data/
    ├── samples/                  # Sample findings
    └── schemas/                  # JSON schemas
```

## Roadmap

- **v0.1** (current): Simplified file-based implementation for demonstration
- **v1**: Postgres + pgvector for production storage
- **v2**: DeepTempo SaaS API client adapter (drop-in replacement)
- **v3**: Optional integrations (case management, timelines, SIEM export)

## Security Notes

- Default stance is **read-only** and **least privilege**
- Raw log access is **minimized** and **redacted**
- All actions are **explicit** and **auditable**

## References

- [Claude Skills](https://github.com/anthropics/skills) - Official Anthropic skills repository
- [ATT&CK Navigator](https://github.com/mitre-attack/attack-navigator) - MITRE ATT&CK visualization
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [DeepTempo](https://deeptempo.ai) - LogLM for security

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
