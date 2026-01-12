# Agent Approval Integration - Summary

## ✅ Done!

**All SOC agents can now submit actions to the approval queue!**

---

## What Was Added

### 1. Approval MCP Server
**New Files:**
- `mcp_servers/approval_server/__init__.py`
- `mcp_servers/approval_server/server.py`

**MCP Tools Available:**
- `create_approval_action` - Submit actions to approval queue
- `list_approval_actions` - View pending/approved actions
- `get_approval_action` - Get action details
- `approve_action` - Approve pending action
- `reject_action` - Reject pending action
- `get_approval_stats` - Get approval statistics
- `correlate_and_create_action` - Auto-responder's special tool

### 2. Agent Integration
**Updated `services/soc_agents.py`:**

Agents with approval access:
- ✅ **Auto-Responder Agent** - Full approval workflow + correlation
- ✅ **Investigation Agent** - Can propose containment actions
- ✅ **Response Agent** - Can submit response actions  
- ✅ **Threat Hunter Agent** - Can submit actions for threats found

### 3. Configuration
**Updated `mcp-config.json`:**
- Added approval server configuration
- Ready for Claude Desktop integration

---

## How It Works

### Confidence-Based Approval

| Confidence | What Happens |
|------------|--------------|
| ≥ 0.90 | 🟢 **Auto-approved & executed** |
| 0.85-0.89 | 🟡 **Auto-approved with review flag** |
| 0.70-0.84 | 🟠 **Requires manual approval** |
| < 0.70 | ⚪ **Monitor only** |

### Example Flow

```
1. Agent investigates suspicious activity
2. Agent finds evidence of ransomware
3. Agent calculates confidence: 0.92
4. Agent uses create_approval_action tool
5. Action is auto-approved (confidence ≥ 0.90)
6. Action executes automatically
7. Analyst is notified
```

---

## Quick Examples

### Auto-Responder Agent

```
Analyst: "Investigate finding-001 and take action if needed"

Auto-Responder:
[Uses correlate_and_create_action]
"Correlated Tempo Flow + CrowdStrike alerts
 Confidence: 93% 
 Action: Host isolated automatically
 Reason: Confirmed ransomware + C2 + lateral movement"
```

### Investigation Agent

```
Analyst: "Investigate suspicious activity on 192.168.1.100"

Investigator:
[Investigates, finds threats]
[Uses create_approval_action]
"Found evidence of compromise. 
 Submitted isolation action (confidence: 88%)
 Action pending your approval in the queue."
```

### Response Agent

```
Analyst: "What should we do about the DMZ server alerts?"

Responder:
[Analyzes situation]
[Uses create_approval_action]
"Recommend network isolation.
 Submitted action with 82% confidence.
 Requires your approval - see action-003 in queue."
```

### Threat Hunter

```
Analyst: "Hunt for signs of APT29"

Hunter:
[Searches across data]
[Finds IOCs, uses create_approval_action]
"Found 3 hosts with matching IOCs.
 Created blocking actions - 2 auto-approved, 1 needs review."
```

---

## Configuration

### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "approval": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "mcp_servers.approval_server.server"],
      "cwd": "/path/to/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/path/to/deeptempo-ai-soc"
      }
    }
  }
}
```

### For Python

```python
from services.approval_service import get_approval_service, ActionType

approval = get_approval_service()

# Agents call this via MCP tools
action = approval.create_action(
    action_type=ActionType.ISOLATE_HOST,
    title="Isolate Compromised Host",
    target="192.168.1.100",
    confidence=0.92,
    reason="Ransomware detected",
    evidence=["finding-001"],
    created_by="auto_responder"
)
```

---

## Which Agents Can Do What?

### 🤖 Auto-Responder
- ✅ Correlate alerts automatically
- ✅ Calculate confidence scores
- ✅ Create isolation actions
- ✅ Auto-execute high-confidence actions
- ✅ List and check action status

**Primary Tool:** `correlate_and_create_action`

### 🔍 Investigation Agent
- ✅ Create containment actions during investigations
- ✅ List pending actions
- ✅ Check action status

**Primary Tool:** `create_approval_action`

### 🚨 Response Agent
- ✅ Submit response actions
- ✅ List and view actions
- ✅ Check action details

**Primary Tool:** `create_approval_action`

### 🎣 Threat Hunter
- ✅ Submit actions for discovered threats
- ✅ List pending actions

**Primary Tool:** `create_approval_action`

---

## Benefits

### For Agents
✅ Can autonomously propose security actions  
✅ Actions tracked with full audit trail  
✅ High-confidence actions execute immediately  
✅ Low-confidence actions get human review  

### For Analysts
✅ AI agents assist with response recommendations  
✅ Clear confidence scores aid decision-making  
✅ All actions have detailed reasoning  
✅ Can approve/reject from UI or chat  

### For the SOC
✅ Faster response to high-confidence threats  
✅ Consistent action-taking methodology  
✅ Complete audit trail for compliance  
✅ Human oversight for edge cases  

---

## Safety Features

1. **Confidence Thresholds** - Only ≥90% auto-executes
2. **Evidence Required** - All actions must include evidence
3. **Clear Reasoning** - Detailed justification required
4. **Human Override** - Analysts can always intervene
5. **Audit Trail** - Every action logged with full context
6. **Status Tracking** - Monitor approval → execution → results

---

## Documentation

- **Full Guide**: `docs/approval-workflow-agents.md`
- **Approval Service**: `services/approval_service.py`
- **Autonomous Response**: `services/autonomous_response_service.py`
- **Agent Profiles**: `services/soc_agents.py`

---

## Testing

### Test Approval Creation

```python
from services.approval_service import get_approval_service, ActionType

approval = get_approval_service()

# Test action creation
action = approval.create_action(
    action_type=ActionType.ISOLATE_HOST,
    title="Test Isolation",
    description="Testing approval workflow",
    target="192.168.1.100",
    confidence=0.92,
    reason="Test",
    evidence=["test-001"]
)

print(f"Action {action.action_id} status: {action.status}")
# Output: "Action action-XXX status: approved" (auto-approved)
```

### Test in UI

1. Open DeepTempo AI SOC
2. Navigate to **Dashboard → Approval Queue**
3. Create a test action via Python (as above)
4. See action appear in queue
5. Approve/reject from UI

### Test with Claude

```
You: "Create a test isolation action for 192.168.1.100 with 85% confidence"

Agent: [Uses create_approval_action]
"Action created: action-20260112-003
 Status: Auto-approved (85% confidence)
 Target: 192.168.1.100
 Flagged for review due to being below 90% threshold."
```

---

## Summary

**✅ All agents can submit actions**  
**✅ 7 MCP tools available**  
**✅ Confidence-based auto-approval**  
**✅ Full integration with existing workflow**  
**✅ No linting errors**  
**✅ Fully documented**  

Your agents are now empowered to take autonomous action with appropriate oversight! 🚀

