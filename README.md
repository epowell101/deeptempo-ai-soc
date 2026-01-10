# DeepTempo AI SOC

An **embeddings-first AI Security Operations Center** that leverages DeepTempo's LogLM for threat detection and Claude for intelligent orchestration via MCP (Model Context Protocol).

## Overview

This project demonstrates how to build an AI-powered SOC where:

- **DeepTempo LogLM** handles log analysis, embedding generation, and MITRE ATT&CK classification
- **Claude** serves as the primary analyst interface, orchestrating investigations through natural conversation
- **MCP Servers** provide the bridge, exposing SOC tools that Claude can invoke

### The Vision: Claude as Your SOC Analyst

Instead of clicking through dashboards, you have conversations:

You: "Show me today's high-severity findings"
Claude: [queries findings] "I found 18 high-severity findings. 15 are clustered
as C2 beaconing from workstation-042..."
You: "Find similar activity across the network"
Claude: [runs embedding search] "Found 47 similar findings across 3 hosts,
all showing the same beacon pattern to 203.0.113.50..."
You: "Create a case and show me the ATT&CK techniques involved"
Claude: [creates case, generates rollup] "Created case-2026-01-10-abc123.
Primary techniques: T1071.001 (Web Protocols), T1573.001 (Encrypted Channel)..."
Plain Text

## Quick Start

### Prerequisites

- **Python 3.10+** (required for MCP SDK)
- **Claude Desktop** ([download here](https://claude.ai/download ))
- **Git**

### Step 1: Clone and Set Up

```bash
# Clone the repository
git clone https://github.com/epowell101/deeptempo-ai-soc.git
cd deeptempo-ai-soc

# Create a virtual environment (required )
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install "mcp[cli]"
Step 2: Generate Sample Data
Bash
python scripts/demo.py
This creates 50 sample security findings with:
768-dimensional embeddings
MITRE ATT&CK technique predictions
Anomaly scores and cluster assignments
An ATT&CK Navigator layer JSON file
Step 3: Configure Claude Desktop
Find your Claude Desktop config file:
Mac: ~/Library/Application Support/Claude/claude_desktop_config.json
Windows: %APPDATA%\Claude\claude_desktop_config.json
Create or edit the file with this content (replace /path/to/deeptempo-ai-soc with your actual path):
JSON
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
Example for Mac (if cloned to Downloads):
JSON
{
  "mcpServers": {
    "deeptempo-findings": {
      "command": "/Users/yourname/Downloads/deeptempo-ai-soc/venv/bin/python",
      "args": ["-m", "mcp_servers.deeptempo_findings_server.server"],
      "cwd": "/Users/yourname/Downloads/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/Users/yourname/Downloads/deeptempo-ai-soc"
      }
    },
    "evidence-snippets": {
      "command": "/Users/yourname/Downloads/deeptempo-ai-soc/venv/bin/python",
      "args": ["-m", "mcp_servers.evidence_snippets_server.server"],
      "cwd": "/Users/yourname/Downloads/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/Users/yourname/Downloads/deeptempo-ai-soc"
      }
    },
    "case-store": {
      "command": "/Users/yourname/Downloads/deeptempo-ai-soc/venv/bin/python",
      "args": ["-m", "mcp_servers.case_store_server.server"],
      "cwd": "/Users/yourname/Downloads/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/Users/yourname/Downloads/deeptempo-ai-soc"
      }
    }
  }
}
Step 4: Restart Claude Desktop
Quit Claude Desktop completely (Cmd+Q on Mac, not just close the window)
Reopen Claude Desktop
Look for the tools icon (🔨) in the chat input area - this confirms MCP servers are connected
Step 5: Start Investigating!
Try these prompts in Claude Desktop:
Plain Text
"What MCP tools do you have available?"

"Show me all high severity findings"

"Find findings similar to the first one"

"What MITRE ATT&CK techniques are detected across all findings?"

"Create a case for the beaconing cluster findings"
ATT&CK Navigator Visualization
The demo script generates an ATT&CK Navigator layer file that visualizes detected techniques.
To view the ATT&CK layer:
Run the demo to generate the layer file:
Bash
python scripts/demo.py
Open the ATT&CK Navigator: https://mitre-attack.github.io/attack-navigator/
Click "Open Existing Layer" → "Upload from local"
Select the file: data/demo_layer.json
You'll see the detected MITRE ATT&CK techniques highlighted on the matrix, with colors indicating detection frequency.
Architecture
Plain Text
┌─────────────────────────────────────────────────────────────────┐
│                         Claude Desktop                           │
│                    (Natural Language Interface )                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │ MCP Protocol
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Servers                              │
├─────────────────┬─────────────────────┬─────────────────────────┤
│ deeptempo-      │ evidence-snippets   │ case-store              │
│ findings        │                     │                         │
│                 │                     │                         │
│ • list_findings │ • get_evidence      │ • list_cases            │
│ • get_finding   │ • search_evidence   │ • create_case           │
│ • nearest_      │                     │ • update_case           │
│   neighbors     │                     │ • get_case              │
│ • technique_    │                     │                         │
│   rollup        │                     │                         │
└────────┬────────┴──────────┬──────────┴────────────┬────────────┘
         │                   │                       │
         ▼                   ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      JSON File Storage                           │
│                                                                  │
│  data/findings.json    data/cases.json    data/demo_layer.json  │
└─────────────────────────────────────────────────────────────────┘
         ▲
         │
┌────────┴────────────────────────────────────────────────────────┐
│                    DeepTempo LogLM Export                        │
│                                                                  │
│  • 768-dim embeddings    • MITRE predictions    • Anomaly scores│
└─────────────────────────────────────────────────────────────────┘
MCP Tools Reference
Findings Server (deeptempo-findings)
Tool
Description
Parameters
list_findings
List security findings with filters
severity, data_source, cluster_id, min_anomaly_score, limit
get_finding
Get a specific finding by ID
finding_id
nearest_neighbors
Find similar findings by embedding
finding_id, k
technique_rollup
MITRE ATT&CK technique statistics
min_confidence
Evidence Server (evidence-snippets)
Tool
Description
Parameters
get_evidence
Get raw log evidence for a finding
finding_id
search_evidence
Search evidence by keyword
query, limit
Case Store (case-store)
Tool
Description
Parameters
list_cases
List investigation cases
status, priority
get_case
Get a specific case
case_id
create_case
Create a new case
title, finding_ids, priority, description
update_case
Update an existing case
case_id, status, priority, notes
Troubleshooting
"Could not connect to MCP server"
Check Python version - Must be 3.10+:
Bash
python3 --version
Verify the virtual environment:
Bash
cd /path/to/deeptempo-ai-soc
source venv/bin/activate
pip list | grep mcp
Test the server manually:
Bash
source venv/bin/activate
python -m mcp_servers.deeptempo_findings_server.server
It should start without errors (just sit there waiting). Press Ctrl+C to stop.
Check config paths are correct:
Bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
Kill stale processes and restart:
Bash
pkill -f "mcp_servers"
Then quit and reopen Claude Desktop.
"Module not found" errors
Ensure PYTHONPATH is set in the Claude Desktop config:
JSON
"env": {
  "PYTHONPATH": "/path/to/deeptempo-ai-soc"
}
Check the logs
Bash
# Claude Desktop MCP logs (Mac)
cat ~/Library/Logs/Claude/mcp-server-deeptempo-findings.log

# Server-side debug logs
cat /tmp/deeptempo-findings.log
Common Issues
Issue
Solution
Python 3.9 or older
Install Python 3.10+ via brew install python@3.12 or python.org
mcp package not found
Run pip install "mcp[cli]" in your venv
Import conflicts
Make sure folder is named mcp_servers not mcp
JSON serialization errors
Ensure you have the latest server code with NumpyEncoder
Project Structure
Plain Text
deeptempo-ai-soc/
├── README.md
├── requirements.txt
├── mcp_servers/                    # MCP server implementations
│   ├── deeptempo_findings_server/  # Findings queries & embedding search
│   ├── evidence_snippets_server/   # Raw log evidence access
│   └── case_store_server/          # Investigation case management
├── skills/                         # Claude skill definitions
│   ├── soc-triage/
│   ├── embedding-hunt/
│   ├── cross-signal-correlator/
│   ├── attack-layer-exporter/
│   └── response-recommender/
├── adapters/                       # Data source adapters
│   ├── deeptempo_offline_export/   # Load from JSON exports
│   └── deeptempo_api_client/       # Future: SaaS API integration
├── data/                           # Data storage
│   ├── findings.json               # Security findings
│   ├── cases.json                  # Investigation cases
│   ├── demo_layer.json             # ATT&CK Navigator layer
│   └── schemas/                    # JSON schemas
├── scripts/
│   └── demo.py                     # Generate sample data
└── docs/                           # Additional documentation
    ├── architecture.md
    ├── data-model.md
    └── mcp-contracts.md
Roadmap
 v0.1: File-based MCP servers with sample data
 v0.2: Real DeepTempo LogLM integration
 v0.3: ATT&CK Navigator layer export skill
 v0.4: Streamlit dashboard for visualization
 v0.5: Postgres + pgvector for production scale
 v1.0: Full SaaS API integration
Contributing
See CONTRIBUTING.md for guidelines.
License
Apache 2.0 - See LICENSE for details.
References
Claude Skills - Official Anthropic skills repository
ATT&CK Navigator - MITRE ATT&CK visualization
Model Context Protocol - MCP specification
DeepTempo - LogLM for security
About DeepTempo
DeepTempo provides LogLM, a foundation model for security log analysis that generates embeddings and MITRE ATT&CK predictions from raw logs.