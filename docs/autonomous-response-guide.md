# Autonomous Response Agent Guide

## Overview

The **Auto-Response Agent** (🤖) is a specialized AI agent that automatically correlates alerts from multiple sources and takes containment actions when confidence thresholds are met.

## What It Does

### 1. **Multi-Source Correlation**
- Pulls alerts from Tempo Flow (network analytics)
- Pulls alerts from CrowdStrike (endpoint detections)
- Correlates based on IP, time, behavior patterns
- Calculates confidence scores

### 2. **Confidence-Based Decision Making**
- **≥ 0.90**: Automatic isolation + alert senior analyst
- **0.85-0.89**: Automatic isolation + request review
- **0.70-0.84**: Recommend isolation, wait for approval
- **< 0.70**: Monitor and escalate for manual review

### 3. **Automatic Containment**
- Network isolates compromised hosts via CrowdStrike
- Only acts when confidence >= 0.85
- Provides full audit trail
- Documents all reasoning

## Tools Available

### Tempo Flow Tools
- **`get_tempo_flow_alert`** - Get network flow alerts by IP/alert ID
- **`get_flow_statistics`** - Get network statistics for an IP

### CrowdStrike Tools
- **`get_crowdstrike_alert_by_ip`** - Get endpoint alerts for an IP
- **`crowdstrike_foundry_isolate`** - Network isolate a host (requires confidence >= 0.85)
- **`crowdstrike_foundry_unisolate`** - Remove isolation after remediation
- **`get_host_status`** - Check current isolation status

## Example Usage

### Scenario: Investigate Suspicious IP

**You:** "Investigate IP 192.168.1.100 and take action if needed"

**Agent Flow:**
```
1. Call get_tempo_flow_alert(source_ip="192.168.1.100")
   → Finds: Lateral movement to multiple hosts via SMB

2. Call get_crowdstrike_alert_by_ip(ip_address="192.168.1.100")
   → Finds: Ransomware behavior detected on WORKSTATION-01

3. Correlate:
   - Same IP address ✓
   - Time correlation: Within 5 minutes ✓
   - Behavioral correlation: Lateral movement + ransomware ✓
   - Critical severity on both ✓

4. Calculate Confidence:
   - Multiple corroborating alerts: +0.20
   - Critical severity: +0.15
   - Lateral movement: +0.15
   - Ransomware behavior: +0.25
   - Time correlation: +0.10
   - TOTAL: 0.85

5. Decision: Confidence = 0.85 → Automatic isolation threshold met

6. Execute: Call crowdstrike_foundry_isolate(
     ip_address="192.168.1.100",
     reason="Confirmed ransomware with lateral movement",
     confidence=0.85
   )

7. Report: "Host 192.168.1.100 (WORKSTATION-01) has been isolated due to 
   confirmed ransomware activity with 85% confidence. Lateral movement 
   to 2 additional hosts detected. Recommend immediate forensic analysis."
```

## Confidence Scoring

### Scoring Criteria

| Factor | Score | Description |
|--------|-------|-------------|
| Multiple corroborating alerts | +0.20 | Same IP in multiple systems |
| Critical severity detection | +0.15 | Critical-level alerts |
| Lateral movement indicators | +0.15 | Evidence of spreading |
| Known malware signatures | +0.20 | Confirmed malware family |
| Active C2 communications | +0.20 | Command & control detected |
| Ransomware behavior | +0.25 | File encryption activity |
| Time correlation (<5 min) | +0.10 | Alerts within 5 minutes |
| Geographic anomalies | +0.10 | Unusual locations |

### Example Calculations

**High Confidence (0.92):**
```
Ransomware detected: 0.25
+ Lateral movement: 0.15
+ Critical severity: 0.15
+ Multiple alerts: 0.20
+ Time correlation: 0.10
+ Known malware: 0.20
= 1.05 (capped at 1.0, reported as 0.92)
```

**Medium Confidence (0.75):**
```
Suspicious PowerShell: 0.10
+ High severity: 0.10
+ Multiple alerts: 0.20
+ Time correlation: 0.10
+ Anomalous network: 0.15
= 0.65 (needs manual review)
```

## Safety Features

### Built-in Safeguards
1. **Confidence threshold**: Never isolates below 0.85
2. **Reason required**: Must provide justification
3. **Audit trail**: All actions logged
4. **Check isolation status**: Prevents duplicate isolation
5. **Human oversight**: Recommends review for borderline cases

### What It Won't Do
- ❌ Isolate without sufficient confidence
- ❌ Take action without clear reasoning
- ❌ Skip documentation
- ❌ Ignore safety checks

## Mock Data

The current implementation uses mock data for testing:

### Tempo Flow Alerts
- **flow-001**: SMB lateral movement from 192.168.1.100 (high severity, 0.85 confidence)
- **flow-002**: RDP connection from 192.168.1.100 (critical severity, 0.92 confidence)

### CrowdStrike Alerts
- **cs-alert-001**: Ransomware on 192.168.1.100/WORKSTATION-01 (critical, 0.95 confidence)
- **cs-alert-002**: Suspicious PowerShell on 10.0.0.50/SERVER-DMZ-01 (high, 0.88 confidence)

## Integration with Real Systems

To connect to real systems, update these files:

### Tempo Flow Integration
Edit `mcp_servers/tempo_flow_server/server.py`:
```python
# Replace MOCK_FLOW_ALERTS with actual API calls
import requests

def get_tempo_flow_alerts(ip_address):
    response = requests.get(
        f"https://tempo-flow-api.example.com/alerts",
        params={"ip": ip_address},
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    return response.json()
```

### CrowdStrike Integration
Edit `mcp_servers/crowdstrike_server/server.py`:
```python
# Replace mock functions with CrowdStrike Falcon API
from falconpy import Hosts, Detects

def get_crowdstrike_alerts(ip_address):
    falcon = Detects(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    response = falcon.query_detects(filter=f"device.local_ip:'{ip_address}'")
    return response
```

## Workflow Examples

### Example 1: Automatic Isolation

```
User: "Check IP 192.168.1.100 for threats"

Agent:
1. Gathering data from Tempo Flow...
   → Found 2 alerts: SMB lateral movement + RDP connection
   
2. Gathering data from CrowdStrike...
   → Found 1 alert: Ransomware behavior on WORKSTATION-01
   
3. Correlation Analysis:
   - IP match: 192.168.1.100 ✓
   - Time match: All within 7 minutes ✓
   - Behavior match: Lateral movement + malware ✓
   - Severity: Critical ✓
   
4. Confidence Calculation:
   - Ransomware: +0.25
   - Lateral movement: +0.15
   - Critical severity: +0.15
   - Multiple alerts: +0.20
   - Time correlation: +0.10
   - Total: 0.85
   
5. DECISION: Confidence 0.85 meets automatic isolation threshold
   
6. EXECUTING: Isolating host 192.168.1.100...
   ✓ Host isolated successfully
   
7. RESULT:
   - Host: WORKSTATION-01 (192.168.1.100)
   - Action: Network isolated
   - Reason: Confirmed ransomware with lateral movement
   - Confidence: 85%
   - Status: Contained
   
   NEXT STEPS:
   - Conduct forensic analysis
   - Identify patient zero
   - Check lateral movement targets
   - Remediate threat
   - Consider unisolation after cleanup
```

### Example 2: Manual Review Required

```
User: "Analyze alerts for 10.0.0.50"

Agent:
1. Gathering data from Tempo Flow...
   → No alerts found
   
2. Gathering data from CrowdStrike...
   → Found 1 alert: Suspicious PowerShell execution
   
3. Correlation Analysis:
   - Single source alert
   - No network correlation
   - High severity (not critical)
   
4. Confidence Calculation:
   - High severity: +0.10
   - PowerShell execution: +0.10
   - Total: 0.20
   
5. DECISION: Confidence 0.20 is below automatic threshold (0.85)
   
6. RECOMMENDATION: Manual review required
   
7. ANALYSIS:
   - Insufficient correlation for automatic action
   - Single detection source
   - Could be legitimate admin activity
   - Recommend: Monitor for 1 hour, check user context
   
   SUGGESTED ACTIONS:
   - Verify user account legitimacy
   - Check PowerShell command history
   - Monitor for additional suspicious activity
   - Escalate if pattern continues
```

## Best Practices

### When to Use Auto-Response Agent
✅ **Use for:**
- Investigating specific IPs with potential threats
- Correlating multi-source alerts
- Getting automatic containment recommendations
- Rapid response to confirmed threats

❌ **Don't use for:**
- General SOC questions
- Policy compliance checks
- Report generation
- Threat hunting (use Threat Hunter agent instead)

### Tips for Best Results
1. **Be specific**: Provide IP addresses or alert IDs
2. **Let it think**: Agent uses extended thinking for complex correlation
3. **Trust the confidence scores**: They're based on multiple factors
4. **Review borderline cases**: Confidence 0.70-0.84 needs human judgment
5. **Check isolation status**: Use get_host_status to verify actions

## Monitoring & Audit

### What Gets Logged
- All tool calls (get alerts, isolate, etc.)
- Confidence calculations with reasoning
- Decision points and thresholds
- Actions taken and their justifications
- Timestamps for all activities

### Audit Trail Example
```json
{
  "timestamp": "2026-01-12T10:45:00Z",
  "agent": "auto_responder",
  "action": "host_isolated",
  "ip_address": "192.168.1.100",
  "hostname": "WORKSTATION-01",
  "confidence": 0.85,
  "reason": "Confirmed ransomware with lateral movement",
  "correlation_factors": [
    "tempo_flow_alert_flow-001",
    "tempo_flow_alert_flow-002",
    "crowdstrike_alert_cs-alert-001"
  ],
  "next_steps": [
    "Conduct forensic analysis",
    "Remediate threat",
    "Consider unisolation"
  ]
}
```

## Troubleshooting

### Agent not isolating when it should?
- Check confidence calculation in agent's response
- Verify threshold is set to 0.85
- Ensure CrowdStrike tools are available

### Agent isolating too aggressively?
- Review confidence scoring criteria
- Adjust thresholds in agent system prompt
- Add additional safety checks

### No alerts found?
- Verify MCP servers are running
- Check mock data in server files
- Ensure IP addresses match test data

## Summary

The Auto-Response Agent provides:
- ✅ **Automatic correlation** across multiple alert sources
- ✅ **Confidence-based decisions** with clear thresholds
- ✅ **Autonomous containment** when confidence is high
- ✅ **Full audit trail** for all actions
- ✅ **Safety guardrails** to prevent false positives
- ✅ **Human oversight** for borderline cases

**Use it when**: You need rapid, automated response to correlated threats with high confidence.

