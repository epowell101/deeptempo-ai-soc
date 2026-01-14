# Navigation Guide - DeepTempo AI SOC

## Main Navigation

The DeepTempo AI SOC platform has a streamlined navigation structure with 5 main sections:

### 🏠 Dashboard
**Path**: `/`

The main overview page showing:
- Key metrics and statistics
- Recent findings and cases
- System health status
- Quick actions

### 🔍 Findings
**Path**: `/findings`

Security findings management:
- View all security findings
- Filter and search findings
- Investigate findings with AI agents
- Export findings to Timesketch
- Create cases from findings

### 📁 Cases
**Path**: `/cases`

Case management system:
- View all security cases
- Track case status and progress
- Assign cases to team members
- View case details and timeline
- Link findings to cases

### 📈 Timesketch
**Path**: `/timesketch`

Timeline analysis integration:
- View Timesketch server status
- Manage Docker container
- Access timeline analysis
- Export data for investigation

### ⚙️ Settings
**Path**: `/settings`

**All configuration and administrative tasks are here**, organized in 9 tabs:

#### 1. Claude API
Configure Anthropic Claude API for AI-powered analysis

#### 2. Timesketch
Set up Timesketch server connection and Docker options

#### 3. S3 Storage
Configure AWS S3 for findings and cases storage

#### 4. MCP Servers 🔧
**Manage Model Context Protocol servers:**
- View all configured MCP servers
- Start/Stop individual servers
- Bulk operations (Start All / Stop All)
- View server logs
- Monitor server status

#### 5. GitHub
Configure GitHub community MCP server

#### 6. PostgreSQL
Set up PostgreSQL community MCP server

#### 7. Splunk
Configure Splunk SIEM integration

#### 8. Integrations 🔌
**Configure 27+ security tool integrations:**
- Threat Intelligence (6 tools)
- EDR/XDR (4 tools)
- SIEM (1 tool)
- Cloud Security (2 tools)
- Identity & Access (2 tools)
- Network Security (1 tool)
- Incident Management (1 tool)
- Communications (7 tools)
- Sandbox Analysis (3 tools)

#### 9. General
Application preferences and theme settings

## Quick Access Guide

### Common Tasks

| Task | Location |
|------|----------|
| View security findings | **Findings** page |
| Investigate with AI | **Findings** → Click investigate button |
| Create a case | **Cases** → New Case button |
| Configure integrations | **Settings** → **Integrations** tab |
| Manage MCP servers | **Settings** → **MCP Servers** tab |
| Set up VirusTotal | **Settings** → **Integrations** → Threat Intelligence |
| Configure Slack alerts | **Settings** → **Integrations** → Communications |
| Start/Stop servers | **Settings** → **MCP Servers** tab |
| Change theme | **Settings** → **General** tab |
| Export to timeline | **Findings** → Select finding → Export |

### Configuration Workflow

1. **Initial Setup**
   - Settings → Claude API (configure AI)
   - Settings → Integrations (set up tools)
   - Settings → MCP Servers (verify servers running)

2. **Daily Operations**
   - Dashboard (overview)
   - Findings (triage)
   - Cases (track investigations)

3. **Advanced Analysis**
   - Findings → Investigate (AI analysis)
   - Timesketch (timeline analysis)

## Navigation Tips

### 💡 Pro Tips

1. **Settings is Your Friend**: All configuration lives in Settings - don't look elsewhere!

2. **MCP Servers Location**: MCP server management moved to Settings → MCP Servers tab (no longer in main nav)

3. **Integration Setup**: Use the visual wizard in Settings → Integrations for easy configuration

4. **Quick Chat**: Click the chat icon (💬) in the top-right to open DeepTempo AI assistant

5. **Theme Toggle**: Click the sun/moon icon in the top-right to switch themes

6. **Breadcrumbs**: The page title in the top bar shows your current location

### 🔍 Finding Things

**Looking for...**
- **API Keys?** → Settings → Integrations
- **Server Status?** → Settings → MCP Servers
- **Theme Settings?** → Settings → General
- **Timesketch Setup?** → Settings → Timesketch
- **Tool Configuration?** → Settings → Integrations
- **Database Config?** → Settings → PostgreSQL

## Mobile Navigation

On mobile devices:
1. Tap the **☰** menu icon (top-left)
2. Navigation drawer slides out
3. Select your destination
4. Drawer auto-closes

## Keyboard Shortcuts

*Coming soon - keyboard shortcuts for power users*

## URL Structure

```
/                    → Dashboard
/findings            → Findings page
/cases               → Cases page
/timesketch          → Timesketch page
/settings            → Settings page (all tabs)
```

**Note**: The old `/mcp-servers` URL has been removed. Use `/settings` and click the MCP Servers tab instead.

## What's Changed?

### Recent Updates (January 2026)

#### ✅ MCP Servers Consolidated
- **Old**: Separate "MCP Servers" page in main navigation
- **New**: MCP Servers tab inside Settings page
- **Why**: Better organization - all configuration in one place

#### ✅ Integrations Expanded
- **Old**: 21 integrations
- **New**: 27 integrations (added 6 communication platforms)
- **New**: Visual configuration wizards for all tools

## Need Help?

- **General Questions**: Use the DeepTempo AI chat (💬 icon)
- **Configuration Help**: Check Settings → Integrations → Click "Docs" on any tool
- **MCP Server Issues**: Settings → MCP Servers → View logs
- **Integration Setup**: See [Integration Wizard Guide](integration-wizard-guide.md)

---

**Last Updated**: January 2026  
**Version**: 1.1.0

