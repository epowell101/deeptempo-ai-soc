# Investigation Chat PDF Reports

## Overview

You can now print investigation chat summaries as professional PDF reports directly from investigation tabs.

## How to Use

### From an Investigation Tab

1. Open or create an investigation tab (either from the main tab or by analyzing a finding in a new tab)
2. Have a conversation with Claude about your investigation
3. Click the **"📄 Print Chat as PDF"** button in the Quick Actions section
4. Choose where to save the PDF file
5. The PDF will be generated with:
   - Investigation title and metadata
   - Your investigation notes (if any)
   - Summary of focused findings (if any)
   - Complete chat conversation between you and Claude

## PDF Report Contents

The generated PDF report includes:

### Header Section
- Investigation title
- Report generation date
- Total message count
- Number of focused findings

### Investigation Notes
- Any notes you've written in the investigation notes field

### Focused Findings Summary
- Table of all findings being analyzed in this investigation
- Finding ID, severity, data source, and anomaly score

### Chat Conversation
- Complete conversation history
- User messages clearly labeled with 👤
- Assistant (Claude) messages clearly labeled with 🤖
- Proper formatting and pagination

## Tips

- **Before generating the PDF**: Make sure to add any important notes in the "Investigation Notes" section
- **Long conversations**: Very long messages are automatically truncated in the PDF for readability
- **Default location**: PDFs are saved to the `TestOutputs` folder by default
- **File naming**: Default filename includes the tab ID and timestamp for easy tracking
- **Multiple reports**: You can generate multiple PDF snapshots of the same investigation at different points

## Use Cases

- **Documentation**: Create permanent records of your security investigations
- **Reporting**: Share investigation findings with team members or management
- **Compliance**: Maintain audit trails of security analysis work
- **Case files**: Attach investigation reports to security incident cases
- **Knowledge sharing**: Document your analysis methodology for training purposes

## Technical Details

- Generated using ReportLab for professional PDF formatting
- Supports all conversation types (streaming and non-streaming)
- Includes automatic HTML entity escaping for security
- Handles long conversations with automatic pagination
- Material Design color scheme matching the UI theme

