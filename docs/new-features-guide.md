# New Features Guide - DeepTempo AI SOC

This guide covers three major new features added to the DeepTempo AI SOC platform:

1. **Splunk MCP Server** - Natural language to SPL query generation
2. **Approval Workflow** - Human-in-the-loop for autonomous actions
3. **Investigation Workflows** - Multi-phase investigation state machine

---

## 1. Splunk MCP Server with Natural Language Queries

### Overview

The Splunk MCP Server enables Claude (via Claude Desktop or the integrated chat) to query Splunk using natural language. Instead of writing complex SPL queries, you can ask questions like "Show me all failed login attempts in the last 24 hours" and the system will generate and execute the appropriate SPL query.

### Features

- **Natural Language to SPL Translation**: Automatically generates SPL queries from plain English
- **Pre-built Query Templates**: Common security investigation patterns built-in
- **Direct Execution**: Execute generated queries against your Splunk instance
- **Entity Searches**: Quick searches by IP, hostname, username, or hash
- **Index Discovery**: List available Splunk indexes

### Configuration

#### Option 1: Environment Variables

```bash
export SPLUNK_URL="https://splunk.example.com:8089"
export SPLUNK_USERNAME="admin"
export SPLUNK_PASSWORD="your_password"
export SPLUNK_VERIFY_SSL="false"
```

#### Option 2: Config File

Create or edit `~/.deeptempo/config.json`:

```json
{
  "splunk": {
    "server_url": "https://splunk.example.com:8089",
    "username": "admin",
    "password": "your_password",
    "verify_ssl": false
  }
}
```

#### Option 3: MCP Config (for Claude Desktop)

Edit your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "splunk": {
      "command": "/path/to/deeptempo-ai-soc/venv/bin/python",
      "args": ["-m", "mcp_servers.splunk_server.server"],
      "cwd": "/path/to/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/path/to/deeptempo-ai-soc",
        "SPLUNK_URL": "https://splunk.example.com:8089",
        "SPLUNK_USERNAME": "admin",
        "SPLUNK_PASSWORD": "your_password",
        "SPLUNK_VERIFY_SSL": "false"
      }
    }
  }
}
```

### Available Tools

#### 1. `generate_spl_query`

Generate SPL query from natural language without executing it.

**Example:**
```
Query: "Find all PowerShell executions with encoded commands"
Result: index=* sourcetype=WinEventLog:Security EventCode=4688 (powershell.exe OR pwsh.exe) | table _time, Computer, User, CommandLine
```

#### 2. `execute_spl_search`

Execute a specific SPL query.

**Parameters:**
- `spl_query`: The SPL query to execute
- `earliest_time`: Start time (default: "-24h")
- `latest_time`: End time (default: "now")
- `max_results`: Maximum results (default: 100)

#### 3. `natural_language_search`

Combined tool - generates and executes in one step.

**Example queries:**
- "Show me all failed login attempts in the last 24 hours"
- "Find suspicious PowerShell activity"
- "Search for potential data exfiltration"
- "Look for lateral movement indicators"
- "Find brute force attacks"

#### 4. Entity Search Tools

- `search_by_ip`: Search for all events related to an IP address
- `search_by_hostname`: Search for all events related to a hostname
- `search_by_username`: Search for all events related to a username

#### 5. `get_splunk_indexes`

List all available Splunk indexes.

### Pre-built Query Patterns

The system recognizes these patterns and generates optimized SPL:

| Pattern | Generated Query Focus |
|---------|----------------------|
| "failed login" | Failed authentication events |
| "powershell" | PowerShell execution with command lines |
| "brute force" | Multiple failed login attempts by source |
| "c2 beacon" | High-frequency connections to external IPs |
| "data exfiltration" | Large outbound data transfers |
| "lateral movement" | Cross-host authentication patterns |
| "suspicious process" | Suspicious process executions |
| "network scan" | Port scanning behavior |
| "malware execution" | Malware-related events |
| "privilege escalation" | Privilege escalation attempts |

### Usage Examples

#### In Claude Desktop

```
You: "Use Splunk to find all failed SSH login attempts in the last 48 hours"

Claude: [Uses natural_language_search tool]
Found 47 failed SSH login attempts:
- 192.168.1.100: 23 attempts
- 10.0.0.50: 15 attempts
- 172.16.0.10: 9 attempts

Top targeted users: root (31), admin (12), ubuntu (4)
```

#### In Python

```python
from services.splunk_service import SplunkService

splunk = SplunkService(
    server_url="https://splunk.example.com:8089",
    username="admin",
    password="password",
    verify_ssl=False
)

# Search by IP
results = splunk.search_by_ip("192.168.1.100", hours=24)

# Custom SPL query
results = splunk.search(
    "index=main sourcetype=access_combined status=404 | stats count by uri",
    earliest_time="-7d"
)
```

---

## 2. Approval Workflow for Autonomous Actions

### Overview

The Approval Workflow system provides human-in-the-loop oversight for autonomous security actions. High-confidence actions (≥90%) are auto-approved, while lower-confidence actions require analyst review.

### Key Concepts

#### Confidence Thresholds

- **≥ 0.90**: Auto-approved and executed immediately
- **0.85-0.89**: Auto-approved but flagged for review
- **0.70-0.84**: Requires manual approval before execution
- **< 0.70**: Recommended for monitoring only

#### Action Types

- `ISOLATE_HOST`: Network isolation of compromised host
- `BLOCK_IP`: Block malicious IP address
- `BLOCK_DOMAIN`: Block malicious domain
- `QUARANTINE_FILE`: Quarantine malicious file
- `DISABLE_USER`: Disable compromised user account
- `EXECUTE_SPL_QUERY`: Execute sensitive Splunk query
- `CUSTOM`: Custom action type

#### Action Status

- `PENDING`: Awaiting approval
- `APPROVED`: Approved, ready for execution
- `REJECTED`: Rejected by analyst
- `EXECUTED`: Successfully executed
- `FAILED`: Execution failed

### Using the Approval Queue

#### In the UI

1. Navigate to **Dashboard → Approval Queue** tab
2. View pending actions requiring approval
3. Select an action to view details
4. Click **Approve** or **Reject**
5. Approved actions are automatically executed

#### Programmatically

```python
from services.approval_service import get_approval_service, ActionType

approval_service = get_approval_service()

# Create an action
action = approval_service.create_action(
    action_type=ActionType.ISOLATE_HOST,
    title="Isolate Compromised Workstation",
    description="Host showing ransomware behavior",
    target="192.168.1.100",
    confidence=0.92,
    reason="Ransomware detected with high confidence",
    evidence=["finding-001", "finding-002"],
    created_by="auto_responder"
)

# Action is auto-approved if confidence >= 0.90
print(f"Status: {action.status}")  # "approved"

# List pending actions
pending = approval_service.list_actions(status=ActionStatus.PENDING)

# Approve an action
approval_service.approve_action(action.action_id, approved_by="analyst")

# Reject an action
approval_service.reject_action(
    action.action_id, 
    reason="False positive - legitimate admin activity",
    rejected_by="analyst"
)
```

### Autonomous Response Integration

The autonomous response system automatically creates approval actions:

```python
from services.autonomous_response_service import get_autonomous_response_service

auto_response = get_autonomous_response_service()

# Investigate a finding and automatically respond
result = auto_response.investigate_and_respond(
    finding_id="finding-20260112-001",
    auto_execute=True
)

# Result includes:
# - Correlation analysis
# - Confidence score
# - Action taken (or pending approval)
```

### Correlation Scoring

The system calculates confidence scores based on:

- **Multiple corroborating alerts**: +0.20
- **Critical severity detections**: +0.15
- **Lateral movement indicators**: +0.15
- **Known malware signatures**: +0.20
- **Active C2 communications**: +0.20
- **Ransomware behavior**: +0.25
- **Time correlation (<5 min)**: +0.10
- **Geographic anomalies**: +0.10

### Best Practices

1. **Review Auto-Approved Actions**: Even high-confidence actions should be reviewed post-execution
2. **Document Rejections**: Always provide clear reasons when rejecting actions
3. **Adjust Thresholds**: Tune confidence thresholds based on your environment
4. **Monitor Execution**: Check execution results for failures
5. **Audit Trail**: All actions are logged with full context

---

## 3. Investigation Workflows

### Overview

Investigation Workflows provide a structured, multi-phase approach to security investigations. Each investigation progresses through defined phases, tracking context, queries, and findings along the way.

### Investigation Phases

1. **Initialize**: Set up investigation scope and objectives
2. **Gather Context**: Collect relevant data and evidence
3. **Analyze**: Deep analysis of collected data
4. **Correlate**: Find relationships and patterns
5. **Report**: Document findings and recommendations
6. **Closed**: Investigation complete

### Using Investigation Workflows

#### In the UI

1. Navigate to **Dashboard → Investigation** tab
2. Click **Create Workflow** for a case
3. Progress through phases:
   - Add notes to current phase
   - Click **Advance to Next Phase** when ready
4. Track discovered entities, hypotheses, and queries
5. View phase completion status

#### Programmatically

```python
from services.investigation_workflow_service import (
    get_workflow_service,
    InvestigationPhase
)

workflow_service = get_workflow_service()

# Create a workflow
workflow = workflow_service.create_workflow(
    case_id="case-20260112-001",
    title="Ransomware Investigation",
    description="Investigating ransomware outbreak on workstation-042",
    assigned_to="analyst@example.com",
    priority="critical"
)

# Add discovered entities
workflow_service.add_entity(
    workflow.workflow_id,
    entity_type="ip_address",
    entity_value="192.168.1.100"
)

# Add a hypothesis
workflow_service.add_hypothesis(
    workflow.workflow_id,
    hypothesis="Ransomware spread via phishing email",
    confidence=0.75,
    evidence=["finding-001", "email-log-002"]
)

# Record a query
workflow_service.add_query(
    workflow.workflow_id,
    query_type="splunk",
    query="index=windows EventCode=4688 process=*encrypt*",
    results_count=23
)

# Update current phase
workflow_service.update_phase(
    workflow.workflow_id,
    phase=InvestigationPhase.GATHER_CONTEXT,
    notes="Collected logs from affected host",
    findings=["finding-001", "finding-002"]
)

# Advance to next phase
workflow_service.advance_phase(
    workflow.workflow_id,
    notes="Context gathering complete. 5 affected hosts identified.",
    findings=["finding-001", "finding-002", "finding-003"]
)
```

### Investigation Context

Each workflow maintains rich context:

#### Entities Discovered
```python
{
    "ip_addresses": ["192.168.1.100", "10.0.0.50"],
    "hostnames": ["workstation-042", "server-dmz-01"],
    "users": ["john.doe", "admin"],
    "domains": ["malicious.com"],
    "file_hashes": ["abc123..."]
}
```

#### Queries Executed
```python
[
    {
        "timestamp": "2026-01-12T10:30:00Z",
        "type": "splunk",
        "query": "index=windows EventCode=4688",
        "results_count": 47
    }
]
```

#### Hypotheses
```python
[
    {
        "timestamp": "2026-01-12T10:35:00Z",
        "hypothesis": "Initial access via phishing",
        "confidence": 0.80,
        "evidence": ["email-001", "finding-002"],
        "status": "active"
    }
]
```

### Workflow Statistics

```python
stats = workflow_service.get_stats()
# {
#     "total": 15,
#     "active": 8,
#     "paused": 2,
#     "completed": 5,
#     "by_phase": {
#         "initialize": 2,
#         "gather_context": 3,
#         "analyze": 2,
#         "correlate": 1
#     }
# }
```

### Best Practices

1. **Create Workflows Early**: Start workflows at the beginning of investigations
2. **Document Thoroughly**: Add detailed notes at each phase
3. **Track All Entities**: Record every IP, hostname, user discovered
4. **Test Hypotheses**: Document hypotheses and update as investigation progresses
5. **Record Queries**: Log all queries run for reproducibility
6. **Review Before Advancing**: Ensure phase objectives are met before advancing

---

## Integration Examples

### Example 1: Full Investigation with All Features

```python
from services.investigation_workflow_service import get_workflow_service
from services.autonomous_response_service import get_autonomous_response_service
from services.approval_service import get_approval_service

# 1. Create investigation workflow
workflow_service = get_workflow_service()
workflow = workflow_service.create_workflow(
    case_id="case-001",
    title="Suspicious Network Activity Investigation"
)

# 2. Use Splunk to gather context
# (Would be done via Claude with natural language)
# "Search Splunk for all activity from IP 192.168.1.100 in the last 24 hours"

# 3. Record findings in workflow
workflow_service.add_entity(workflow.workflow_id, "ip_address", "192.168.1.100")
workflow_service.add_query(
    workflow.workflow_id,
    "splunk",
    "search 192.168.1.100",
    results_count=150
)

# 4. Autonomous response evaluates threat
auto_response = get_autonomous_response_service()
result = auto_response.investigate_and_respond("finding-001")

# 5. If confidence is high, action is created
if result['action']['status'] == 'pending_approval':
    # Analyst reviews in Approval Queue UI
    approval_service = get_approval_service()
    action = approval_service.get_action(result['action']['action_id'])
    
    # Approve if legitimate
    approval_service.approve_action(action.action_id, "analyst")

# 6. Advance workflow phase
workflow_service.advance_phase(
    workflow.workflow_id,
    notes="Threat confirmed and contained",
    findings=["finding-001"]
)
```

### Example 2: Claude Desktop Integration

In Claude Desktop, you can now:

```
You: "Investigate finding-20260112-001 using Splunk and recommend actions"

Claude: 
1. [Uses get_finding to load the finding]
2. [Uses natural_language_search in Splunk]
   "Search Splunk for all activity from 192.168.1.100"
3. [Analyzes correlation]
   Found 47 related events showing:
   - Multiple failed login attempts
   - Suspicious PowerShell execution
   - Outbound connection to known C2 IP
   
   Confidence: 88%
   
4. [Creates approval action]
   Created isolation action (action-20260112-001)
   Status: Pending approval (confidence below 90% threshold)
   
   Recommendation: Approve isolation to prevent lateral movement.
```

---

## Troubleshooting

### Splunk MCP Server

**Issue**: "Splunk not configured" error

**Solution**: Ensure Splunk credentials are set in environment variables or config file.

**Issue**: Connection timeout

**Solution**: Check Splunk URL, firewall rules, and SSL verification settings.

### Approval Workflow

**Issue**: Actions not auto-executing

**Solution**: Check confidence scores. Only actions with confidence ≥ 0.90 auto-execute.

**Issue**: Can't see pending actions

**Solution**: Refresh the Approval Queue tab or check data file permissions.

### Investigation Workflows

**Issue**: Can't create workflow

**Solution**: Ensure a case is selected first. Workflows must be associated with cases.

**Issue**: Phase won't advance

**Solution**: Ensure current phase is marked as complete and workflow status is "active".

---

## Data Storage

All new features store data in JSON files:

- **Approval Actions**: `data/pending_actions.json`
- **Investigation Workflows**: `data/investigation_workflows.json`
- **Splunk Config**: `~/.deeptempo/config.json`

---

## API Reference

See individual service files for complete API documentation:

- `services/splunk_service.py`
- `services/approval_service.py`
- `services/investigation_workflow_service.py`
- `services/autonomous_response_service.py`

---

## Next Steps

1. **Configure Splunk**: Set up Splunk connection for natural language queries
2. **Test Approval Workflow**: Create a test action and practice approval process
3. **Start an Investigation**: Create a workflow for an existing case
4. **Integrate with Claude**: Use these features via Claude Desktop for AI-assisted investigations

For more information, see the main README and other documentation in the `docs/` directory.

