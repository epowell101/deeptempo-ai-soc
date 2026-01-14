# Timesketch Integration - User Guide

## Quick Start

### 1. Configure Timesketch

Before using Timesketch features, you need to configure the connection:

1. Navigate to **Settings** (gear icon in the navigation)
2. Click on the **Timesketch** tab
3. Enter your Timesketch configuration:
   - **Server URL**: Your Timesketch server address (e.g., `http://localhost:5000`)
   - **Username**: Your Timesketch username
   - **Password**: Your Timesketch password
   - **Auto-start Docker** (optional): Check this to automatically start Docker container
4. Click **Save**

### 2. Access Timesketch Features

Once configured, you can access Timesketch features from multiple locations:

#### Timesketch Page
Navigate to **Timesketch** in the main menu to:
- View server connection status
- Manage Docker container (start/stop)
- List all your sketches
- Create new sketches
- Open sketches in Timesketch web interface

#### Export from Findings
1. Go to **Findings** page
2. Apply filters (optional) to select specific findings
3. Click **Export to Timesketch** button
4. Choose export options (see below)
5. Click **Export**

#### Export from Cases
1. Go to **Cases** page
2. Click **View** on any case
3. In the case detail dialog, click **Export to Timesketch**
4. Choose export options (see below)
5. Click **Export**

## Export Options

When exporting to Timesketch, you'll see a dialog with the following options:

### Timeline Name
Give your timeline a descriptive name. Default suggestions:
- For findings: "Findings Export - [Date]"
- For cases: "Case: [Case Title]"

### Sketch Selection
Choose how to organize your timeline:

**Option 1: Add to Existing Sketch**
- Select an existing sketch from the dropdown
- Timeline will be added to the selected sketch
- Useful for grouping related investigations

**Option 2: Create New Sketch**
- Enter a name for the new sketch
- Optionally add a description
- A new sketch will be created with your timeline
- Useful for starting new investigations

## Understanding Timeline Events

When you export findings or cases to Timesketch, DeepTempo automatically converts them into timeline events with rich metadata:

### Finding Events Include:
- **Timestamp**: When the finding occurred
- **Severity**: Critical, High, Medium, or Low
- **Data Source**: Where the finding came from
- **Anomaly Score**: Numerical score indicating anomaly level
- **MITRE Techniques**: Predicted attack techniques
- **Entity Context**: IP addresses, hostnames, users, etc.
- **Tags**: Searchable tags for filtering

### Case Events Include:
- **Case Creation Event**: When the case was created
- **Case Timeline Events**: All activities in the case
- **Associated Findings**: All findings linked to the case
- **Case Metadata**: Priority, status, assignee, etc.

## Using Timesketch for Investigation

Once your data is exported to Timesketch, you can:

### 1. Visualize Timelines
- View events on an interactive timeline
- Zoom in/out to focus on specific time periods
- Compare multiple timelines side-by-side

### 2. Search and Filter
- Use Timesketch's powerful search syntax
- Filter by tags, severity, MITRE techniques
- Create saved searches for common queries

### 3. Annotate Events
- Add comments to events
- Tag events with custom labels
- Star important events

### 4. Collaborate
- Share sketches with team members
- View team member annotations
- Track investigation progress

### 5. Analyze Patterns
- Run Timesketch analyzers
- Identify temporal patterns
- Detect anomalies and outliers

## Docker Container Management

If you're running Timesketch locally using Docker, you can manage it from the Timesketch page:

### Check Status
The Docker status card shows:
- Docker availability
- Docker daemon status
- Container running status

### Start Container
1. Ensure Docker is installed and running
2. Click **Start Container** button
3. Wait for container to start (may take 30-60 seconds)
4. Refresh page to verify status

### Stop Container
1. Click **Stop Container** button
2. Container will shut down gracefully
3. Your data is preserved for next start

## Best Practices

### Organizing Sketches
- **One sketch per investigation**: Keep related timelines together
- **Descriptive names**: Use clear, searchable sketch names
- **Add descriptions**: Document the investigation scope

### Naming Timelines
- **Include date**: Makes it easy to find recent exports
- **Describe content**: "Suspicious Login Attempts" vs "Export 1"
- **Use case IDs**: Reference case numbers when applicable

### Exporting Data
- **Filter first**: Apply filters before exporting to reduce noise
- **Export incrementally**: Add new findings as they're discovered
- **Combine with cases**: Export full cases for comprehensive timelines

### Investigating in Timesketch
- **Start with overview**: Look at the full timeline first
- **Zoom to anomalies**: Focus on high-severity or high-score events
- **Follow entity trails**: Track IP addresses, users across events
- **Use MITRE tags**: Filter by attack techniques
- **Document findings**: Add comments and annotations

## Troubleshooting

### "Timesketch not configured"
**Solution**: Go to Settings → Timesketch and configure your connection

### "Connection failed"
**Possible causes**:
- Timesketch server is not running
- Incorrect server URL
- Network connectivity issues
- Docker container not started

**Solutions**:
1. Verify server URL is correct
2. Check Timesketch server is running
3. If using Docker, click "Start Container"
4. Test connection from Settings page

### "Failed to export"
**Possible causes**:
- Invalid authentication credentials
- Insufficient permissions in Timesketch
- No findings/events to export
- Server error

**Solutions**:
1. Verify username/password in Settings
2. Check you have permission to create sketches
3. Ensure findings/case has data
4. Check Timesketch server logs

### Docker container won't start
**Possible causes**:
- Docker not installed
- Docker daemon not running
- Port 5000 already in use
- Insufficient system resources

**Solutions**:
1. Install Docker Desktop
2. Start Docker daemon
3. Stop other services using port 5000
4. Free up system memory/CPU

### No sketches appear
**Possible causes**:
- No sketches created yet
- Authentication issue
- Server connection problem

**Solutions**:
1. Create your first sketch
2. Verify authentication in Settings
3. Check server connection status

## Advanced Features

### Custom Timeline Names
Use descriptive names that include:
- Investigation type
- Date range
- Key entities (IPs, users)
- Case reference numbers

Example: "Ransomware Investigation - 2026-01-14 - 192.168.1.100"

### Sketch Organization
Create sketches for different investigation types:
- **Active Investigations**: Current cases
- **Threat Hunting**: Proactive searches
- **Incident Response**: Security incidents
- **Forensics**: Deep-dive analysis

### Timeline Correlation
Export related data to the same sketch:
1. Export initial findings
2. Add case timeline
3. Export additional findings as discovered
4. View complete picture in Timesketch

### MITRE ATT&CK Integration
Timeline events include MITRE technique tags:
- Search by technique ID (e.g., "T1078")
- Filter by tactic (e.g., "Initial Access")
- Track attack progression
- Identify technique patterns

## Getting Help

### Resources
- **Timesketch Documentation**: https://timesketch.org/
- **DeepTempo Docs**: See `docs/` folder
- **MITRE ATT&CK**: https://attack.mitre.org/

### Support
- Check the `TIMESKETCH_INTEGRATION.md` for technical details
- Review Timesketch server logs for errors
- Consult DeepTempo documentation for data model

## Example Workflows

### Workflow 1: Investigate Suspicious Findings
1. Go to Findings page
2. Filter by severity: "High" or "Critical"
3. Click "Export to Timesketch"
4. Create new sketch: "High Severity Investigation - [Date]"
5. Open sketch in Timesketch
6. Analyze timeline for patterns
7. Add annotations and comments
8. Share with team

### Workflow 2: Case Timeline Analysis
1. Create case in DeepTempo
2. Add relevant findings to case
3. Open case detail dialog
4. Click "Export to Timesketch"
5. Add to existing investigation sketch
6. View complete case timeline
7. Identify attack progression
8. Document resolution steps

### Workflow 3: Threat Hunting
1. Apply filters for specific data sources
2. Set minimum anomaly score
3. Export findings to Timesketch
4. Run Timesketch analyzers
5. Identify anomalous patterns
6. Create new cases for threats found
7. Export cases back to Timesketch

### Workflow 4: Incident Response
1. Identify initial finding/alert
2. Create case in DeepTempo
3. Export case to Timesketch
4. Investigate timeline in Timesketch
5. Identify related findings
6. Add findings to case
7. Re-export updated case
8. Generate final report

## Tips and Tricks

### Efficient Searching
- Use wildcards: `192.168.*` for IP ranges
- Combine filters: severity AND technique
- Save common searches in Timesketch
- Use tags for quick filtering

### Timeline Analysis
- Look for temporal clustering (many events in short time)
- Identify outliers (unusual times or patterns)
- Track entity movement across events
- Correlate with external threat intel

### Collaboration
- Use consistent naming conventions
- Document assumptions in comments
- Share sketches with relevant team members
- Update case notes in DeepTempo

### Performance
- Export filtered data to reduce event count
- Create separate sketches for large investigations
- Use Timesketch's pagination for large timelines
- Archive old sketches when complete

## Conclusion

The Timesketch integration provides powerful timeline analysis capabilities for DeepTempo AI SOC. By following this guide, you can effectively export, visualize, and investigate security findings and cases using Timesketch's advanced features.

Happy investigating! 🔍

