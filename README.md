# DeepTempo AI SOC

An **embeddings-first AI Security Operations Center** that leverages DeepTempo's LogLM for threat detection and Claude for intelligent orchestration via MCP (Model Context Protocol).

## Overview

This project demonstrates how to build an AI-powered SOC where:

- **DeepTempo LogLM** handles log analysis, embedding generation, and MITRE ATT&CK classification
- **Claude** serves as the primary analyst interface, orchestrating investigations through natural conversation
- **MCP Servers** provide the bridge, exposing SOC tools that Claude can invoke
- **Streamlit** provides rich, interactive dashboards for visualizing attack flows and comparing detection methods
- **Timesketch** provides timeline visualization for forensic analysis

### The Vision: Claude as Your SOC Analyst

Instead of clicking through dashboards, you have conversations:

```
You: "Show me today's high-severity findings"
Claude: [queries findings] "I found 18 high-severity findings. 15 are clustered 
        as C2 beaconing from workstation-042..."

You: "Find similar activity across the network"
Claude: [runs embedding search] "Found 47 similar findings across 3 hosts, 
        all showing the same beacon pattern to 203.0.113.50..."

You: "Create a timeline view in Timesketch"
Claude: [syncs to Timesketch] "Created sketch with 50 events. 
        View at: http://localhost:5000/sketch/1/"
```

## 🆕 Tale of Two SOCs: Rules vs. LogLM

This project now includes a **side-by-side comparison** demonstrating the difference between traditional rules-based detection and LogLM-enhanced detection.

### The Key Insight

**Same 5,000 logs → Two completely different experiences**

| | Rules-Only SOC | LogLM-Enhanced SOC |
|---|---|---|
| **Detections** | 602 alerts | 155 findings |
| **Precision** | 37.4% | 97.4% |
| **False Positives** | 253 | 4 |
| **Correlation** | Manual | Automatic |
| **Similarity Search** | ❌ | ✅ |
| **MITRE Classification** | ❌ | ✅ |

**LogLM detects malicious BEHAVIORS, not just anomalies.** This is why it has high precision - it's trained to recognize actual attack patterns, not just statistical outliers.

### Run the Comparison Dashboard

```bash
# Generate scenario data
python scripts/generate_scenario.py

# Run detection pipelines
python scripts/rules_detection.py
python scripts/loglm_detection.py

# Evaluate both methods
python scripts/evaluate.py

# Launch the comparison dashboard
streamlit run streamlit_app/tale_of_two_socs.py
```

### Switch Modes for Claude

The dashboard includes a **mode toggle** that controls which tools Claude can access:

- **Rules-Only Mode**: Claude only sees `list_alerts`, `filter_alerts_by_rule`, `get_alert_details`
- **LogLM Mode**: Claude sees `list_findings`, `nearest_neighbors`, `get_attack_narrative`, `technique_rollup`

This lets you experience the difference firsthand - ask Claude the same questions in both modes!

## Quick Start

### Prerequisites

- **Python 3.10+** (required for MCP SDK)
- **Claude Desktop** ([download here](https://claude.ai/download))
- **Docker** (optional, for Timesketch visualization)

### Step 1: Clone and Set Up

```bash
git clone https://github.com/epowell101/deeptempo-ai-soc.git
cd deeptempo-ai-soc

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Step 2: Generate Sample Data

```bash
# For the Tale of Two SOCs comparison:
python scripts/generate_scenario.py
python scripts/rules_detection.py
python scripts/loglm_detection.py
python scripts/evaluate.py

# For the original demo:
python scripts/demo.py
```

### Step 3: Configure Claude Desktop

Find your config file:
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**For Tale of Two SOCs (Unified Server):**

```json
{
  "mcpServers": {
    "ai-soc": {
      "command": "/path/to/deeptempo-ai-soc/venv/bin/python",
      "args": ["-m", "mcp_servers.unified_soc_server.server"],
      "cwd": "/path/to/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/path/to/deeptempo-ai-soc",
        "DATA_DIR": "/path/to/deeptempo-ai-soc/data"
      }
    }
  }
}
```

**For Original Demo (Multiple Servers):**

```json
{
  "mcpServers": {
    "deeptempo-findings": {
      "command": "/path/to/deeptempo-ai-soc/venv/bin/python",
      "args": ["-m", "mcp_servers.deeptempo_findings_server.server"],
      "cwd": "/path/to/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/path/to/deeptempo-ai-soc"
      }
    },
    "evidence-snippets": {
      "command": "/path/to/deeptempo-ai-soc/venv/bin/python",
      "args": ["-m", "mcp_servers.evidence_snippets_server.server"],
      "cwd": "/path/to/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/path/to/deeptempo-ai-soc"
      }
    },
    "case-store": {
      "command": "/path/to/deeptempo-ai-soc/venv/bin/python",
      "args": ["-m", "mcp_servers.case_store_server.server"],
      "cwd": "/path/to/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/path/to/deeptempo-ai-soc"
      }
    }
  }
}
```

### Step 4: Restart Claude Desktop
Quit completely (Cmd+Q on Mac, Alt+F4 on Windows) and reopen.

### Step 5: Start Investigating!

**Tale of Two SOCs prompts:**
```
"What mode am I in?"
"List all alerts" (in rules-only mode)
"List all findings" (in LogLM mode)
"Find similar findings to finding_00001"
"Show me the attack narrative"
"What are the evaluation metrics?"
```

**Original demo prompts:**
```
"Show me all high severity findings"
"Find findings similar to f-20260109-9bfe5ba7"
"What MITRE ATT&CK techniques are detected?"
"Create a case for the beaconing cluster"
```

## Dashboards

### Tale of Two SOCs Dashboard

```bash
streamlit run streamlit_app/tale_of_two_socs.py
```

Features:
- **Side-by-side comparison** of Rules vs. LogLM detection
- **Confusion matrix visualization** showing precision/recall
- **MTTD (Mean Time to Detect)** analysis by attack phase
- **Mode toggle** for Claude integration
- **Radar chart** comparing detection performance

### Attack Flow Visualization

```bash
streamlit run streamlit_app/app.py
```

Features:
- **Attack Graph**: Interactive network graph of all entities
- **Kill Chain Timeline**: Visual timeline of attack phases
- **Data Exfiltration Flow**: Sankey diagram of data movement
- **MITRE ATT&CK Heatmap**: Bar chart of detected techniques

## Timesketch Integration

### Mock Mode (Default)

The Timesketch server runs in mock mode by default, simulating functionality without requiring a real server.

### Live Timesketch Server

```bash
cd docker
docker compose up -d
# Wait 2-3 minutes for services to start
# Access at http://localhost:5000 (login: dev / dev)
```

## MCP Tools Reference

### Unified SOC Server (Tale of Two SOCs)

**Rules-Only Mode:**
| Tool | Description |
|------|-------------|
| `list_alerts` | List security alerts from Sigma rule matches |
| `get_alert_details` | Get details for a specific alert |
| `get_rule_statistics` | Get statistics about which rules are firing |

**LogLM Mode:**
| Tool | Description |
|------|-------------|
| `list_findings` | List findings with LogLM enrichment |
| `get_finding_details` | Get details including MITRE predictions |
| `list_incidents` | List correlated security incidents |
| `nearest_neighbors` | Find similar findings using embeddings |
| `technique_rollup` | Get MITRE ATT&CK technique statistics |
| `get_attack_narrative` | Get human-readable attack summary |

**Common Tools (Both Modes):**
| Tool | Description |
|------|-------------|
| `get_soc_mode` | Get current mode (rules_only or loglm) |
| `get_raw_logs` | Get raw log events |
| `get_evaluation_metrics` | Get confusion matrix and MTTD metrics |

### Original Servers

| Server | Tools |
|--------|-------|
| Findings | `list_findings`, `get_finding`, `nearest_neighbors`, `technique_rollup` |
| Evidence | `get_evidence`, `search_evidence` |
| Case Store | `list_cases`, `get_case`, `create_case`, `update_case` |
| Timesketch | `sync_findings_to_timesketch`, `create_timesketch_sketch`, `search_timesketch` |

## Project Structure

```
deeptempo-ai-soc/
├── streamlit_app/               # Streamlit dashboards
│   ├── app.py                   # Attack flow visualization
│   ├── tale_of_two_socs.py      # Rules vs LogLM comparison
│   └── replay.py                # Scenario replay module
├── mcp_servers/                 # MCP server implementations
│   ├── unified_soc_server/      # Tale of Two SOCs server
│   ├── deeptempo_findings_server/
│   ├── evidence_snippets_server/
│   ├── case_store_server/
│   └── timesketch_server/
├── scripts/                     # Data generation and evaluation
│   ├── generate_scenario.py     # Generate attack scenario
│   ├── rules_detection.py       # Sigma-like rule detection
│   ├── loglm_detection.py       # LogLM detection simulation
│   └── evaluate.py              # Calculate metrics
├── data/
│   └── scenarios/               # Attack scenarios with ground truth
│       └── default_attack/
├── adapters/                    # External system adapters
├── docker/                      # Docker Compose for Timesketch
└── config/                      # Configuration templates
```

## Roadmap

- [x] v0.1: File-based MCP servers with sample data
- [x] v0.2: Timesketch integration for timeline visualization
- [x] v0.3: Streamlit dashboard for attack flow visualization
- [x] v0.4: Tale of Two SOCs - Rules vs LogLM comparison with evaluation metrics
- [ ] v0.5: Real DeepTempo LogLM integration
- [ ] v1.0: Full SaaS API integration

## Troubleshooting

### Python Version
MCP requires Python 3.10+:
```bash
python3 --version
```

### Test Server Manually
```bash
source venv/bin/activate
python -m mcp_servers.unified_soc_server.server
```

### Check Logs
```bash
cat ~/Library/Logs/Claude/mcp-server-ai-soc.log
```

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## References

- [Timesketch](https://timesketch.org/) - Timeline analysis platform
- [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/) - MITRE ATT&CK visualization
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [DeepTempo](https://deeptempo.ai) - LogLM for security
