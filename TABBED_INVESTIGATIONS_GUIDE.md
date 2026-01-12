# Tabbed Investigations - User Guide

## Overview

The Tabbed Investigations feature allows you to work on multiple security investigations simultaneously, each with completely isolated contexts. This prevents mixing of chat histories, findings, and analysis between different investigations.

## Key Features

### 🔒 Complete Isolation
- **Separate Chat History**: Each tab maintains its own conversation with Claude AI
- **Independent Context**: Findings, notes, and analysis don't mix between tabs
- **Multiple Agents**: Use different SOC agents in different tabs simultaneously
- **No Cross-Contamination**: Investigate unrelated events without context pollution

### 📋 Tab Capabilities
Each investigation tab includes:
- **Claude AI Chat**: Full-featured chat interface with streaming responses
- **Focused Findings**: Add specific findings to analyze in this investigation
- **Investigation Notes**: Track your investigation progress and observations
- **Quick Actions**: Correlate findings, create cases, export chat history
- **Agent Selection**: Choose specialized SOC agents per investigation

## Getting Started

### Opening Tabbed Investigations

1. **From Menu**: `View → Tabbed Investigations` (Ctrl+I)
2. **From Toolbar**: Click the "Investigations" button
3. **From Finding List**: Right-click "Analyze" button → "Analyze in New Investigation Tab"

### Creating Investigation Tabs

#### Method 1: Manual Creation
1. Click "+ New Investigation" button
2. Enter an investigation name (e.g., "Suspicious Login - User123")
3. Start adding findings and chatting with Claude

#### Method 2: From Finding List
1. Navigate to Dashboard → Findings tab
2. Find a security finding you want to investigate
3. Click the "Analyze ▾" button on the finding
4. Select "Analyze in New Investigation Tab"
5. A new tab opens automatically with the finding loaded

## Using Investigation Tabs

### Adding Findings

1. Click "Add Finding" in the Focused Findings section
2. Enter the Finding ID
3. The finding appears in your focused list

**OR** use the "Analyze in New Investigation Tab" option from the Finding List

### Analyzing Findings

Once findings are added:

1. **Single Finding Analysis**: Select a finding and click "Analyze Selected"
   - Claude will provide a detailed analysis of that specific finding
   
2. **Multiple Finding Correlation**: Add 2+ findings, then click "Correlate All Focused Findings"
   - Claude will identify patterns, attack chains, and shared indicators

### Chatting with Claude

The chat interface works just like the main Claude Chat, but with **isolated context**:

1. Type your question/request in the message box
2. Press Enter or click "Send"
3. Claude responds with context about YOUR TAB'S focused findings
4. Switch agents using the agent selector to get different perspectives

**Example Queries:**
- "What MITRE ATT&CK techniques are involved in these findings?"
- "Is this a false positive or a real threat?"
- "What containment actions should I take?"
- "Are these findings related to a single attack campaign?"

### Investigation Notes

Use the Investigation Notes section to:
- Document your hypothesis
- Track investigation steps taken
- Note key findings or IOCs discovered
- Keep a timeline of events

### Creating Cases

When your investigation is ready to be formalized:

1. Click "Create Case from This Investigation"
2. Enter a case title
3. All focused findings will be linked to the new case
4. Your investigation notes are added to the case description

### Exporting Chat History

To save your investigation conversation:

1. Click "Export Chat History"
2. Choose a filename (default: `{tab_id}_chat.json`)
3. The export includes:
   - All chat messages
   - Focused findings list
   - Investigation notes
   - Tab metadata

## Tab Management

### Renaming Tabs

1. Click "Rename" button in the tab
2. Enter new investigation name
3. Tab title updates automatically

### Closing Tabs

**From Tab Bar:**
- Click the ✕ on the tab
- System will warn if there's unsaved work

**From Toolbar:**
- Click "Close Current" to close active tab

**Note**: You must keep at least one tab open

### Context Menu (Right-Click Tab)

Right-click any tab to access:
- **Rename**: Change the investigation name
- **Duplicate**: Create a copy with same findings (fresh chat history)
- **Export Chat**: Save the conversation
- **Close**: Close this tab
- **Close Others**: Close all tabs except this one

## Use Cases

### Scenario 1: Multiple Unrelated Incidents

You receive alerts about:
- Suspicious login from unusual location
- Potential data exfiltration
- Malware detection on different host

**Solution**: Create 3 separate investigation tabs
- Each incident gets its own isolated workspace
- No confusion between different attack vectors
- Work on all three simultaneously without losing context

### Scenario 2: Comparing Hypotheses

You're investigating a security event and have two theories:
- Theory A: Insider threat
- Theory B: External compromise

**Solution**: Duplicate the tab
- Tab 1: Investigate insider threat angle
- Tab 2: Investigate external compromise angle
- Compare findings and chat history from both approaches

### Scenario 3: Team Collaboration

Multiple analysts working on the same system:
- Analyst 1: Investigates network anomalies (Tab 1)
- Analyst 2: Investigates host-based indicators (Tab 2)
- Analyst 3: Investigates user behavior (Tab 3)

**Solution**: Each analyst works in their own tab
- No context mixing
- Each can export their investigation when done
- Findings can be merged into cases later

### Scenario 4: Different Agent Perspectives

You want multiple viewpoints on the same finding:
- Tab 1: Smart Agent (general analysis)
- Tab 2: Forensic Analyst (deep technical dive)
- Tab 3: Threat Hunter (proactive threat hunting)

**Solution**: Duplicate tabs and switch agents
- Same findings, different analytical approaches
- Compare insights from different specialized agents

## Best Practices

### 📝 Naming Conventions

Use descriptive tab names:
- ✅ "SQL Injection - WebApp01 - 2024-01-12"
- ✅ "Data Exfil Investigation - User: jsmith"
- ✅ "Ransomware Analysis - Host: WS-FINANCE-05"
- ❌ "Investigation 1", "Tab 2", "Untitled"

### 💾 Save Your Work

- Export chat history for important investigations
- Create cases before closing significant tabs
- Copy investigation notes to case descriptions

### 🔄 Use Correlation Features

- Add all related findings to a single tab
- Use "Correlate All Focused Findings" to find patterns
- Let Claude help identify attack chains

### 🎯 Focus Each Tab

- Keep tabs focused on specific incidents or hypotheses
- Don't mix unrelated events in the same tab
- Use multiple tabs instead of cramming everything into one

### 🔍 Leverage Different Agents

- Start with Smart Agent for initial triage
- Switch to Forensic Analyst for deep dives
- Use Threat Hunter for proactive investigation
- Try Incident Commander for coordination

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+I | Open Tabbed Investigations view |
| Ctrl+Tab | Switch between tabs |
| Enter | Send chat message |
| Ctrl+W | Close current tab (when multiple tabs open) |

## Troubleshooting

### "Cannot Close - Must have at least one tab"

**Issue**: Trying to close the last remaining tab

**Solution**: This is by design. Create a new tab first, then close the old one.

### Chat context seems mixed

**Issue**: Responses reference findings from other tabs

**Solution**: This shouldn't happen! Each tab is isolated. If it does:
1. Clear the chat history in the affected tab
2. Report as a bug

### Lost my investigation

**Issue**: Closed a tab without exporting

**Solution**: Prevention is key:
- Export important chats before closing
- Create cases from investigations
- Keep investigation notes updated

### Tab is unresponsive

**Issue**: Tab not loading or responding

**Solution**:
1. Switch to another tab
2. Switch back to the problematic tab
3. If still unresponsive, export chat and create new tab

## Technical Details

### Data Isolation

Each `InvestigationTab` maintains:
```python
- conversation_history: []      # Isolated chat messages
- focused_findings: []           # This tab's findings only
- workflow_id: Optional[str]     # Optional workflow link
- case_id: Optional[str]        # Optional case link
```

Tabs **DO NOT** share:
- Claude conversation history
- Finding lists
- Investigation notes
- Agent contexts

### Export Format

Chat exports are JSON files containing:
```json
{
  "tab_id": "inv_20240112_143022_1",
  "title": "Investigation: Finding-ABC123",
  "history": [...],              // Claude conversation
  "findings": ["ABC123", ...],   // Finding IDs
  "notes": "Investigation notes..."
}
```

### Performance

- Each tab uses ~10-50MB of memory (depending on chat length)
- Recommended maximum: 10-15 active tabs
- Old chats can be exported and closed to free memory

## FAQ

**Q: Can I work on the same finding in multiple tabs?**

A: Yes! This is useful for exploring different hypotheses or using different agents.

**Q: Do tabs sync with each other?**

A: No. Each tab is completely independent. This is by design to prevent context mixing.

**Q: Can I move findings between tabs?**

A: Not directly, but you can:
1. Note the finding ID
2. Add it to another tab using "Add Finding"

**Q: What happens if I create a case from a tab?**

A: The case is created with all focused findings linked. The tab remains open and functional.

**Q: Can I use MCP tools in tabs?**

A: Yes! Each tab has full access to MCP tools if configured. Tool calls are isolated per tab.

**Q: How do I see all my open investigations?**

A: Look at the tab bar at the top of the Tabbed Investigations view. Each tab shows its investigation name.

**Q: Can I change the agent mid-investigation?**

A: Yes! Use the agent selector dropdown. Your chat history remains but future responses use the new agent.

## Summary

Tabbed Investigations provide a powerful way to:
- ✅ Work on multiple security events simultaneously
- ✅ Keep investigation contexts completely separated
- ✅ Avoid mixing findings and analysis between cases
- ✅ Use different SOC agents for different investigations
- ✅ Collaborate effectively with team members
- ✅ Maintain clear organization of your SOC work

Start using Tabbed Investigations today to streamline your security operations workflow!

