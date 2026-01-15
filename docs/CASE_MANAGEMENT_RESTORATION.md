# Case Management Access Restored

**Date:** January 14, 2026  
**Status:** ✅ Complete

## Problem

The `case_store_server` and `evidence_snippets_server` were removed during the January 14, 2026 MCP server cleanup because they had 0 tools implemented and appeared abandoned. However, the AI chat agents still referenced these servers in their system prompts, creating a gap where **agents couldn't access case management data**.

## Solution

Case management tools have been **integrated into the deeptempo-findings MCP server**, giving AI agents full access to both findings and cases from a single server.

---

## New Case Management Tools

The following tools are now available to AI agents via the `deeptempo-findings` MCP server:

### 1. `deeptempo-findings_list_cases`
List investigation cases with filters (status, priority, assignee)

**Example usage:**
```python
# List all open cases
list_cases(status="in_progress")

# List high-priority cases
list_cases(priority="high", limit=10)
```

### 2. `deeptempo-findings_get_case`
Get detailed case information including findings, notes, timeline, and activities

**Example usage:**
```python
# Get full case details
get_case(case_id="case-20260114-a1b2c3d4", include_findings=True)
```

### 3. `deeptempo-findings_create_case`
Create a new investigation case from findings

**Example usage:**
```python
create_case(
    title="Suspicious lateral movement investigation",
    finding_ids=["f-20260114-abc123", "f-20260114-def456"],
    description="Multiple alerts indicating potential lateral movement",
    priority="high",
    assignee="analyst@company.com",
    tags=["malware", "lateral-movement"]
)
```

### 4. `deeptempo-findings_update_case`
Update case status, priority, assignee, or add notes

**Example usage:**
```python
update_case(
    case_id="case-20260114-a1b2c3d4",
    status="resolved",
    add_note="Confirmed false positive - user account was legitimately accessing systems"
)
```

### 5. `deeptempo-findings_add_finding_to_case`
Link additional findings to an existing case

**Example usage:**
```python
add_finding_to_case(
    case_id="case-20260114-a1b2c3d4",
    finding_id="f-20260114-xyz789"
)
```

### 6. `deeptempo-findings_remove_finding_from_case`
Remove a finding from a case

**Example usage:**
```python
remove_finding_from_case(
    case_id="case-20260114-a1b2c3d4",
    finding_id="f-20260114-xyz789"
)
```

---

## Updated Files

### MCP Server
- ✅ `/mcp_servers/deeptempo_findings_server/server.py` - Added 6 case management tools

### Agent System Prompts
- ✅ `/services/claude_service.py` - Updated to reference correct case tools
- ✅ `/services/claude_agent_service.py` - Updated to reference correct case tools
- ✅ `/services/soc_agents.py` - Updated triage and investigation agent prompts

### Documentation
- ✅ `/docs/mcp-servers-inventory.md` - Updated to reflect case management integration
- ✅ `/docs/mcp-contracts.md` - Added case management tool contracts
- ✅ `/docs/CASE_MANAGEMENT_RESTORATION.md` - This document

---

## What AI Agents Can Now Do

✅ **List all cases** with filtering by status, priority, or assignee  
✅ **View case details** including all linked findings, notes, and timeline  
✅ **Create new cases** from security findings  
✅ **Update case status** as investigations progress  
✅ **Add notes** to document investigation activities  
✅ **Link findings** to cases for correlation  
✅ **Manage case lifecycle** from creation to resolution

---

## Data Flow

```
AI Agent → MCP Tool Call → deeptempo-findings server → Database Service → PostgreSQL
                                                                          ↓
                                                        Case data returned to agent
```

All case data is stored in PostgreSQL and accessed via the DatabaseService layer, ensuring consistency with the REST API that the frontend uses.

---

## Testing

To verify the AI chat has access to case management:

1. **Start the backend:**
   ```bash
   cd /Users/mando222/Github/deeptempo-ai-soc
   ./start_web.sh
   ```

2. **In the AI chat, try these commands:**
   ```
   "List all open cases"
   "Show me case-20260114-12345678"
   "Create a new case for findings f-20260114-abc123 and f-20260114-def456"
   "Update case-20260114-12345678 status to in_progress"
   ```

3. **Check available tools:**
   The AI should have access to these tools:
   - `deeptempo-findings_list_cases`
   - `deeptempo-findings_get_case`
   - `deeptempo-findings_create_case`
   - `deeptempo-findings_update_case`
   - `deeptempo-findings_add_finding_to_case`
   - `deeptempo-findings_remove_finding_from_case`

---

## Benefits

✅ **Full case access restored** - AI agents can now work with cases  
✅ **Consolidated server** - Findings + cases in one MCP server  
✅ **Consistent data** - Uses same PostgreSQL database as REST API  
✅ **Better workflow** - Agents can create and manage cases during investigations  
✅ **Documentation updated** - All prompts and docs now reference correct tools

---

## Next Steps

1. ✅ Case management tools implemented and tested
2. ⏳ Test end-to-end in AI chat interface
3. ⏳ Verify case creation from agent workflows
4. ⏳ Monitor for any issues with case data access

---

## Technical Notes

- Case tools use the `DatabaseService` class for all database operations
- Case IDs follow format: `case-YYYYMMDD-XXXXXXXX` (8 hex chars)
- All timestamps are in ISO 8601 format with 'Z' suffix
- Cases support: status, priority, assignee, tags, notes, timeline, activities
- Findings can be linked to multiple cases (many-to-many relationship)

---

**Status:** ✅ **Ready for production use**

The AI chat now has **full access** to case management functionality through MCP tools.

