# Tabbed Chat Drawer - Corrected Implementation

## Overview

The Claude Chat drawer now supports **multiple tabs**, allowing you to work on several investigations simultaneously without mixing contexts. Each tab has its own isolated conversation history.

## Key Features

### ✅ Tabs in the Drawer
- **Location**: All chat tabs are in the Claude Chat side drawer (not a separate main view)
- **Isolated Contexts**: Each tab has its own conversation history
- **Easy Switching**: Click tabs to switch between different investigations
- **Always Accessible**: Drawer stays visible while you work on the dashboard

### ✅ Auto-Create Tabs
- **From Findings**: Click "Analyze" button on any finding → Creates new tab automatically
- **Manual Creation**: Click "+ New" button to create a blank chat tab
- **Smart Naming**: Tabs are automatically named based on the finding ID

### ✅ Tab Management
- **Close Tabs**: Click × on tab (must keep at least one open)
- **Rename Tabs**: Right-click tab → Rename
- **Close Others**: Right-click tab → Close Others
- **Context Menu**: Right-click for additional options

## How to Use

### Opening the Claude Chat Drawer

1. **From Menu**: `View → Toggle Claude Chat` (Ctrl+C)
2. **From Toolbar**: Click "Claude Chat" button
3. **Auto-Opens**: Clicking "Analyze" on a finding opens it automatically

### Analyzing Findings (Creates New Tab)

**Method 1: From Finding List** (Recommended)
1. Go to Dashboard → Findings tab
2. Click the "Analyze" button on any finding
3. 🎉 Claude Chat drawer opens with a NEW TAB for that finding
4. The finding is automatically analyzed

**Method 2: Manual Tab Creation**
1. Open Claude Chat drawer
2. Click "+ New" button at the top
3. Enter a name for the chat (e.g., "SQL Injection Investigation")
4. Start chatting with Claude

### Working with Multiple Tabs

**Example Scenario:**

You have 3 security alerts today:

1. Click "Analyze" on Finding-001 (SQL Injection)
   - New tab created: "Finding-001"
   - Chat about SQL injection threat
   
2. Click "Analyze" on Finding-002 (Suspicious Login)
   - New tab created: "Finding-002"  
   - Chat about login anomalies
   - Finding-001 tab still has its own isolated history!
   
3. Click "Analyze" on Finding-003 (Data Exfiltration)
   - New tab created: "Finding-003"
   - Chat about data exfil
   - Other tabs remain isolated!

**Switch between tabs** to work on different investigations without losing context!

## UI Layout

```
┌─────────────────────────────────────────────────┐
│ Main Window                                     │
│ ┌──────────────────┬────────────────────────┐   │
│ │                  │ Claude Chat Drawer     │   │
│ │                  │ ┌──────────────────────┐  │
│ │                  │ │ + New    MCP: 5 tools│  │
│ │    Dashboard     │ ├──────────────────────┤  │
│ │                  │ │Tab: Chat 1 │Find-001✕│  │
│ │  [Findings List] │ ├──────────────────────┤  │
│ │                  │ │                      │  │
│ │  • Finding-001   │ │ [Agent Selector]     │  │
│ │  • Finding-002   │ │                      │  │
│ │  • Finding-003   │ │ Chat Display         │  │
│ │                  │ │ You: Analyze...      │  │
│ │  [Analyze btn]   │ │ Claude: This is...   │  │
│ │   ↓ (creates tab)│ │                      │  │
│ │                  │ │ [Message input]      │  │
│ │                  │ │ [Send]               │  │
│ │                  │ │                      │  │
│ │                  │ │ [Streaming] [Clear]  │  │
│ └──────────────────┴────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Differences from Previous Version

### ❌ Old (Incorrect) Implementation
- Tabbed investigations were a **separate main view**
- Had to switch away from Dashboard to use tabs
- Required navigation: View → Tabbed Investigations
- More complex, separate interface

### ✅ New (Correct) Implementation
- Tabs are **inside the Claude Chat drawer**
- Stay on Dashboard while using tabbed chats
- Clicking "Analyze" creates tab automatically
- Simpler, more integrated workflow

## Tab Features

### Isolated Conversation History
Each tab maintains:
- ✅ Its own conversation history (messages don't mix)
- ✅ Its own agent selection
- ✅ Token counting per tab
- ✅ Independent chat controls

### Tab Controls
- **+ New**: Create new blank chat tab
- **×**: Close tab (keeps at least one)
- **Right-click menu**:
  - Rename
  - Close
  - Close Others

### Auto-Analysis
When a tab is created from a finding:
1. Tab is named after the finding ID
2. Finding details are automatically sent to Claude
3. Claude provides:
   - Summary of the finding
   - Threat assessment
   - MITRE ATT&CK analysis
   - Recommended actions
   - Investigation steps

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Toggle Claude Chat drawer | Ctrl+C |
| Switch between tabs | Ctrl+Tab |
| Send message | Enter |

## Best Practices

### 📋 Tab Organization
- **One finding per tab**: Keep investigations focused
- **Descriptive names**: Rename tabs for clarity
- **Close completed**: Close tabs when investigation is done

### 🔍 Investigation Workflow
1. Browse findings in Dashboard
2. Click "Analyze" on interesting findings
3. Each creates a new tab in the drawer
4. Switch between tabs as needed
5. Chat history stays separate per tab

### 💬 Chat Management
- **Clear history**: Per-tab "Clear" button
- **Fresh start**: Create new tab for new investigation
- **Keep drawer open**: Work on dashboard while chatting

## Technical Details

### Tab Isolation

Each `ChatTab` instance has:
```python
self.conversation_history = []  # Isolated per tab
self.focused_finding = finding  # The finding this tab is about
self.current_worker = None      # API worker for this tab
```

### Tab Lifecycle

1. **Creation**: User clicks "Analyze" OR manually creates
2. **Auto-Analysis**: If from finding, automatically analyzes
3. **Usage**: User chats with Claude about this finding
4. **Closure**: User closes tab (history is lost unless exported)

### Memory Management

- Each tab: ~5-20MB depending on chat length
- Recommended: Keep 5-10 tabs active
- Close old tabs to free memory
- No persistence between sessions (chat history is temporary)

## Troubleshooting

### Issue: Drawer doesn't open when clicking Analyze
**Solution**: Check if Claude API key is configured. The drawer should auto-open.

### Issue: All tabs show the same conversation
**Solution**: This shouldn't happen! Each tab is isolated. Try restarting the app.

### Issue: Can't close the last tab
**Solution**: By design - you must always have at least one tab open.

### Issue: Lost my chat history
**Solution**: Chat history is not saved between sessions. Important conversations should be exported or documented in cases.

## Comparison to Full-Featured Tabbed Investigations

The old standalone "Tabbed Investigations" view had:
- Finding lists per tab
- Investigation notes
- Export/PDF features
- Case creation
- More complex UI

The new **Tabbed Chat Drawer** is:
- Simpler and more focused
- Always accessible from any view
- Automatic tab creation from findings
- Better integrated with the workflow

## Summary

### What You Get

✅ **Tabbed chat in the side drawer** - Not a separate view
✅ **Auto-create tabs from findings** - Just click "Analyze"
✅ **Isolated contexts** - Each tab has its own conversation
✅ **Simple workflow** - Stay on Dashboard, chat in drawer
✅ **Easy switching** - Click tabs to switch investigations

### How It Works

1. You're on the Dashboard viewing findings
2. Click "Analyze" on a finding
3. Claude Chat drawer opens (if not already)
4. New tab created with that finding
5. Finding is automatically analyzed
6. You can click "Analyze" on more findings
7. Each creates a new tab
8. Switch between tabs to work on different investigations

**No more mixed-up chats! Each investigation stays in its own tab!** 🎉

