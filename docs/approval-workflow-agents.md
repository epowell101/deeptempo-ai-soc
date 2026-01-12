# Approval Workflow & Agent Integration

## Overview

All SOC agents can now submit actions to the approval queue! This enables AI-assisted decision-making with human oversight for critical security actions.

## How It Works

### 1. Agents Can Submit Actions

Any agent can use the **Approval MCP Server** to:
- Create approval actions
- List pending actions
- View action details
- Check approval statistics

### 2. Auto-Responder Has Special Powers

The **Auto-Responder Agent** has an additional tool:
- `correlate_and_create_action` - Automatically correlate alerts and create actions with confidence scoring

### 3. Confidence-Based Approval

Actions are handled based on confidence:

| Confidence | Behavior | Example |
|------------|----------|---------|
| ≥ 0.90 | **Auto-approved & executed** | Confirmed ransomware + C2 + lateral movement |
| 0.85-0.89 | **Auto-approved with flag** | High severity + temporal correlation |
| 0.70-0.84 | **Requires approval** | Moderate indicators, needs review |
| < 0.70 | **Monitor only** | Single low-confidence alert |

## Agents with Approval Access

### 🤖 Auto-Responder Agent
**Full approval workflow integration**

Tools:
- `correlate_and_create_action` - Correlate alerts and auto-create actions
- `create_approval_action` - Submit actions
- `list_approval_actions` - View pending actions
- `get_approval_action` - Get action details

**Use Case:**
```
Agent correlates Tempo Flow + CrowdStrike alerts
→ Calculates confidence: 0.92
→ Creates isolation action (auto-approved)
→ Executes isolation
→ Reports to analyst
```

### 🔍 Investigation Agent
**Can propose actions during investigations**

Tools:
- `create_approval_action` - Submit containment actions
- `list_approval_actions` - Check pending actions

**Use Case:**
```
Agent investigates suspicious activity
→ Finds evidence of compromise
→ Submits isolation action with 0.88 confidence
→ Action goes to approval queue
→ Analyst reviews and approves
```

### 🚨 Response Agent
**Can recommend and submit response actions**

Tools:
- `create_approval_action` - Submit response actions
- `list_approval_actions` - View action queue
- `get_approval_action` - Check action status

**Use Case:**
```
Agent recommends containment
→ Submits "Isolate Host" action
→ Includes evidence and reasoning
→ Analyst approves
→ Action executes
```

### 🎣 Threat Hunter
**Can submit actions for discovered threats**

Tools:
- `create_approval_action` - Submit actions for threats found
- `list_approval_actions` - View hunting-related actions

**Use Case:**
```
Agent discovers active C2 beaconing
→ Submits blocking action
→ Includes IOCs and confidence
→ Goes to approval queue
```

## MCP Tools Reference

### `create_approval_action`

Submit an action to the approval queue.

**Parameters:**
```json
{
  "action_type": "isolate_host|block_ip|block_domain|quarantine_file|disable_user|execute_spl_query|custom",
  "title": "Short title",
  "description": "Detailed description",
  "target": "IP/hostname/username/etc",
  "confidence": 0.0-1.0,
  "reason": "Why this action is needed",
  "evidence": ["finding-001", "alert-002"],
  "created_by": "agent_name",
  "parameters": {} // Optional
}
```

**Response:**
```json
{
  "success": true,
  "action_id": "action-20260112-001",
  "status": "approved|pending",
  "requires_approval": false,
  "message": "Action created successfully..."
}
```

### `list_approval_actions`

List actions with optional filters.

**Parameters:**
```json
{
  "status": "pending|approved|rejected|executed|failed", // optional
  "action_type": "isolate_host|...", // optional
  "requires_approval": true|false // optional
}
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "actions": [
    {
      "action_id": "action-001",
      "action_type": "isolate_host",
      "title": "Isolate Compromised Host",
      "target": "192.168.1.100",
      "confidence": 0.92,
      "status": "approved",
      "requires_approval": false,
      "created_at": "2026-01-12T10:30:00Z",
      "created_by": "auto_responder",
      "evidence_count": 3
    }
  ]
}
```

### `get_approval_action`

Get detailed information about a specific action.

**Parameters:**
```json
{
  "action_id": "action-20260112-001"
}
```

### `correlate_and_create_action` (Auto-Responder Only)

Advanced tool that correlates alerts and automatically creates actions.

**Parameters:**
```json
{
  "finding_id": "finding-20260112-001",
  "auto_execute": true // default: true
}
```

**Response:**
```json
{
  "success": true,
  "investigation_result": {
    "finding_id": "finding-001",
    "target": "192.168.1.100",
    "correlation": {
      "confidence": 0.92,
      "indicators": ["ransomware", "c2_communication"],
      "evidence": ["Tempo Flow: finding-001", "CrowdStrike: 2 alerts"],
      "reasoning": [
        "Ransomware behavior detected (T1486)",
        "C2 communication detected (T1071)",
        "Critical severity in CrowdStrike"
      ]
    },
    "action": {
      "status": "executed",
      "action_id": "action-001",
      "message": "Host 192.168.1.100 isolated automatically"
    }
  }
}
```

## Usage Examples

### Example 1: Investigator Finds Threat

**Conversation with Claude:**
```
Analyst: "Investigate finding-20260112-001 for suspicious activity"

Investigation Agent:
1. [Gets finding details]
2. [Searches related logs]
3. [Finds evidence of compromise]
4. "I found evidence of active ransomware. Creating isolation action..."
5. [Uses create_approval_action with confidence: 0.88]
6. "Action submitted to approval queue (requires approval due to 88% confidence)"

Analyst: "Show me the action details"

Investigation Agent:
[Uses get_approval_action]
"Action: Isolate Host 192.168.1.100
 Evidence: finding-001, finding-002, splunk-results
 Confidence: 88%
 Status: Pending approval
 
 Would you like me to provide more context or approve this action?"
```

### Example 2: Auto-Responder in Action

**Triggered by New Finding:**
```python
# Automatic workflow
auto_response = get_autonomous_response_service()
result = auto_response.investigate_and_respond("finding-001")

# Result:
{
  "correlation": {
    "confidence": 0.93,
    "indicators": ["ransomware", "lateral_movement"]
  },
  "action": {
    "status": "executed",
    "action_id": "action-001",
    "message": "Host isolated automatically (93% confidence)"
  }
}
```

### Example 3: Response Agent Recommends Action

**Conversation with Claude:**
```
Analyst: "What should we do about the alerts on server-dmz-01?"

Response Agent:
1. [Analyzes alerts and context]
2. "Based on the indicators, I recommend network isolation. Submitting action..."
3. [Uses create_approval_action with confidence: 0.82]
4. "Isolation action created (action-002). 
    Confidence: 82% - requires your approval.
    Evidence includes: port scanning, suspicious outbound connections, 
    and failed authentication attempts."

Analyst: "Approve it"

Response Agent:
[Uses approve_action]
"Action approved and queued for execution."
```

### Example 4: Threat Hunter Discovers IOCs

**Conversation with Claude:**
```
Analyst: "Hunt for signs of the new ransomware variant"

Threat Hunter Agent:
1. [Searches across data sources]
2. "Found 3 hosts with matching IOCs. Creating blocking actions..."
3. [Creates 3 separate actions for each host]
4. "Submitted 3 actions:
    - action-003: Block 192.168.1.100 (confidence: 0.87)
    - action-004: Block 192.168.1.101 (confidence: 0.85)
    - action-005: Block 10.0.0.50 (confidence: 0.79 - requires approval)
    
    First two are auto-approved. Third requires your review."
```

## Configuration

### Add Approval Server to MCP Config

Edit your Claude Desktop config:

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

### Agent Configuration

Agent profiles in `services/soc_agents.py` now include approval tools in their `recommended_tools` list:

```python
recommended_tools=[
    "list_findings",
    "get_finding",
    "create_approval_action",  # NEW
    "list_approval_actions",   # NEW
    "get_approval_action"      # NEW
]
```

## Benefits

### For Agents
- ✅ Can propose security actions autonomously
- ✅ Actions are tracked with full audit trail
- ✅ High-confidence actions execute immediately
- ✅ Low-confidence actions get human review

### For Analysts
- ✅ AI agents assist with response recommendations
- ✅ Clear confidence scores help decision-making
- ✅ All actions have detailed reasoning
- ✅ Can approve/reject from UI or chat

### For the SOC
- ✅ Faster response to high-confidence threats
- ✅ Consistent action-taking methodology
- ✅ Complete audit trail for compliance
- ✅ Human oversight for edge cases

## Safety Features

### 1. Confidence Thresholds
Only actions with confidence ≥ 0.90 auto-execute

### 2. Evidence Required
All actions must include supporting evidence

### 3. Clear Reasoning
Actions include detailed reasoning and context

### 4. Human Override
Analysts can always approve or reject

### 5. Audit Trail
Every action is logged with full context

### 6. Status Tracking
Actions track approval, execution, and results

## Monitoring

### Check Approval Queue
```python
from services.approval_service import get_approval_service

approval = get_approval_service()

# Get statistics
stats = approval.get_stats()
print(f"Pending: {stats['pending']}")
print(f"Approved: {stats['approved']}")
print(f"Executed: {stats['executed']}")

# List pending actions
pending = approval.list_actions(status=ActionStatus.PENDING)
for action in pending:
    print(f"{action.action_id}: {action.title} - {action.confidence:.0%}")
```

### In the UI
1. Navigate to **Dashboard → Approval Queue**
2. View all pending, approved, and executed actions
3. Approve or reject with reasoning
4. See execution results

## Best Practices

### For Agents
1. **Calculate Honest Confidence**: Base confidence on actual evidence
2. **Provide Context**: Include all relevant findings and reasoning
3. **Document IOCs**: List all indicators in evidence
4. **Be Conservative**: When in doubt, lower confidence for human review

### For Analysts
1. **Review Auto-Approved**: Check high-confidence actions post-execution
2. **Provide Feedback**: Add notes when rejecting actions
3. **Adjust Thresholds**: Tune confidence levels for your environment
4. **Monitor Trends**: Watch for patterns in agent recommendations

## Troubleshooting

### Agent Can't Create Actions

**Issue**: "Approval service not available"

**Solution**: Ensure approval MCP server is running:
```bash
python -m mcp_servers.approval_server.server
```

### Actions Not Executing

**Issue**: Approved actions not running

**Solution**: Check autonomous response service:
```python
from services.autonomous_response_service import get_autonomous_response_service

auto_response = get_autonomous_response_service()
results = auto_response.execute_approved_actions()
```

### Confidence Scores Seem Wrong

**Issue**: Actions have unexpected confidence

**Solution**: Review correlation scoring in `autonomous_response_service.py`:
- Adjust scoring weights
- Add/remove scoring criteria
- Tune thresholds

## Summary

**✅ All agents can submit actions to approval queue**
**✅ Auto-responder has advanced correlation tools**
**✅ Confidence-based auto-approval (≥0.90)**
**✅ Full audit trail and human oversight**
**✅ Available via MCP for Claude Desktop**

Agents are now empowered to autonomously propose and execute security actions while maintaining appropriate human oversight!

