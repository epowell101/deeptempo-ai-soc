# DeepTempo AI SOC - Complete Application Architecture

## Overview

The DeepTempo AI SOC is a desktop application that provides a comprehensive interface for managing security operations, integrating with Claude AI for analysis, and connecting to MCP servers for Claude Desktop integration. The application is built with PyQt6 and follows a layered architecture.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Desktop Application (PyQt6)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Main Window  │  │  Dashboard   │  │ Claude Chat │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Setup Wizard │  │ Config Mgr   │  │ MCP Manager  │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Services Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Data Service │  │Claude Service│  │ MCP Service  │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│  ┌──────────────┐                                                │
│  │Report Service│                                                │
│  └──────────────┘                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Storage (JSON Files)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Findings    │  │    Cases     │  │ ATT&CK Layer │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Servers (Optional)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Findings    │  │  Evidence    │  │  Case Store │            │
│  │   Server     │  │   Server     │  │   Server    │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Application Entry Point (`main.py`)

**Purpose**: Initializes the PyQt6 application and launches the main window.

**What it does**:
- Creates the QApplication instance
- Configures logging (console and file)
- Applies dark theme (qdarkstyle)
- Creates and displays the MainWindow
- Runs the Qt event loop

**Key Features**:
- Error handling for startup failures
- Logging to `~/.deeptempo/app.log`
- High DPI support (automatic in PyQt6)

---

### 2. Main Window (`ui/main_window.py`)

**Purpose**: The primary application shell that coordinates all views and features.

**What it does**:
- Provides menu bar, toolbar, and status bar
- Manages switching between different views (Dashboard, Claude Chat, MCP Manager)
- Handles application-level actions (setup, configuration, reports)
- Checks for required setup on startup

**Key Components**:
- **Menu Bar**: File (Setup, Config, Reports, Exit), View (Dashboard, Claude Chat, MCP Manager), Help (About)
- **Toolbar**: Quick access buttons for main views
- **Status Bar**: Shows findings/cases count, updates every 5 seconds
- **Central Widget**: Switches between Dashboard, Claude Chat, or MCP Manager

**User Interactions**:
- Keyboard shortcuts (Ctrl+D for Dashboard, Ctrl+C for Claude Chat, etc.)
- Menu-driven navigation
- Toolbar buttons for quick access

---

### 3. Dashboard (`ui/dashboard.py`)

**Purpose**: Main data visualization and management interface with tabbed views.

**What it does**:
- Provides tabbed interface for different data views
- Auto-refreshes data every 30 seconds
- Generates overall PDF reports
- Coordinates multiple widget views

**Tabs**:
1. **Findings Tab**: List and filter security findings
2. **Cases Tab**: Manage investigation cases
3. **Evidence Tab**: (Placeholder for future evidence viewing)
4. **ATT&CK Tab**: MITRE ATT&CK technique visualization

**Key Features**:
- Refresh button to manually update data
- Generate Overall Report button for PDF export
- Real-time data updates

---

### 4. Findings Widget (`ui/widgets/finding_list.py`)

**Purpose**: Display, filter, and search security findings.

**What it does**:
- Shows findings in a table with key information
- Provides filtering by severity, data source
- Enables search by ID, IP, hostname
- Allows viewing finding details
- Supports similarity search (nearest neighbors)

**Features**:
- **Filtering**: Severity dropdown, Data Source dropdown, Search box
- **Table Columns**: ID, Timestamp, Severity, Data Source, Anomaly Score, Cluster, MITRE Techniques
- **Actions**:
  - View Details: Opens detailed finding view
  - Find Similar: Uses embedding similarity to find related findings
  - Refresh: Reloads findings from data service

**Data Displayed**:
- Finding ID, timestamp, severity (color-coded)
- Data source (flow, dns, waf)
- Anomaly score
- Cluster ID
- Top MITRE ATT&CK techniques

---

### 5. Finding Detail Widget (`ui/widgets/finding_detail.py`)

**Purpose**: Shows comprehensive details for a single finding.

**What it does**:
- Displays all finding metadata
- Shows entity context (IPs, hostnames, users)
- Lists MITRE ATT&CK predictions with confidence scores
- Shows evidence links
- Provides raw JSON view (without embeddings)

**Sections**:
- Basic Information: ID, timestamp, severity, status
- Entity Context: Source/destination IPs, ports, hostnames, users
- MITRE Predictions: Techniques with confidence scores (sorted)
- Evidence Links: References to raw log files
- Raw JSON: Complete finding data (for debugging)

---

### 6. Case List Widget (`ui/widgets/case_list.py`)

**Purpose**: Manage investigation cases - create, update, and view cases.

**What it does**:
- Lists all cases in a table
- Allows creating new cases with findings
- Enables updating case status, priority, notes
- Generates PDF reports for individual cases
- Links findings to cases

**Features**:
- **Create Case Dialog**: 
  - Title, description, priority, status
  - Multi-select findings to link
- **Update Case Dialog**:
  - Change status, priority
  - Add investigation notes
- **Case Table**: ID, Title, Status, Priority, Finding Count, Created Date
- **Generate Case Report**: Creates PDF for selected case

**Case Data Structure**:
- Case ID, title, description
- Status (new, open, in-progress, resolved, closed)
- Priority (low, medium, high, critical)
- Linked finding IDs
- Timeline of events
- Investigation notes
- Tags

---

### 7. ATT&CK Layer View (`ui/widgets/attack_layer_view.py`)

**Purpose**: Visualize and manage MITRE ATT&CK technique data.

**What it does**:
- Aggregates MITRE techniques across all findings
- Shows technique statistics (count, average confidence)
- Generates ATT&CK Navigator layer files
- Exports layers for use in MITRE ATT&CK Navigator

**Features**:
- **Technique Table**: Technique ID, Finding Count, Avg Confidence, Score
- **Generate Layer**: Creates ATT&CK Navigator JSON layer
- **Export Layer**: Saves layer to file
- **Open in Navigator**: Opens MITRE ATT&CK Navigator website with instructions

**Technique Rollup**:
- Aggregates all MITRE predictions from findings
- Filters by minimum confidence (default 0.5)
- Calculates scores based on volume and confidence
- Sorts by finding count

---

### 8. Claude Chat (`ui/claude_chat.py`)

**Purpose**: Direct integration with Claude AI for security analysis.

**What it does**:
- Provides chat interface to Claude API
- Supports streaming and non-streaming responses
- Includes context-aware prompts for findings/cases
- Manages conversation history
- Stores API key securely

**Features**:
- **API Key Management**: Secure storage using keyring or config file
- **Quick Actions**:
  - Analyze Selected Finding: Sends finding to Claude for analysis
  - Correlate Findings: Analyzes relationships between findings
  - Generate Case Summary: Creates case summary using Claude
- **Chat Interface**:
  - Message input with Enter key support
  - Streaming mode toggle
  - Conversation history
  - Clear history button

**Claude Integration**:
- Uses Anthropic API (claude-3-5-sonnet model)
- Includes system prompts for security analysis
- Context-aware: Includes selected findings/cases in prompts
- Streaming responses for real-time feedback

---

### 9. MCP Manager (`ui/mcp_manager.py`)

**Purpose**: Manage and monitor MCP servers for Claude Desktop integration.

**What it does**:
- Shows status of all MCP servers
- Allows starting/stopping servers
- Displays server logs
- Tests server connectivity

**Features**:
- **Server Status Table**: Server name, status (running/stopped), actions, log button
- **Controls**: Start All, Stop All, Refresh
- **Log Viewer**: Select server, view last 100 lines of logs
- **Auto-refresh**: Updates status every 5 seconds

**MCP Servers Managed**:
1. **deeptempo-findings**: Findings queries and embedding search
2. **evidence-snippets**: Raw log evidence access
3. **case-store**: Case management

---

### 10. Setup Wizard (`ui/setup_wizard.py`)

**Purpose**: Automated environment setup for first-time users.

**What it does**:
- Checks Python version (3.10+)
- Creates virtual environment
- Installs dependencies from requirements.txt
- Installs MCP SDK
- Optionally generates sample data

**Wizard Pages**:
1. **Welcome**: Introduction and overview
2. **Options**: Choose to generate sample data
3. **Progress**: Shows setup progress with logs
4. **Completion**: Summary and next steps

**Process**:
- Runs in background thread to avoid UI freezing
- Shows real-time progress updates
- Handles errors gracefully
- Validates each step before proceeding

---

### 11. Configuration Manager (`ui/config_manager.py`)

**Purpose**: Configure Claude Desktop to use MCP servers.

**What it does**:
- Auto-detects Claude Desktop config file location (Mac/Windows)
- Auto-detects project and venv paths
- Generates MCP server configuration
- Merges with existing Claude Desktop config
- Creates backup before modifying

**Features**:
- **Path Detection**: Automatically finds Claude Desktop config directory
- **Path Browsing**: Browse buttons for project and venv paths
- **Configuration Preview**: Shows generated JSON before saving
- **Validation**: Checks paths exist, validates Python executable
- **Backup**: Creates backup of existing config before modification

**Configuration Generated**:
- Three MCP server entries (findings, evidence, case-store)
- Python executable path from venv
- Working directory (project root)
- PYTHONPATH environment variable

---

## Services Layer

### 12. Data Service (`services/data_service.py`)

**Purpose**: Unified interface for accessing and managing JSON data files.

**What it does**:
- Loads findings, cases, and ATT&CK layers from JSON files
- Provides caching (5-second TTL) for performance
- Handles data validation and format conversion
- Supports CRUD operations for cases
- Enables import/export of findings

**Key Methods**:
- `get_findings()`: Load all findings (with caching)
- `get_finding(id)`: Get specific finding
- `save_findings()`: Save findings to disk
- `get_cases()`: Load all cases
- `create_case()`: Create new case
- `update_case()`: Update existing case
- `get_demo_layer()`: Load ATT&CK Navigator layer
- `export_findings()`: Export to JSON/JSONL
- `import_findings()`: Import from JSON/JSONL

**Data Formats**:
- Handles both `{"findings": [...]}` and `[...]` formats
- Validates data structure
- Caches for performance (invalidates on save)

---

### 13. Claude Service (`services/claude_service.py`)

**Purpose**: Integration with Anthropic Claude API.

**What it does**:
- Manages API key (secure storage via keyring)
- Provides chat interface (streaming and non-streaming)
- Offers specialized analysis functions
- Handles errors and retries

**Key Methods**:
- `set_api_key()`: Store API key securely
- `chat()`: Send message, get response
- `chat_stream()`: Streaming chat responses
- `analyze_finding()`: Analyze a security finding
- `correlate_findings()`: Correlate multiple findings
- `generate_case_summary()`: Create case summary

**API Key Storage**:
- Primary: System keyring (most secure)
- Fallback: `~/.deeptempo/config.json`
- Environment variable: `ANTHROPIC_API_KEY`

**Models Used**:
- Default: `claude-3-5-sonnet-20241022`
- Configurable per call

---

### 14. MCP Service (`services/mcp_service.py`)

**Purpose**: Manage MCP server processes.

**What it does**:
- Launches MCP servers as subprocesses
- Monitors server health
- Provides server status
- Reads server logs
- Handles server lifecycle (start/stop)

**Key Classes**:
- **MCPServer**: Represents a single MCP server process
  - `start()`: Launch server
  - `stop()`: Terminate server
  - `is_running()`: Check status
  - `get_log_path()`: Get log file location

- **MCPService**: Manages all MCP servers
  - `start_server(name)`: Start specific server
  - `stop_server(name)`: Stop specific server
  - `start_all()`: Start all servers
  - `get_all_statuses()`: Get status of all servers
  - `get_server_log(name)`: Read server logs

**Server Configuration**:
- Auto-detects project root and venv
- Determines Python executable (Windows vs Unix)
- Sets PYTHONPATH environment variable
- Configures working directory

---

### 15. Report Service (`services/report_service.py`)

**Purpose**: Generate PDF reports from findings and cases.

**What it does**:
- Creates professional PDF reports using reportlab
- Generates overall SOC reports
- Creates individual case reports
- Formats data in tables and paragraphs

**Report Types**:

**Overall Report**:
- Executive summary with severity breakdown
- Cases summary table
- Detailed findings (up to 50)
- Statistics and metadata
- Color-coded tables

**Case Report**:
- Case metadata and description
- Timeline of events
- Investigation notes
- Related findings table
- Detailed finding information
- MITRE ATT&CK techniques

**Features**:
- Professional formatting with custom styles
- Color-coded severity indicators
- Tables for structured data
- Page breaks for long content
- Automatic file naming with timestamps

---

## Data Storage

### 16. JSON Data Files (`data/`)

**Purpose**: Persistent storage for application data.

**Files**:
- `findings.json`: All security findings with embeddings
- `cases.json`: All investigation cases
- `demo_layer.json`: ATT&CK Navigator layer file

**Data Structure**:
- **Findings**: Array of finding objects with:
  - finding_id, timestamp, severity, data_source
  - embedding (768-dimensional vector)
  - mitre_predictions (technique -> confidence)
  - anomaly_score, cluster_id
  - entity_context (IPs, hostnames, users)
  - evidence_links

- **Cases**: Array of case objects with:
  - case_id, title, description
  - status, priority, assignee
  - finding_ids (linked findings)
  - timeline, notes, tags
  - created_at, updated_at

---

## MCP Servers (Optional Integration)

### 17. Findings Server (`mcp_servers/deeptempo_findings_server/server.py`)

**Purpose**: Expose findings data to Claude Desktop via MCP.

**MCP Tools**:
- `list_findings()`: Filter and list findings
- `get_finding()`: Get specific finding
- `nearest_neighbors()`: Find similar findings by embedding
- `technique_rollup()`: Aggregate MITRE techniques

**Features**:
- FastMCP server implementation
- Cosine similarity for embedding search
- Filtering by severity, source, cluster, score
- JSON serialization with numpy support

---

### 18. Evidence Server (`mcp_servers/evidence_snippets_server/server.py`)

**Purpose**: Provide access to raw log evidence.

**MCP Tools**:
- `get_evidence()`: Get evidence for a finding
- `search_evidence()`: Search evidence by keyword

---

### 19. Case Store Server (`mcp_servers/case_store_server/server.py`)

**Purpose**: Manage cases from Claude Desktop.

**MCP Tools**:
- `list_cases()`: List cases with filters
- `get_case()`: Get specific case
- `create_case()`: Create new case
- `update_case()`: Update case status/priority/notes

---

## Supporting Components

### 20. Adapters (`adapters/`)

**Purpose**: Load data from external sources.

**Components**:
- `deeptempo_offline_export/loader.py`: 
  - Load findings from DeepTempo exports
  - Generate sample data for demos
  - Transform export format to internal schema

---

### 21. Demo Script (`scripts/demo.py`)

**Purpose**: Generate sample data for testing and demos.

**What it does**:
- Generates 50 sample findings with:
  - Random embeddings (768-dimensional)
  - MITRE ATT&CK predictions
  - Anomaly scores
  - Entity context
  - Clusters (beaconing, DNS tunneling, WAF attacks, lateral movement)
- Creates sample cases
- Generates ATT&CK Navigator layer
- Demonstrates core functionality

---

## Data Flow

### Typical User Workflow

1. **Startup**:
   ```
   main.py → MainWindow → Dashboard → DataService.load()
   ```

2. **View Findings**:
   ```
   User clicks Findings tab
   → FindingListWidget.refresh()
   → DataService.get_findings()
   → Load from findings.json
   → Display in table
   ```

3. **Analyze Finding**:
   ```
   User selects finding → View Details
   → FindingDetailWidget shows full details
   OR
   User clicks "Find Similar"
   → Calculate cosine similarity
   → Show top 10 similar findings
   ```

4. **Create Case**:
   ```
   User clicks "Create Case"
   → CreateCaseDialog
   → User selects findings
   → DataService.create_case()
   → Save to cases.json
   → Refresh case list
   ```

5. **Generate Report**:
   ```
   User clicks "Generate Report"
   → FileDialog for save location
   → ReportService.generate_report()
   → Load findings and cases
   → Create PDF with reportlab
   → Save to file
   ```

6. **Claude Analysis**:
   ```
   User opens Claude Chat
   → Enters API key (if needed)
   → Sends message
   → ClaudeService.chat()
   → Anthropic API call
   → Display response
   ```

7. **MCP Integration** (if configured):
   ```
   Claude Desktop → MCP Protocol
   → MCP Server (findings/evidence/case-store)
   → DataService methods
   → Return JSON to Claude
   → Claude processes and responds
   ```

---

## Key Technologies

- **PyQt6**: Desktop GUI framework
- **reportlab**: PDF generation
- **anthropic**: Claude API client
- **numpy**: Vector operations (similarity search)
- **qdarkstyle**: Dark theme
- **keyring**: Secure API key storage
- **MCP SDK**: Model Context Protocol for Claude Desktop

---

## Security Features

- **API Key Storage**: Uses system keyring when available
- **Path Validation**: Validates all file paths
- **Input Sanitization**: Sanitizes user inputs
- **Safe Subprocess**: Secure MCP server execution
- **Error Handling**: Comprehensive error handling and logging

---

## Extension Points

The application is designed for extension:

1. **New Widgets**: Add to `ui/widgets/`
2. **New Services**: Add to `services/`
3. **New MCP Tools**: Extend MCP servers
4. **New Report Types**: Extend ReportService
5. **New Data Sources**: Add adapters

---

## Summary

The DeepTempo AI SOC desktop application provides a complete interface for:
- **Viewing and managing security findings** with filtering and search
- **Creating and tracking investigation cases** with linked findings
- **Analyzing data with Claude AI** for insights and summaries
- **Generating professional PDF reports** for findings and cases
- **Integrating with Claude Desktop** via MCP servers
- **Visualizing MITRE ATT&CK techniques** and generating Navigator layers

All components work together through the services layer, which provides a clean abstraction over data storage and external APIs.

