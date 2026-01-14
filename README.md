# Example AI SOC - using the DeepTempo LogLM for incident identification plus Claude and Claude skills

## Overview

This project demonstrates how to build an AI-powered SOC where:

- **The DeepTempo LogLM** handles log based identification of attacks, generates embeddings, and classifies attacks based on MITRE ATT&CK
- **Claude** serves as the primary analyst interface, orchestrating investigations through natural conversation
- **MCP Servers** provide the bridge, exposing SOC tools that Claude can invoke
- **the MITRE ATT&CK explorer serves as an example GUI

### The Vision: Claude as Your SOC Analyst

Instead of clicking through dashboards, or using proprietary AI SOC solutions, you work directly with Claude and DeepTempo and possibly (with some extension work) another SIEM as your source of information

```
You: "Show me today's high-severity findings"
Claude: [queries findings] "I found 18 high-severity findings. 15 are clustered 
        as C2 beaconing from workstation-042..."

You: "Find similar activity"
Claude: [runs embedding search] "Found 47 similar findings across 3 hosts, 
        all showing the same beacon pattern to 203.0.113.50..."

You: "Create a case and show me the ATT&CK techniques involved"
Claude: [creates case, generates rollup] "Created case-2026-01-10-abc123. 
        Primary techniques: T1071.001 (Web Protocols), T1573.001 (Encrypted Channel)..."
```

## 🆕 New Features

### AI-Powered Custom Integration Builder 🤖✨

Build custom security integrations in minutes using AI! Simply provide API documentation and let Claude generate complete MCP server integrations automatically:

- **🧠 AI-Powered Analysis**: Claude analyzes API docs and generates complete integration code
- **⚡ Lightning Fast**: Go from documentation to working integration in under 5 minutes
- **🎯 Zero Coding**: No programming knowledge required - just paste API docs
- **🔧 Production Ready**: Generates complete MCP servers with error handling and validation
- **📝 Auto Configuration**: Creates UI fields, schemas, and tool definitions automatically
- **✅ Code Validation**: Built-in validation ensures generated code is correct

**Example Use Case**: Want to add support for a new threat feed? Just paste the API docs and Claude will generate:
- Integration configuration UI
- Complete MCP server code  
- Tool definitions for all API endpoints
- Authentication handling

**Quick Start**: Settings → Integrations → "Build Custom Integration"  
**Full Guide**: See `docs/custom-integration-builder.md` for complete documentation  
**Implementation Details**: See `CUSTOM_INTEGRATION_BUILDER.md` for technical overview

### Cribl Stream Integration 🔄

Optimize your security data pipeline with Cribl Stream integration:

- **📊 Data Normalization**: Standardize logs before AI analysis for better accuracy
- **💰 Cost Reduction**: Reduce SIEM ingestion costs by 30-50% through intelligent filtering
- **🔍 Real-time Enrichment**: Add GeoIP, threat intel, and asset context automatically
- **🚀 Multi-Destination Routing**: Send data to DeepTempo, Splunk, S3, and more simultaneously

**Quick Start**: See `docs/cribl-quick-start.md` for 15-minute setup  
**Full Guide**: See `docs/cribl-integration.md` for complete documentation

### Comprehensive Case Management System

In addition to conversational AI with Claude, the platform now includes a **full-featured React web UI** with comprehensive case management:

### Key Features

- **📋 Complete Case Management**: Create, track, and resolve security cases from detection to resolution
- **🔍 Dynamic Finding Association**: Add/remove findings to cases on the fly
- **📝 Activity Tracking**: Full audit trail with timestamped activities (notes, investigations, actions)
- **✅ Resolution Workflow**: Document step-by-step resolution process with detailed actions and results
- **📊 PDF Report Generation**: Generate professional reports including all activities and resolution steps
- **🎯 Status Tracking**: Open, In Progress, Resolved, Closed with visual indicators
- **👥 Case Assignment**: Track case ownership and responsibility

### Quick Access

```bash
# Start the web UI (see QUICK_START_WEB.md for details)
cd frontend
npm install
npm run dev
# Access at http://localhost:5173
```

**Documentation:**
- **Quick Start**: `QUICK_START_CASE_MANAGEMENT.md` - Get started in 5 minutes
- **Full Guide**: `docs/case-management-system.md` - Complete feature documentation
- **Demo Case**: Open "Suspicious Lateral Movement Detected" to see all features in action

## Quick Start

### Prerequisites

- **Python 3.10+** (required - 3.12 recommended)
  - Required for Claude Agent SDK and all integrations
  - Check version: `python3 --version`
  - Upgrade if needed: See [PYTHON_COMPATIBILITY_GUIDE.md](PYTHON_COMPATIBILITY_GUIDE.md)
- **Claude API Key** - Get yours at [console.anthropic.com](https://console.anthropic.com/)
- **Git**

> **Note for Server Deployments:** This application now supports flexible secrets management suitable for server environments. See [SECRETS_MIGRATION.md](SECRETS_MIGRATION.md) for details.

### Step 1: Clone and Set Up

```bash
# Clone the repository
git clone https://github.com/epowell101/deeptempo-ai-soc.git
cd deeptempo-ai-soc

# Create a virtual environment (Python 3.10+ required)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies (includes Claude Agent SDK and all integrations)
pip install -r requirements.txt
pip install "mcp[cli]"

# Configure secrets (for server deployments)
cp env.example ~/.deeptempo/.env
nano ~/.deeptempo/.env  # Add your CLAUDE_API_KEY and other secrets
chmod 600 ~/.deeptempo/.env
```

### Step 2: Generate Sample Data

```bash
python scripts/demo.py
```

This creates 50 sample security findings with:
- 768-dimensional embeddings
- MITRE ATT&CK technique predictions
- Anomaly scores and cluster assignments
- An ATT&CK Navigator layer JSON file

### Step 3: Configure Claude Desktop

**Find your Claude Desktop config file:**
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Create or edit the file with this content** (replace `/path/to/deeptempo-ai-soc` with your actual path):

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

**Example for Mac** (if cloned to Downloads):

```json
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
```

### Step 4: Restart Claude Desktop

1. **Quit Claude Desktop completely** (Cmd+Q on Mac, not just close the window)
2. **Reopen Claude Desktop**
3. Look for the tools icon in the chat input area - this confirms MCP servers are connected

### Step 5: Start Investigating!

Try these prompts in Claude Desktop:

- "What MCP tools do you have available?"
- "Show me all high severity findings"
- "Find findings similar to the first one"
- "What MITRE ATT&CK techniques are detected across all findings?"
- "Create a case for the beaconing cluster findings"

## ATT&CK Navigator Visualization

The demo script generates an ATT&CK Navigator layer file that visualizes detected techniques.

**To view the ATT&CK layer:**

1. Run the demo to generate the layer file:
   ```bash
   python scripts/demo.py
   ```

2. Open the ATT&CK Navigator: https://mitre-attack.github.io/attack-navigator/

3. Click **"Open Existing Layer"** then **"Upload from local"**

4. Select the file: `data/demo_layer.json`

You'll see the detected MITRE ATT&CK techniques highlighted on the matrix, with colors indicating detection frequency.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Claude Desktop                           │
│                    (Natural Language Interface)                  │
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
```

## MCP Tools Reference

### Findings Server (deeptempo-findings)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_findings` | List security findings with filters | `severity`, `data_source`, `cluster_id`, `min_anomaly_score`, `limit` |
| `get_finding` | Get a specific finding by ID | `finding_id` |
| `nearest_neighbors` | Find similar findings by embedding | `finding_id`, `k` |
| `technique_rollup` | MITRE ATT&CK technique statistics | `min_confidence` |

### Evidence Server (evidence-snippets)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_evidence` | Get raw log evidence for a finding | `finding_id` |
| `search_evidence` | Search evidence by keyword | `query`, `limit` |

### Case Store (case-store)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_cases` | List investigation cases | `status`, `priority` |
| `get_case` | Get a specific case | `case_id` |
| `create_case` | Create a new case | `title`, `finding_ids`, `priority`, `description` |
| `update_case` | Update an existing case | `case_id`, `status`, `priority`, `notes` |

## Troubleshooting

### "Could not connect to MCP server"

1. **Check Python version** - Must be 3.10+:
   ```bash
   python3 --version
   ```

2. **Verify the virtual environment**:
   ```bash
   cd /path/to/deeptempo-ai-soc
   source venv/bin/activate
   pip list | grep mcp
   ```

3. **Test the server manually**:
   ```bash
   source venv/bin/activate
   python -m mcp_servers.deeptempo_findings_server.server
   ```
   It should start without errors (just sit there waiting). Press Ctrl+C to stop.

4. **Check config paths are correct**:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

5. **Kill stale processes and restart**:
   ```bash
   pkill -f "mcp_servers"
   ```
   Then quit and reopen Claude Desktop.

### "Module not found" errors

Ensure `PYTHONPATH` is set in the Claude Desktop config:

```json
"env": {
  "PYTHONPATH": "/path/to/deeptempo-ai-soc"
}
```

### Check the logs

```bash
# Claude Desktop MCP logs (Mac)
cat ~/Library/Logs/Claude/mcp-server-deeptempo-findings.log

# Server-side debug logs
cat /tmp/deeptempo-findings.log
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Python 3.9 or older | Install Python 3.10+ via `brew install python@3.12` or python.org |
| `mcp` package not found | Run `pip install "mcp[cli]"` in your venv |
| Import conflicts | Make sure folder is named `mcp_servers` not `mcp` |
| JSON serialization errors | Ensure you have the latest server code with NumpyEncoder |

## Project Structure

```
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
```

## Roadmap

- [x] **v0.1**: File-based MCP servers with sample data
- [ ] **v0.2**: Real DeepTempo LogLM integration
- [ ] **v0.3**: ATT&CK Navigator layer export skill
- [ ] **v0.4**: Streamlit dashboard for visualization
- [ ] **v0.5**: Postgres + pgvector for production scale
- [ ] **v1.0**: Full SaaS API integration

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## References

- [Claude Skills](https://github.com/anthropics/skills) - Official Anthropic skills repository
- [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/) - MITRE ATT&CK visualization
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [DeepTempo](https://deeptempo.ai) - LogLMs for security

## About DeepTempo

[DeepTempo](https://deeptempo.ai) enables the detection of especially advanced threats using a LogLM, a foundation model or embedded context model that generates embeddings and MITRE ATT&CK predictions from raw logs.
