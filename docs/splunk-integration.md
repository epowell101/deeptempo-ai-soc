# Splunk Integration Guide

## Overview

The Splunk integration enables DeepTempo AI SOC to enrich security cases with data from your Splunk deployment. The enrichment process automatically extracts indicators of compromise (IOCs) from cases and findings, queries Splunk for related events, and uses Claude AI to provide intelligent analysis and insights.

## Features

- **Automatic Indicator Extraction**: Automatically identifies IPs, domains, file hashes, usernames, hostnames, and email addresses from cases and findings
- **Intelligent Querying**: Queries Splunk for events related to extracted indicators
- **AI-Powered Analysis**: Uses Claude AI to analyze Splunk data in context and provide actionable insights
- **Seamless Integration**: Results are automatically added to case notes for easy reference

## Setup

### 1. Configure Splunk Connection

There are two ways to configure Splunk:

#### Option A: Settings Console (Recommended)
1. Open the application
2. Go to **File → Settings Console...**
3. Select the **Splunk** tab
4. Enter your Splunk server details:
   - **Server URL**: Your Splunk server URL (e.g., `https://splunk.example.com:8089`)
   - **Username**: Your Splunk username
   - **Password**: Your Splunk password
   - **Verify SSL**: Enable if using valid SSL certificates
5. Click **Test Connection** to verify
6. Click **Save All** to save your configuration

#### Option B: Quick Configuration Dialog
1. Go to the Cases view
2. Click **Enrich with Splunk** (you'll be prompted to configure)
3. Enter your connection details
4. Click **Test Connection** to verify
5. Click **Save**

### 2. Verify Connection

Always test your connection after configuration to ensure:
- Splunk is reachable
- Credentials are correct
- API access is working

### 3. Configure Claude AI (if not already done)

The enrichment feature uses Claude AI for intelligent analysis. Ensure you have:
1. An Anthropic API key configured
2. Go to **Settings Console → Claude AI** to configure

## Using Splunk Enrichment

### Enriching a Case

1. **Open Cases View**
   - Navigate to the Cases tab in the main window

2. **Select a Case**
   - Click on the case you want to enrich

3. **Start Enrichment**
   - Click the **Enrich with Splunk** button in the toolbar
   - A progress dialog will appear

4. **Review Results**
   - After 1-2 minutes, the enrichment will complete
   - A results dialog shows:
     - Number of Splunk events retrieved
     - AI analysis and insights
   - Results are automatically added to case notes

### What Gets Enriched

The system automatically extracts and queries for:

- **IP Addresses**: Source and destination IPs from findings
- **Domain Names**: Any domains mentioned in findings or case data
- **File Hashes**: MD5, SHA1, and SHA256 hashes
- **Usernames**: User accounts involved in incidents
- **Hostnames**: System names and endpoints
- **Email Addresses**: Email addresses in case data

### Enrichment Process

1. **Extract Indicators**: IOCs are automatically extracted from:
   - Case title and description
   - Finding details and entity context
   - Notes and metadata

2. **Query Splunk**: For each indicator type:
   - Relevant Splunk searches are executed
   - Results are filtered and aggregated
   - Lookback period: Configurable (default: 7 days)

3. **AI Analysis**: Claude analyzes the data to:
   - Identify patterns and anomalies
   - Correlate events with findings
   - Assess risk level
   - Provide actionable recommendations
   - Suggest next investigation steps

4. **Update Case**: Results are added to case notes:
   - Summary of indicators analyzed
   - Number of events found
   - Full AI analysis
   - Timestamp of enrichment

## Configuration Options

### Lookback Period

Configure how far back to search in Splunk:
- Default: 168 hours (7 days)
- Configurable in: **Settings Console → Splunk → Query Settings**
- Range: 1 hour to 720 hours (30 days)

### SSL Verification

- **Enabled**: Verify SSL certificates (recommended for production)
- **Disabled**: Skip verification (for self-signed certificates or testing)

## Troubleshooting

### Connection Issues

**Problem**: "Authentication failed"
- **Solution**: Verify username and password are correct
- Check Splunk user has API access permissions

**Problem**: "Connection error"
- **Solution**: Check server URL is correct and includes port (default: 8089)
- Verify network connectivity to Splunk server
- Check firewall rules

**Problem**: "SSL certificate verification failed"
- **Solution**: Disable SSL verification for self-signed certificates
- Or install proper SSL certificates on Splunk server

### Enrichment Issues

**Problem**: "No events found"
- **Solution**: 
  - Increase lookback period
  - Verify indicators exist in Splunk data
  - Check Splunk search permissions

**Problem**: "Enrichment takes too long"
- **Solution**:
  - Reduce lookback period
  - Case may have many indicators
  - Check Splunk server performance

**Problem**: "AI analysis not available"
- **Solution**: Ensure Claude AI is configured in Settings Console

## API Requirements

### Splunk Requirements

- Splunk Enterprise 7.0 or later
- Splunk REST API access enabled
- User account with search permissions
- Network access to Splunk management port (default: 8089)

### Required Permissions

The Splunk user needs:
- `can_search` capability
- Access to relevant indexes
- `rest_properties_get` capability

## Security Considerations

- **Credentials Storage**: Passwords are stored locally in configuration files
- **Recommendation**: Use a dedicated service account with minimal required permissions
- **Network Security**: Use SSL/TLS when possible
- **Access Control**: Restrict access to DeepTempo configuration files

## Best Practices

1. **Test Connection Regularly**: Ensure Splunk connectivity before enrichment
2. **Monitor Lookback Period**: Balance between data completeness and performance
3. **Review Enrichment Results**: Validate AI insights with manual investigation
4. **Update Credentials**: Rotate Splunk passwords regularly
5. **Use SSL**: Enable SSL verification in production environments

## Example Use Cases

### Incident Investigation

1. Analyst creates case for suspicious activity
2. Adds initial findings from SIEM/EDR
3. Clicks "Enrich with Splunk"
4. Reviews Splunk events showing:
   - Related authentication attempts
   - Network connections
   - File activity
   - Process executions
5. Uses AI analysis to:
   - Confirm lateral movement
   - Identify compromised accounts
   - Prioritize response actions

### Threat Hunting

1. Create case for known IOC (e.g., malicious IP)
2. Enrich with Splunk
3. Discover additional indicators:
   - Other IPs communicating with same endpoint
   - Related domains
   - Affected systems
4. Expand investigation based on findings

### Timeline Analysis

1. Use enrichment to build comprehensive timeline
2. Splunk events provide detailed activity log
3. AI analysis identifies key events
4. Export timeline to Timesketch for visualization

## Support

For issues or questions:
- Check application logs for detailed error messages
- Review Splunk server logs for API errors
- Ensure all dependencies are installed (see `requirements.txt`)
- Verify Splunk REST API is accessible

## Future Enhancements

Planned improvements:
- Support for Splunk Cloud
- Custom query templates
- Automatic indicator enrichment on case creation
- Integration with Splunk ES notable events
- Bulk enrichment of multiple cases
- Scheduled enrichment tasks

