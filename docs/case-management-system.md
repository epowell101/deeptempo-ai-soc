# Case Management System

## Overview

The DeepTempo AI SOC platform now includes a comprehensive case management system that allows you to track, investigate, and resolve security cases from start to finish. The system provides full visibility into case progress, maintains detailed audit trails, and generates professional PDF reports documenting all resolution steps.

## Key Features

### 1. **Enhanced Case Detail View with Tabs**

The case detail dialog now features a tabbed interface with four main sections:

- **Overview**: Core case information and metadata
- **Findings**: Associated security findings
- **Activities**: Activity log and audit trail
- **Resolution**: Step-by-step resolution documentation

### 2. **Case Overview Tab**

View and edit essential case information:

- **Title & Description**: Clear identification and context
- **Status**: Open, In Progress, Resolved, Closed
- **Priority**: Low, Medium, High, Critical
- **Assignee**: Track case ownership
- **Timeline**: Automatic timeline of case events
- **Creation & Update Timestamps**: Full audit trail

#### Quick Actions (Header)
- **Generate Report**: Create PDF report with all case details
- **Resolve**: Quickly mark case as resolved
- **Edit Mode**: Toggle between view and edit modes

### 3. **Findings Management Tab**

Dynamically manage findings associated with a case:

#### Features:
- **Add Findings**: Search and add findings to the case from a dropdown
- **View Details**: See finding details in a table format
  - Finding ID
  - Severity (with color-coded chips)
  - Data Source
  - Anomaly Score
- **Remove Findings**: Remove findings that aren't relevant
- **Real-time Updates**: Changes immediately reflect in the case

#### Use Cases:
- Group related findings into a single investigation
- Remove false positives from a case
- Build comprehensive threat narratives

### 4. **Activities Tracking Tab**

Maintain a complete audit trail of all case activities:

#### Activity Types:
- **Note**: General observations and comments
- **Status Change**: Document status transitions
- **Finding Added**: Track when findings are associated
- **Action Taken**: Record investigative actions
- **Investigation**: Document investigation steps

#### Features:
- **Add Activities**: Quick form to log new activities
- **Chronological View**: Activities displayed in reverse chronological order
- **Timestamps**: Automatic timestamping of all activities
- **Color-coded Cards**: Easy visual scanning

#### Best Practices:
- Log significant investigation steps
- Document decision-making rationale
- Note external communications
- Track IOC enrichment activities

### 5. **Resolution Workflow Tab**

Document the complete resolution process with detailed steps:

#### Resolution Step Components:
1. **Step Description**: What was done (e.g., "Isolated affected host")
2. **Action Taken**: Detailed explanation of the action (e.g., "Disabled network interface on workstation-42 and quarantined via EDR")
3. **Result**: Outcome of the action (e.g., "Host successfully isolated, no lateral movement detected")
4. **Timestamp**: Automatic timestamp for each step

#### Features:
- **Sequential Steps**: Steps are numbered automatically
- **Detailed Documentation**: Rich text fields for comprehensive notes
- **Visual Cards**: Each step displayed in an easy-to-read card format
- **Export to PDF**: All steps included in case reports

#### Example Resolution Flow:

**Step 1: Initial Containment**
- Description: "Isolated compromised host"
- Action: "Disabled network interface on WS-2024-042, contacted network team to VLAN isolate"
- Result: "Host isolated within 5 minutes, no additional network activity detected"

**Step 2: Evidence Collection**
- Description: "Collected forensic artifacts"
- Action: "Captured memory dump, disk image, and event logs using forensic toolkit"
- Result: "Successfully collected 45GB of evidence, stored in case folder"

**Step 3: Malware Analysis**
- Description: "Analyzed suspicious binary"
- Action: "Submitted to sandbox, performed static analysis, identified C2 domains"
- Result: "Confirmed Cobalt Strike beacon, added IOCs to threat intel feed"

**Step 4: Remediation**
- Description: "Cleaned infected system"
- Action: "Reimaged host, reset user credentials, deployed updated EDR policies"
- Result: "System cleaned and returned to service, monitoring for 48 hours"

### 6. **Report Generation**

Generate comprehensive PDF reports that include:

#### Report Contents:
- **Case Metadata**: ID, status, priority, assignee, dates
- **Description**: Full case description
- **Tags**: Case categorization tags
- **Timeline**: Event timeline
- **Investigation Notes**: All notes and observations
- **Activities**: Complete activity log with timestamps
- **Resolution Steps**: Detailed step-by-step resolution documentation
- **Related Findings**: Summary table of all associated findings
- **Finding Details**: Comprehensive details for each finding
  - Finding ID, timestamp, severity
  - Data source and anomaly score
  - Entity context
  - MITRE ATT&CK techniques

#### Report File Location:
Reports are saved to `TestOutputs/` directory with the format:
```
{case_id}_report_{timestamp}.pdf
```

Example: `case-2026-01-14-abc123_report_20260114_153045.pdf`

## Usage Guide

### Creating a New Case

1. Navigate to the **Cases** page
2. Click **New Case** button
3. Fill in:
   - Title (required)
   - Description
   - Priority (Low/Medium/High/Critical)
4. Click **Create**

### Building Out a Case

1. **Open Case Details**: Click **View** on any case in the table
2. **Add Findings** (Findings Tab):
   - Select a finding from the dropdown
   - Click **Add**
   - Repeat for all relevant findings
3. **Log Activities** (Activities Tab):
   - Select activity type
   - Enter description
   - Click **Add**
4. **Document Resolution** (Resolution Tab):
   - For each resolution step:
     - Enter step description
     - Detail the action taken
     - Document the result
     - Click **Add Resolution Step**

### Updating Case Information

1. Open the case detail dialog
2. Click **Edit** button
3. Modify any fields:
   - Title
   - Description
   - Status
   - Priority
   - Assignee
4. Click **Save Changes**

### Marking a Case as Resolved

**Option 1: Quick Resolve**
1. Open case detail dialog
2. Click **Resolve** button in the header
3. Case status automatically changes to "Resolved"

**Option 2: Edit Mode**
1. Click **Edit**
2. Change Status dropdown to "Resolved"
3. Click **Save Changes**

### Generating a Case Report

1. Open the case detail dialog
2. Click **Generate Report** button in the header
3. Wait for confirmation message
4. Report is saved to `TestOutputs/` directory
5. Share PDF with stakeholders or archive for compliance

## API Endpoints

### New Backend Endpoints

```python
# Add activity to case
POST /api/cases/{case_id}/activities
Body: {
  "activity_type": "note",
  "description": "Contacted user to verify activity",
  "details": {}
}

# Add resolution step
POST /api/cases/{case_id}/resolution-steps
Body: {
  "description": "Isolated host",
  "action_taken": "Disabled network interface",
  "result": "Host successfully isolated"
}

# Add finding to case
POST /api/cases/{case_id}/findings/{finding_id}

# Remove finding from case
DELETE /api/cases/{case_id}/findings/{finding_id}

# Generate case report
POST /api/cases/{case_id}/generate-report
Response: {
  "success": true,
  "filename": "case-123_report_20260114.pdf",
  "path": "TestOutputs/case-123_report_20260114.pdf"
}

# Delete case
DELETE /api/cases/{case_id}
```

## Data Model

### Case Structure

```json
{
  "case_id": "case-2026-01-14-abc123",
  "title": "Suspicious Beaconing Activity",
  "description": "Multiple hosts showing periodic C2 beaconing",
  "status": "in-progress",
  "priority": "high",
  "assignee": "analyst@company.com",
  "finding_ids": ["f-20260114-001", "f-20260114-002"],
  "tags": ["c2", "beaconing"],
  "created_at": "2026-01-14T10:00:00Z",
  "updated_at": "2026-01-14T15:30:00Z",
  
  "timeline": [
    {
      "timestamp": "2026-01-14T10:00:00Z",
      "event": "Case created"
    }
  ],
  
  "notes": [
    {
      "timestamp": "2026-01-14T10:30:00Z",
      "text": "Initial investigation started"
    }
  ],
  
  "activities": [
    {
      "timestamp": "2026-01-14T11:00:00Z",
      "activity_type": "investigation",
      "description": "Analyzed network traffic patterns",
      "details": {}
    }
  ],
  
  "resolution_steps": [
    {
      "timestamp": "2026-01-14T15:00:00Z",
      "description": "Isolated affected hosts",
      "action_taken": "Disabled network interfaces on 3 affected workstations",
      "result": "All hosts successfully isolated, C2 communication stopped"
    }
  ]
}
```

## Best Practices

### Case Management Workflow

1. **Initial Response**
   - Create case when triaging alerts
   - Set appropriate priority
   - Assign to analyst
   - Add relevant findings

2. **Investigation**
   - Log all activities as you work
   - Document findings and observations
   - Update status to "In Progress"
   - Add additional findings as discovered

3. **Containment**
   - Document containment actions in resolution steps
   - Include specific commands/actions taken
   - Record results and verification

4. **Eradication & Recovery**
   - Continue documenting resolution steps
   - Note any remediation activities
   - Track system restoration

5. **Lessons Learned**
   - Add final activities summarizing the case
   - Update status to "Resolved"
   - Generate final report
   - Archive for future reference

### Documentation Tips

- **Be Specific**: Include exact timestamps, hostnames, IPs, and commands
- **Be Clear**: Write for an audience that wasn't involved
- **Be Comprehensive**: Document decisions and rationale
- **Be Timely**: Log activities as you work, not after
- **Be Consistent**: Use standard activity types and terminology

### Report Generation

- Generate interim reports during long investigations
- Create final reports when marking cases as resolved
- Share reports with management for visibility
- Archive reports for compliance requirements
- Use reports for post-incident reviews

## Compliance & Auditing

The case management system supports compliance requirements by:

- **Complete Audit Trail**: All activities timestamped and logged
- **Immutable Records**: Timeline events cannot be deleted
- **PDF Reports**: Professional documentation for auditors
- **Searchable History**: Filter cases by status, priority, date
- **Assignee Tracking**: Clear responsibility and ownership

## Troubleshooting

### Report Generation Fails

**Error**: "Report generation requires reportlab"

**Solution**: Install reportlab:
```bash
pip install reportlab
```

### Findings Not Loading

**Issue**: Findings tab shows empty

**Solution**: 
- Check that findings exist in the system
- Verify finding IDs are correct
- Refresh the case view

### Activities Not Saving

**Issue**: Activities disappear after adding

**Solution**:
- Check browser console for errors
- Verify backend is running
- Check data file permissions in `data/cases.json`

## Future Enhancements

Planned improvements for the case management system:

- [ ] Case templates for common incident types
- [ ] Bulk case operations
- [ ] Case metrics and analytics dashboard
- [ ] Integration with ticketing systems (Jira, ServiceNow)
- [ ] Automated case creation from alert rules
- [ ] Case collaboration features (comments, mentions)
- [ ] Case search and advanced filtering
- [ ] Custom fields and case metadata
- [ ] SLA tracking and alerting
- [ ] Case playbook integration

## Support

For issues or questions:
- Check the logs in the backend terminal
- Review the browser console for frontend errors
- Consult the main README.md for general setup
- Review APPLICATION_ARCHITECTURE.md for system design

---

**Last Updated**: January 14, 2026
**Version**: 1.0.0

