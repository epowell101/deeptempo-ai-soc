# Quick Start - New Features

## 🚀 3 New Features in 3 Minutes

### 1️⃣ Splunk Natural Language Queries

**What**: Ask Splunk questions in plain English

**Setup** (30 seconds):
```bash
# Add to ~/.deeptempo/config.json
{
  "splunk": {
    "server_url": "https://splunk.example.com:8089",
    "username": "admin",
    "password": "password"
  }
}
```

**Try it**:
```python
from services.splunk_service import SplunkService

splunk = SplunkService("https://splunk:8089", "admin", "pass")
results = splunk.search_by_ip("192.168.1.100")
```

**In Claude Desktop**:
```
"Search Splunk for failed login attempts in the last 24 hours"
```

---

### 2️⃣ Approval Workflow

**What**: Human oversight for autonomous actions

**Try it**:
```python
from services.approval_service import get_approval_service, ActionType

approval = get_approval_service()

# Create action (auto-approves if confidence >= 90%)
action = approval.create_action(
    action_type=ActionType.ISOLATE_HOST,
    title="Isolate Compromised Host",
    target="192.168.1.100",
    confidence=0.92,
    reason="Ransomware detected",
    evidence=["finding-001"]
)

print(f"Status: {action.status}")  # "approved" (auto-approved!)
```

**In UI**:
1. Open Dashboard → **Approval Queue** tab
2. See pending actions
3. Click **Approve** or **Reject**

**Confidence Levels**:
- ≥ 90%: Auto-approved ✅
- 85-89%: Auto-approved with flag ⚠️
- 70-84%: Requires approval 🔒
- < 70%: Monitor only 👁️

---

### 3️⃣ Investigation Workflows

**What**: Structured multi-phase investigations

**Try it**:
```python
from services.investigation_workflow_service import get_workflow_service

workflow_service = get_workflow_service()

# Create workflow
workflow = workflow_service.create_workflow(
    case_id="case-001",
    title="Ransomware Investigation"
)

# Track entities
workflow_service.add_entity(workflow.workflow_id, "ip_address", "192.168.1.100")

# Add hypothesis
workflow_service.add_hypothesis(
    workflow.workflow_id,
    "Initial access via phishing",
    confidence=0.80,
    evidence=["email-001"]
)

# Advance phase
workflow_service.advance_phase(workflow.workflow_id, notes="Phase complete")
```

**In UI**:
1. Open Dashboard → **Investigation** tab
2. Click **Create Workflow**
3. Progress through phases:
   - Initialize
   - Gather Context
   - Analyze
   - Correlate
   - Report

---

## 🎯 Common Use Cases

### Use Case 1: Investigate Suspicious IP

```python
# 1. Query Splunk
from services.splunk_service import SplunkService
splunk = SplunkService(...)
events = splunk.search_by_ip("192.168.1.100", hours=24)

# 2. Create investigation workflow
from services.investigation_workflow_service import get_workflow_service
workflow_service = get_workflow_service()
workflow = workflow_service.create_workflow(
    case_id="case-001",
    title="Suspicious IP Investigation"
)

# 3. Track discovered entities
workflow_service.add_entity(workflow.workflow_id, "ip_address", "192.168.1.100")

# 4. If threat confirmed, create isolation action
from services.approval_service import get_approval_service, ActionType
approval = get_approval_service()
action = approval.create_action(
    action_type=ActionType.ISOLATE_HOST,
    target="192.168.1.100",
    confidence=0.88,
    reason="Confirmed malicious activity",
    evidence=["finding-001", "finding-002"]
)

# 5. Approve in UI (Dashboard → Approval Queue)
```

### Use Case 2: Automated Response

```python
from services.autonomous_response_service import get_autonomous_response_service

auto_response = get_autonomous_response_service()

# Automatically investigate and respond
result = auto_response.investigate_and_respond(
    finding_id="finding-001",
    auto_execute=True
)

# Result includes:
# - Correlation analysis
# - Confidence score
# - Action taken (or pending approval)
```

### Use Case 3: Natural Language Investigation

**In Claude Desktop**:
```
You: "Investigate finding-001. Search Splunk for related activity, 
      correlate with other findings, and recommend actions."

Claude:
1. [Gets finding details]
2. [Searches Splunk: "Search for activity from 192.168.1.100"]
3. [Correlates with CrowdStrike alerts]
4. [Calculates confidence: 88%]
5. [Creates approval action]

Recommendation: Isolate host 192.168.1.100
Confidence: 88%
Status: Pending approval (see Approval Queue)
```

---

## 📊 Dashboard Overview

### New Tabs

1. **🚦 Approval Queue**
   - View pending actions
   - Approve/reject with reasoning
   - See execution status
   - Auto-refresh every 5 seconds

2. **🔬 Investigation**
   - Create workflows for cases
   - Track investigation phases
   - Manage entities, hypotheses, queries
   - Advance through phases

---

## 🔧 Configuration Files

### Splunk Config
`~/.deeptempo/config.json`:
```json
{
  "splunk": {
    "server_url": "https://splunk.example.com:8089",
    "username": "admin",
    "password": "password",
    "verify_ssl": false
  }
}
```

### MCP Config (for Claude Desktop)
`~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "splunk": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "mcp_servers.splunk_server.server"],
      "cwd": "/path/to/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/path/to/deeptempo-ai-soc",
        "SPLUNK_URL": "https://splunk.example.com:8089",
        "SPLUNK_USERNAME": "admin",
        "SPLUNK_PASSWORD": "password"
      }
    }
  }
}
```

---

## 🎓 Cheat Sheet

### Splunk Queries (Natural Language)

| Say This | Gets This |
|----------|-----------|
| "failed login attempts" | Failed auth events |
| "powershell activity" | PowerShell executions |
| "brute force attacks" | Multiple failed logins |
| "c2 beaconing" | High-frequency connections |
| "data exfiltration" | Large outbound transfers |
| "lateral movement" | Cross-host auth patterns |
| "suspicious processes" | Suspicious process executions |
| "network scanning" | Port scanning behavior |

### Approval Confidence Levels

| Confidence | Action | Example |
|------------|--------|---------|
| ≥ 90% | Auto-execute | Confirmed ransomware + C2 |
| 85-89% | Auto-approve, flag | High severity + correlation |
| 70-84% | Require approval | Moderate indicators |
| < 70% | Monitor only | Single low-confidence alert |

### Investigation Phases

1. **Initialize** - Define scope
2. **Gather Context** - Collect data
3. **Analyze** - Deep analysis
4. **Correlate** - Find patterns
5. **Report** - Document findings

---

## 🆘 Troubleshooting

### Splunk Connection Issues

```bash
# Test connection
python -c "
from services.splunk_service import SplunkService
s = SplunkService('https://splunk:8089', 'admin', 'pass', verify_ssl=False)
print(s.test_connection())
"
```

### Approval Service Not Working

```bash
# Check data file
ls -la data/pending_actions.json

# Test service
python -c "
from services.approval_service import get_approval_service
a = get_approval_service()
print(a.get_stats())
"
```

### Workflow Service Issues

```bash
# Check data file
ls -la data/investigation_workflows.json

# Test service
python -c "
from services.investigation_workflow_service import get_workflow_service
w = get_workflow_service()
print(w.get_stats())
"
```

---

## 📚 Full Documentation

- **Complete Guide**: `docs/new-features-guide.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **Main README**: `README.md`

---

## 🎉 You're Ready!

All three features are now available:

✅ **Splunk Natural Language Queries** - Ask questions, get answers  
✅ **Approval Workflow** - Safe autonomous actions  
✅ **Investigation Workflows** - Structured investigations  

Start investigating! 🚀

