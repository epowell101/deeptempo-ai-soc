# DeepTempo AI SOC

An **embeddings-first AI Security Operations Center** that leverages DeepTempo's LogLM for threat detection and Claude for intelligent orchestration via MCP (Model Context Protocol).

## Overview

This project demonstrates how to build an AI-powered SOC where:

- **DeepTempo LogLM** handles log analysis, embedding generation, and MITRE ATT&CK classification
- **Claude** serves as the primary analyst interface, orchestrating investigations through natural conversation
- **MCP Servers** provide the bridge, exposing SOC tools that Claude can invoke
- **Streamlit** provides a rich, interactive dashboard for visualizing attack flows.
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
python scripts/demo.py
```

### Step 3: Configure Claude Desktop

Find your config file:
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add this content (adjust paths to match your setup):

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
    },
    "timesketch": {
      "command": "/path/to/deeptempo-ai-soc/venv/bin/python",
      "args": ["-m", "mcp_servers.timesketch_server.server"],
      "cwd": "/path/to/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/path/to/deeptempo-ai-soc",
        "TIMESKETCH_MOCK": "true"
      }
    }
  }
}
```

### Step 4: Restart Claude Desktop
Quit completely (Cmd+Q on Mac, Alt+F4 on Windows) and reopen.

### Step 5: Start Investigating!

Try these prompts in Claude Desktop:

```
"Show me all high severity findings"
"Find findings similar to f-20260109-9bfe5ba7"
"What MITRE ATT&CK techniques are detected?"
"Create a case for the beaconing cluster"
"Sync all findings to Timesketch"
```

## Attack Flow Visualization (Streamlit)

This project includes a Streamlit dashboard to visualize the entire attack flow, from initial compromise to data exfiltration.

### Step 1: Install Dependencies

```bash
pip install streamlit plotly pandas networkx pyvis
```

### Step 2: Run the Dashboard

```bash
streamlit run streamlit_app/app.py
```

This will open the dashboard in your browser, where you can explore:
- **Attack Graph**: An interactive network graph of all entities.
- **Kill Chain Timeline**: A visual timeline of the attack phases.
- **Data Exfiltration Flow**: A Sankey diagram showing how data was exfiltrated.
- **MITRE ATT&CK Heatmap**: A bar chart of detected techniques.

## Timesketch Integration

### Mock Mode (Default)

The Timesketch server runs in mock mode by default, simulating functionality without requiring a real server. Perfect for demos.

### Live Timesketch Server

To use a real Timesketch server:

1. **Start Timesketch with Docker:**
```bash
cd docker
docker compose up -d
# Wait 2-3 minutes for services to start
```

2. **Access Timesketch** at http://localhost:5000 (login: dev / dev)

3. **Update Claude Desktop config** to disable mock mode:
```json
"env": {
  "PYTHONPATH": "/path/to/deeptempo-ai-soc",
  "TIMESKETCH_HOST": "http://localhost:5000",
  "TIMESKETCH_USER": "dev",
  "TIMESKETCH_PASSWORD": "dev",
  "TIMESKETCH_MOCK": "false"
}
```

4. **Restart Claude Desktop**

### Timesketch Tools

| Tool | Description |
|------|-------------|
| `sync_findings_to_timesketch` | One-click: creates sketch and uploads all findings |
| `create_timesketch_sketch` | Create a new investigation sketch |
| `upload_findings_to_timesketch` | Upload findings to an existing sketch |
| `search_timesketch` | Search events in a sketch |
| `get_timesketch_url` | Get URL to view a sketch |
| `get_timesketch_status` | Check connection status |

## ATT&CK Navigator Visualization

Generate and view MITRE ATT&CK technique coverage:

1. Run the demo: `python scripts/demo.py`
2. Open https://mitre-attack.github.io/attack-navigator/
3. Click **"Open Existing Layer"** → **"Upload from local"**
4. Select `data/demo_layer.json`

## MCP Tools Reference

### Findings Server

| Tool | Description |
|------|-------------|
| `list_findings` | List findings with filters (severity, data_source, cluster) |
| `get_finding` | Get details for a specific finding |
| `nearest_neighbors` | Find similar findings using embeddings |
| `technique_rollup` | Get MITRE ATT&CK technique statistics |

### Evidence Server

| Tool | Description |
|------|-------------|
| `get_evidence` | Get raw log evidence for a finding |
| `search_evidence` | Search across all evidence |

### Case Store
| Tool | Description |
|------|-------------|
| `list_cases` | List all investigation cases |
| `get_case` | Get details for a specific case |
| `create_case` | Create a new investigation case |
| `update_case` | Update case status, priority, or notes |

## Troubleshooting

### Python Version

MCP requires Python 3.10+:
```bash
python3 --version
```

On Mac with Homebrew:
```bash
brew install python@3.12
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv venv
```

### Test Server Manually

```bash
cd /path/to/deeptempo-ai-soc
source venv/bin/activate
python -m mcp_servers.deeptempo_findings_server.server
```

### Check Logs

```bash
cat ~/Library/Logs/Claude/mcp-server-deeptempo-findings.log
```

### Kill Stale Processes

```bash
pkill -f "mcp_servers"
```

### Timesketch Docker Issues

- Ensure Docker has at least 8GB RAM
- Wait 2-3 minutes for initial startup
- Check logs: `docker compose logs -f timesketch`

## Project Structure

```
deeptempo-ai-soc/
├── streamlit_app/             # Streamlit attack flow visualization
├── mcp_servers/                 # MCP server implementations
│   ├── deeptempo_findings_server/
│   ├── evidence_snippets_server/
│   ├── case_store_server/
│   └── timesketch_server/       # Timesketch integration
├── adapters/                    # External system adapters
│   ├── deeptempo_offline_export/
│   └── timesketch_adapter/
├── docker/                      # Docker Compose for Timesketch
├── scripts/                     # Demo and utility scripts
├── data/                        # Sample data and outputs
└── docs/                        # Additional documentation
```

## Roadmap

- [x] v0.1: File-based MCP servers with sample data
- [x] v0.2: Timesketch integration for timeline visualization
- [x] v0.3: Streamlit dashboard for attack flow visualization
- [ ] v0.4: Real DeepTempo LogLM integration
- [ ] v1.0: Full SaaS API integration

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## References


- [Timesketch](https://timesketch.org/) - Timeline analysis platform
- [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/) - MITRE ATT&CK visualization
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [DeepTempo](https://deeptempo.ai) - LogLM for security
