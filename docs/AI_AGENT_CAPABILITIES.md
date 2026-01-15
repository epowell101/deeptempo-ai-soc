# AI Agent Capabilities - Complete Access Overview

**Last Updated:** January 15, 2026  
**Status:** ✅ Full Access Enabled

## Overview

AI agents now have **complete read and modify access** to all system functionality through MCP (Model Context Protocol) tools. Agents can perform investigations, manage cases, query logs, create visualizations, and take response actions autonomously.

---

## 🔍 Data Access

### Findings Management
✅ **Full CRUD Access** via `deeptempo-findings` server

**Available Actions:**
- `list_findings` - Query findings with filters (severity, data_source, cluster_id, anomaly_score)
- `get_finding` - Retrieve complete finding details including embeddings and MITRE predictions
- `nearest_neighbors` - Find similar findings using embedding similarity
- `technique_rollup` - Get MITRE ATT&CK technique statistics across findings

**What Agents Can Do:**
- Search for specific types of threats
- Find patterns across multiple findings
- Correlate related security events
- Analyze technique prevalence

---

### Case Management
✅ **Full CRUD Access** via `deeptempo-findings` server

**Available Actions:**
- `list_cases` - List cases with filters (status, priority, assignee)
- `get_case` - Get full case details with findings, notes, timeline, activities
- `create_case` - Create new investigation cases from findings
- `update_case` - Update status, priority, assignee, add notes
- `add_finding_to_case` - Link additional findings to cases
- `remove_finding_from_case` - Unlink findings from cases

**What Agents Can Do:**
- Create cases during investigations
- Update case status as investigation progresses
- Add investigation notes and findings
- Manage case lifecycle from creation to resolution
- Link related findings together

---

### Log Analysis & Forensics
✅ **Full Access** via `timesketch` server

**Available Actions:**
- `list_sketches` - List all investigation workspaces
- `get_sketch` - Get sketch details and timelines
- `create_sketch` - Create new investigation workspace
- `search_timesketch` - Search logs using Lucene syntax
- `export_to_timesketch` - Export findings/cases to timeline

**What Agents Can Do:**
- Query logs during investigations
- Search for specific events or patterns
- Create forensic timelines
- Export investigation data for analysis
- Build timeline narratives

**Example Queries:**
- "Search logs for failed login attempts from IP 10.0.1.15"
- "Find all PowerShell executions in the last 24 hours"
- "Export case-20260115-abc123 to Timesketch timeline"

---

### MITRE ATT&CK Analysis
✅ **Full Access** via `attack-layer` server

**Available Actions:**
- `get_attack_layer` - Get current ATT&CK Navigator layer
- `get_technique_rollup` - Get technique statistics with counts and severities
- `get_findings_by_technique` - Get all findings for a specific technique
- `get_tactics_summary` - Get summary of tactics detected
- `create_attack_layer` - Generate ATT&CK visualization from findings/cases

**What Agents Can Do:**
- Analyze attack technique prevalence
- Identify most common tactics
- Generate visualizations for reports
- Map findings to MITRE framework
- Track technique trends

**Example Usage:**
- "What are the top 10 MITRE techniques detected?"
- "Create an ATT&CK layer for case-20260115-abc123"
- "Show me all findings with technique T1071"

---

## 🛡️ Security Operations

### Approval Workflow
✅ **Full Management** via `approval` server

**Available Actions:**
- `create_approval_action` - Submit security actions (isolate host, block IP, etc.)
- `list_approval_actions` - List pending/approved/rejected actions
- `get_approval_action` - Get action details
- `approve_action` - Approve pending actions
- `reject_action` - Reject actions with reason
- `get_approval_stats` - Get approval statistics
- `correlate_and_create_action` - Advanced: Correlate alerts and auto-create action

**Auto-Approval Thresholds:**
- Confidence >= 0.90: Auto-approved
- Confidence 0.85-0.89: Auto-approved with flag
- Confidence 0.70-0.84: Requires manual approval
- Confidence < 0.70: Monitor only

**What Agents Can Do:**
- Propose containment actions
- Auto-execute high-confidence responses
- Track action status
- Provide evidence for decisions

---

## 🔗 Integrations

### Threat Intelligence
✅ **Access via configured integrations**

**Available Servers:**
- **VirusTotal** - File/URL/IP/domain reputation
- **Shodan** - IP/host information and vulnerabilities
- **AlienVault OTX** - Threat intelligence pulses
- **MISP** - Threat sharing platform
- **URL Analysis** - URL safety and WHOIS
- **IP Geolocation** - IP location and ASN data

**What Agents Can Do:**
- Enrich IOCs with external intelligence
- Check file/URL reputation
- Geolocate IP addresses
- Query threat databases

---

### Sandbox Analysis
✅ **Access via configured integrations**

**Available Servers:**
- **Hybrid Analysis** - File detonation and analysis
- **Joe Sandbox** - Malware behavior analysis
- **ANY.RUN** - Interactive sandbox

**What Agents Can Do:**
- Submit suspicious files for analysis
- Get malware behavior reports
- Extract IOCs from samples
- Analyze similar samples

---

### SIEM & Log Management
✅ **Access via configured integrations**

**Available Servers:**
- **Splunk** - Query logs with natural language or SPL
- **Cribl Stream** - Data pipeline management (if configured)

**What Agents Can Do:**
- Search logs across all indexes
- Generate and execute SPL queries
- Search by IP, hostname, username
- Natural language log queries

---

### Communication & Ticketing
✅ **Access via configured integrations**

**Available Servers:**
- **Slack** - Send alerts and messages
- **Jira** - Create and update tickets
- **Microsoft Teams** - Team notifications (if configured)
- **PagerDuty** - Incident management (if configured)

**What Agents Can Do:**
- Send investigation updates
- Create tickets for findings
- Escalate to on-call teams
- Notify stakeholders

---

### EDR/XDR Platforms
✅ **Access via configured integrations**

**Available Servers:**
- **CrowdStrike** - Falcon EDR queries and host isolation

**Stub Servers** (implement if needed):
- Microsoft Defender
- SentinelOne
- Carbon Black

**What Agents Can Do:**
- Query endpoint alerts
- Check host status
- Propose host isolation (via approval workflow)
- Get endpoint telemetry

---

## 🚀 Workflows & Automation

### Workflow Execution
✅ **Access** via `tempo-flow` server

**Available Actions:**
- `get_tempo_flow_alert` - Get workflow alert details
- `get_flow_statistics` - Get workflow execution stats

**What Agents Can Do:**
- Execute predefined investigation workflows
- Automate common SOC patterns
- Chain multiple actions together

---

## 📊 What AI Agents Can Do End-to-End

### Complete Investigation Workflow

1. **Detect & Triage**
   - List new findings
   - Assess severity and priority
   - Create case for investigation

2. **Investigate**
   - Search similar findings
   - Query logs in Timesketch
   - Enrich IOCs with threat intel
   - Search Splunk for related events
   - Get MITRE technique context

3. **Analyze**
   - Correlate findings
   - Build timeline of events
   - Map to MITRE ATT&CK framework
   - Generate ATT&CK visualization

4. **Respond**
   - Create approval actions
   - Propose containment measures
   - Execute high-confidence responses
   - Track action status

5. **Document**
   - Update case notes
   - Add findings to case
   - Export to Timesketch
   - Create JIRA tickets
   - Notify via Slack

6. **Close**
   - Update case status
   - Add resolution steps
   - Generate final report

---

## 🔐 Security & Governance

### Approval Requirements

**High-Confidence Actions (Auto-Approved):**
- Confidence >= 0.90
- No manual approval needed
- Logged for audit

**Medium-Confidence Actions (Manual Approval):**
- Confidence 0.70-0.89
- Requires analyst approval
- Clear evidence required

**Low-Confidence Actions (Monitor Only):**
- Confidence < 0.70
- No action taken
- Logged for review

### Audit Trail

All agent actions are logged:
- Case creation/updates
- Approval action submissions
- Log queries
- IOC enrichment
- Timeline exports
- Response actions

---

## 📝 Usage Examples

### Example 1: Full Investigation

```
Agent: Investigate finding f-20260115-abc12345

Actions taken:
1. get_finding(f-20260115-abc12345)
2. nearest_neighbors(f-20260115-abc12345, k=10)
3. search_timesketch("src_ip:10.0.1.15")
4. vt_check_ip("10.0.1.15")
5. create_case(title="Suspicious outbound connection", finding_ids=[...])
6. create_approval_action(action_type="isolate_host", target="10.0.1.15", confidence=0.92)
7. update_case(case_id="...", status="in_progress", add_note="Host isolated")
```

### Example 2: MITRE Analysis

```
Agent: What are the top attack techniques detected this week?

Actions taken:
1. get_technique_rollup(min_confidence=0.5)
2. get_findings_by_technique("T1071")
3. create_attack_layer(name="Weekly Activity", finding_ids=[...])
```

### Example 3: Timeline Forensics

```
Agent: Create a forensic timeline for case-20260115-xyz789

Actions taken:
1. get_case(case_id="case-20260115-xyz789", include_findings=True)
2. create_sketch(name="Case-20260115 Investigation")
3. export_to_timesketch(case_id="case-20260115-xyz789", timeline_name="Case Events")
4. search_timesketch("eventid:4688 AND parent_process:powershell.exe")
```

---

## 🎯 Agent Specializations

Different agents leverage these tools differently:

- **Triage Agent**: Focuses on list_findings, get_finding, create_case
- **Investigation Agent**: Uses all tools systematically
- **Threat Hunter**: Emphasizes search_timesketch, nearest_neighbors, threat intel
- **Correlator**: Focuses on nearest_neighbors, get_technique_rollup
- **Responder**: Creates approval actions, manages containment
- **Reporter**: Generates attack layers, exports timelines
- **Forensics Agent**: Heavy use of Timesketch and timeline analysis

---

## ✅ Verification

To verify agent access:

1. **Start the system:**
   ```bash
   cd /Users/mando222/Github/deeptempo-ai-soc
   ./start_web.sh
   ```

2. **In AI chat, test:**
   ```
   "List all cases"
   "Show me findings with high severity"
   "Search logs for failed logins"
   "What are the top MITRE techniques?"
   "Create a case for finding f-20260115-abc123"
   ```

3. **Check MCP server status in Settings**

---

## 📚 Documentation References

- [MCP Servers Inventory](/docs/mcp-servers-inventory.md)
- [MCP Contracts](/docs/mcp-contracts.md)
- [SOC Agents Guide](/docs/soc-agents-guide.md)
- [Case Management Restoration](/docs/CASE_MANAGEMENT_RESTORATION.md)

---

**Status:** ✅ **AI agents have full access to all functionality**

Agents can read, modify, create, and delete data across the entire system. They have the tools needed to conduct complete security investigations from detection through response and documentation.

