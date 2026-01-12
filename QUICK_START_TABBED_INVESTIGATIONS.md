# Quick Start: Tabbed Investigations

## 🎯 What You Got

**Problem Solved**: You can now analyze different events in separate tabs without mixing up chat contexts!

Each investigation tab has:
- ✅ **Its own isolated Claude chat** (conversations don't mix)
- ✅ **Separate findings list** (focus on specific events)
- ✅ **Investigation notes** (track your thoughts)
- ✅ **Independent agent selection** (use different agents per tab)

## 🚀 Quick Start (3 Steps)

### Step 1: Open Tabbed Investigations

**Option A**: Menu Bar
```
View → Tabbed Investigations (or press Ctrl+I)
```

**Option B**: Toolbar
```
Click the "Investigations" button in the toolbar
```

### Step 2: Create Investigation Tabs

**Easy Way** (Recommended):
1. Go to Dashboard → Findings tab
2. Find a security finding you want to investigate
3. Click the "Analyze ▾" button (with dropdown arrow)
4. Select "Analyze in New Investigation Tab"
5. 🎉 New tab opens with the finding already loaded!

**Manual Way**:
1. In Tabbed Investigations view
2. Click "+ New Investigation" button
3. Enter a name like "Suspicious Login - User123"
4. Click "Add Finding" to add findings manually

### Step 3: Investigate with Isolated Context

In each tab:
1. **Chat with Claude** - Ask questions about YOUR TAB'S findings
2. **Add more findings** - Build context for this investigation
3. **Take notes** - Document your hypothesis and observations
4. **Create case** - When ready, formalize the investigation

## 💡 Example Workflow

### Scenario: Multiple Alerts Today

You receive 3 different security alerts:

**Tab 1: "SQL Injection - Web Server"**
- Add finding: `FIND-2024-001`
- Chat: "Is this a real SQL injection or just a scan?"
- Agent: Smart Agent

**Tab 2: "Suspicious Login - Finance User"**
- Add finding: `FIND-2024-002`
- Chat: "Show me the login pattern analysis"
- Agent: Forensic Analyst

**Tab 3: "Data Exfiltration - Sales Dept"**
- Add findings: `FIND-2024-003`, `FIND-2024-004`, `FIND-2024-005`
- Chat: "Correlate these findings. Is this a coordinated attack?"
- Agent: Threat Hunter

**Result**: Each investigation stays separate. No mixing of findings or chat context!

## 🔥 Power User Tips

### Tip 1: Rename Tabs for Clarity
```
Click "Rename" button → Enter descriptive name
Example: "Ransomware Investigation - Host-WS05"
```

### Tip 2: Duplicate to Try Different Approaches
```
Right-click tab → Duplicate
- Tab A: Investigate as insider threat
- Tab B: Investigate as external attack
Compare the results!
```

### Tip 3: Export Before Closing
```
Click "Export Chat History"
Saves your entire conversation + findings + notes
```

### Tip 4: Use Quick Actions
```
- "Correlate All Focused Findings" → Find patterns across multiple events
- "Create Case from This Investigation" → Formalize your findings
```

### Tip 5: Switch Agents Mid-Investigation
```
Use the agent selector dropdown to get different perspectives:
- Smart Agent: General analysis
- Forensic Analyst: Deep technical dive
- Threat Hunter: Proactive hunting
- Incident Commander: Coordination
```

## 🎨 Visual Layout

```
┌────────────────────────────────────────────────────────────────┐
│ + New Investigation │ Close Current │ ℹ️ About               │
├────────────────────────────────────────────────────────────────┤
│ Tab: Investigation 1 │ Tab: SQL Attack │ Tab: Login Anomaly ✕│
├──────────────────────┬─────────────────────────────────────────┤
│                      │ Focused Findings                        │
│  CHAT WITH CLAUDE    │ ┌─────────────────────────────────────┐ │
│                      │ │ • FIND-001 - Critical               │ │
│  [Agent Selector]    │ │ • FIND-002 - High                   │ │
│                      │ └─────────────────────────────────────┘ │
│  You: Analyze this   │ [Add Finding] [Remove] [Analyze]        │
│  finding...          │                                         │
│                      │ Investigation Notes                     │
│  Claude: This        │ ┌─────────────────────────────────────┐ │
│  appears to be...    │ │ User reports unusual activity...    │ │
│                      │ │ Checking logs from 10:00-11:00...   │ │
│  [Message input]     │ └─────────────────────────────────────┘ │
│  [Send]              │                                         │
│                      │ Quick Actions                           │
│  [Streaming] [Clear] │ [Correlate] [Create Case] [Export]     │
└──────────────────────┴─────────────────────────────────────────┘
```

## 🎯 Use Cases

### ✅ Best For:
- Investigating multiple unrelated incidents simultaneously
- Comparing different hypotheses for the same incident
- Team collaboration (each analyst gets their own tab)
- Keeping long-running investigations organized
- Testing different agent perspectives

### ❌ Not Ideal For:
- Single, simple finding lookup (use regular Claude Chat)
- Quick queries that don't need context preservation
- When you want findings from multiple tabs to share context

## 🔧 Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open Tabbed Investigations | Ctrl+I |
| Switch tabs | Ctrl+Tab |
| Send message | Enter |
| Close tab | Ctrl+W (when multiple tabs) |

## 📊 Tab Management

### Creating Tabs
- **From scratch**: Click "+ New Investigation"
- **From finding**: Use "Analyze in New Investigation Tab" in Finding List
- **Duplicate existing**: Right-click tab → Duplicate

### Closing Tabs
- **Close one**: Click ✕ on tab
- **Close others**: Right-click → Close Others
- **Close all**: Close each tab (keeps one by default)

### Context Menu (Right-Click Tab)
- **Rename**: Change investigation name
- **Duplicate**: Copy findings (fresh chat)
- **Export Chat**: Save conversation
- **Close**: Close this tab
- **Close Others**: Keep only this one

## ⚠️ Important Notes

### Isolation Guarantee
✅ Each tab has completely separate:
- Chat history
- Focused findings
- Investigation notes
- Agent context

❌ Tabs do NOT share:
- Conversation history
- Finding lists
- Notes

### Persistence
⚠️ **Chat history is NOT saved** between app sessions
- Use "Export Chat History" before closing important investigations
- Create cases to preserve findings and notes

### Performance
- Recommended: Keep 5-10 tabs open
- Maximum: 15-20 tabs
- Large chat histories may slow down (export old ones)

## 🆘 Troubleshooting

### Issue: "Cannot close - must have at least one tab"
**Solution**: Create a new tab first, then close the old one

### Issue: Tab seems slow
**Solution**: Export chat and create fresh tab with same findings

### Issue: Lost my investigation
**Solution**: Export important chats regularly. No auto-save currently.

### Issue: Chat context seems mixed
**Solution**: This shouldn't happen (tabs are isolated). Clear chat and restart investigation.

## 📚 More Information

- **Full Guide**: See `TABBED_INVESTIGATIONS_GUIDE.md`
- **Technical Details**: See `IMPLEMENTATION_SUMMARY.md`
- **Application Architecture**: See `APPLICATION_ARCHITECTURE.md`

## 🎉 You're Ready!

Start using Tabbed Investigations to:
1. Open View → Tabbed Investigations (Ctrl+I)
2. Create a new tab or analyze a finding
3. Investigate with isolated context
4. Create cases when ready
5. Export important conversations

**No more mixed-up chats! Each investigation stays separate! 🚀**

