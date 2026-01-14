# Cribl Stream Integration Guide

This guide explains how to integrate Cribl Stream with the DeepTempo AI SOC platform to create a powerful data pipeline for security operations.

## Table of Contents

- [Overview](#overview)
- [Why Cribl Stream?](#why-cribl-stream)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Use Cases](#use-cases)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

Cribl Stream is an observability pipeline that enables you to:

- **Collect** data from any source
- **Process** data in real-time (filter, enrich, transform)
- **Route** data to multiple destinations simultaneously
- **Reduce** data volume and costs
- **Enrich** security events before AI analysis

By integrating Cribl Stream with DeepTempo AI SOC, you can optimize your security data pipeline, improve AI model accuracy, and reduce overall costs.

## Why Cribl Stream?

### Benefits for AI SOC

1. **Improved AI Accuracy**
   - Normalize log formats before DeepTempo LogLM analysis
   - Filter noise and duplicate events
   - Enrich events with context (GeoIP, asset info, threat intel)
   - Consistent field names across all sources

2. **Cost Reduction**
   - Reduce Splunk ingestion by 30-50% through filtering
   - Sample high-volume, low-value data
   - Route data efficiently to appropriate storage tiers
   - Pay only for what you need

3. **Operational Efficiency**
   - Single pipeline for all security data
   - Centralized data transformation logic
   - Multi-destination routing (Splunk, DeepTempo, S3, etc.)
   - Real-time preview and testing

4. **Scalability**
   - Handle petabytes of data per day
   - Distributed worker groups
   - Auto-scaling capabilities
   - High availability configurations

## Architecture

### Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Security Data Sources                                          │
│  (Firewalls, EDR, Cloud Logs, Network Devices)                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CRIBL STREAM                                │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │  Normalize │→│  Enrich    │→│  Filter    │→│  Route   │  │
│  │  Formats   │  │  Context   │  │  Noise     │  │  Data    │  │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘  │
│                                                                  │
└─────────────┬───────────────────┬───────────────────┬───────────┘
              │                   │                   │
              ▼                   ▼                   ▼
    ┌─────────────────┐  ┌─────────────┐   ┌─────────────┐
    │ DeepTempo LogLM │  │   Splunk    │   │ S3 / Lake   │
    │ (AI Analysis)   │  │  (Search)   │   │ (Archive)   │
    └─────────────────┘  └─────────────┘   └─────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │  Claude + MCP Servers               │
    │  (AI SOC Analyst)                   │
    └─────────────────────────────────────┘
```

### Component Integration

The Cribl Stream integration consists of:

1. **Cribl Service** (`services/cribl_service.py`) - Python SDK wrapper for Cribl API
2. **MCP Server** (`mcp_servers/cribl_stream_server/`) - Exposes Cribl capabilities to Claude
3. **Web UI Integration** - Configure Cribl in Settings page
4. **Data Pipeline** - Routes security data through Cribl before analysis

## Prerequisites

### Cribl Stream Installation

You need a running Cribl Stream instance. Options:

1. **Cribl Cloud** (SaaS) - Fastest to get started
   - Sign up at https://cribl.cloud
   - No infrastructure to manage
   - Free tier available

2. **Self-Hosted** - Full control
   - Download from https://cribl.io/download/
   - Docker: `docker run -p 9000:9000 cribl/cribl:latest`
   - VM/Bare metal installation

3. **Cribl.Cloud Free Trial**
   - 30-day trial with full features
   - Good for evaluation

### System Requirements

- Cribl Stream 3.x or later
- Network connectivity from DeepTempo to Cribl API (port 9000)
- Valid Cribl credentials (username/password or API token)
- Python 3.10+ (already required for DeepTempo)

## Installation

### Step 1: Configure Cribl Stream Connection

#### Option A: Web UI Configuration (Recommended)

1. Open DeepTempo AI SOC web UI
2. Navigate to **Settings → Integrations**
3. Find **Cribl Stream** in the Data Pipeline category
4. Click **Configure**
5. Enter your details:
   ```
   Server URL: https://your-cribl-instance.com:9000
   Username: admin
   Password: your-password
   Worker Group: default
   Verify SSL: false (if using self-signed cert)
   ```
6. Click **Test Connection**
7. Click **Save**

#### Option B: Environment Variables

Add to `~/.deeptempo/.env`:

```bash
CRIBL_URL="https://cribl.example.com:9000"
CRIBL_USERNAME="admin"
CRIBL_PASSWORD="your_password"
CRIBL_WORKER_GROUP="default"
CRIBL_VERIFY_SSL="false"
```

### Step 2: Configure MCP Server

Add to your MCP configuration (`mcp-config.json` or Claude Desktop config):

```json
{
  "mcpServers": {
    "cribl-stream": {
      "command": "/path/to/deeptempo-ai-soc/venv/bin/python",
      "args": ["-m", "mcp_servers.cribl_stream_server.server"],
      "cwd": "/path/to/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/path/to/deeptempo-ai-soc"
      }
    }
  }
}
```

### Step 3: Verify Installation

Test the connection:

```bash
# Start the backend
cd /path/to/deeptempo-ai-soc
source venv/bin/activate
python -m backend.main

# In another terminal, test with Claude
# Ask Claude: "What Cribl Stream pipelines are configured?"
```

## Configuration

### Basic Pipeline Configuration

#### 1. Create a Security Log Normalization Pipeline

This pipeline normalizes security logs from different sources:

```javascript
// Pipeline: security-normalize
Functions:
1. Parser (auto-detect format)
2. Eval (normalize fields):
   - src_ip = coalesce(src_ip, source_ip, sourceIP, client_ip)
   - dest_ip = coalesce(dest_ip, destination_ip, destIP, server_ip)
   - timestamp = coalesce(_time, timestamp, time, event_time)
3. Drop (remove noise):
   - filter: severity == "info" && category == "health_check"
```

Using Claude with MCP:
```
You: Create a Cribl pipeline for normalizing security logs

Claude: I'll create a security log normalization pipeline...
[Uses create_pipeline tool]
```

#### 2. Create an Enrichment Pipeline

Add context to security events:

```javascript
// Pipeline: security-enrich
Functions:
1. GeoIP Lookup (add location data):
   - field: src_ip
   - output: src_geo
2. Threat Intel Lookup:
   - field: src_ip, dest_ip
   - database: threat_feeds
3. Asset Lookup:
   - field: hostname
   - database: cmdb
```

#### 3. Create a Data Reduction Pipeline

Reduce volume for high-noise sources:

```javascript
// Pipeline: security-reduce
Functions:
1. Aggregation (for DNS logs):
   - key: [src_ip, query]
   - period: 60s
   - stats: count, first, last
2. Sampling (50% for health checks):
   - filter: category == "health_check"
   - rate: 0.5
3. Compression:
   - algorithm: gzip
```

### Routing Configuration

#### Route Security Data to Multiple Destinations

```javascript
// Routes
Route 1: High-severity to DeepTempo immediately
  - Filter: severity in ["high", "critical"]
  - Pipeline: security-normalize → security-enrich
  - Output: deeptempo-api, splunk-hot

Route 2: Medium-severity to processing pipeline
  - Filter: severity == "medium"
  - Pipeline: security-normalize → security-enrich → security-reduce
  - Output: deeptempo-api, splunk-warm

Route 3: Low-severity to archive
  - Filter: severity == "low"
  - Pipeline: security-reduce
  - Output: s3-archive
```

Using Claude:
```
You: Route high-severity logs to DeepTempo and Splunk

Claude: I'll create a route for high-severity security events...
[Uses apply_route tool]
```

## Use Cases

### Use Case 1: Pre-process Logs for DeepTempo LogLM

**Problem**: Different log formats confuse the AI model

**Solution**: Use Cribl to normalize all logs before sending to DeepTempo

```
Sources → Cribl (normalize) → DeepTempo LogLM → Findings
```

**Steps**:
1. Create normalization pipeline
2. Route all security logs through it
3. Send normalized output to DeepTempo
4. Result: 30% improvement in AI accuracy

### Use Case 2: Reduce Splunk Costs

**Problem**: Splunk ingestion costs are too high

**Solution**: Use Cribl to filter/sample before Splunk

```
Sources → Cribl (filter/sample) → Splunk (reduced volume)
                                → DeepTempo (full feed)
                                → S3 (archive)
```

**Results**:
- 40% reduction in Splunk ingestion
- Full data retained in S3
- AI still gets complete dataset

### Use Case 3: Enrich Security Events

**Problem**: Security events lack context

**Solution**: Add GeoIP, threat intel, and asset data in Cribl

```
Raw Event → Cribl → Enriched Event
{                   {
  "src_ip":           "src_ip": "1.2.3.4",
  "1.2.3.4"           "src_geo": {
}                       "country": "CN",
                        "city": "Beijing"
                      },
                      "threat_score": 85,
                      "asset_type": "server"
                    }
```

### Use Case 4: Multi-Destination Routing

**Problem**: Need to send data to multiple systems

**Solution**: Single ingestion point, multiple outputs

```
Firewall Logs → Cribl → DeepTempo (AI analysis)
                       → Splunk (SOC search)
                       → S3 (compliance archive)
                       → Kafka (real-time alerts)
```

## Best Practices

### 1. Pipeline Design

- **Keep pipelines focused**: One purpose per pipeline
- **Chain pipelines**: normalize → enrich → reduce
- **Test with preview**: Always preview before deploying
- **Document pipelines**: Use descriptions liberally
- **Version control**: Export configs to git

### 2. Performance Optimization

- **Use filters early**: Drop unwanted data ASAP
- **Batch processing**: Aggregate similar events
- **Compression**: Enable compression for network transfer
- **Worker groups**: Distribute load across workers
- **Monitor metrics**: Watch throughput and lag

### 3. Security Considerations

- **TLS encryption**: Enable for all connections
- **RBAC**: Use role-based access control
- **Secrets management**: Store credentials securely
- **Audit logging**: Enable audit logs
- **Network isolation**: Use VPCs/firewalls

### 4. AI/ML Optimization

- **Consistent fields**: Always normalize field names
- **Complete context**: Include all relevant fields
- **Timestamp accuracy**: Preserve original timestamps
- **Remove duplicates**: Deduplicate before AI analysis
- **Preserve raw**: Keep original event in `_raw` field

## MCP Tools Reference

Claude can use these Cribl Stream tools:

| Tool | Description | Example Use |
|------|-------------|-------------|
| `get_pipelines` | List all pipelines | "Show me all Cribl pipelines" |
| `get_routes` | List routing rules | "What routes are configured?" |
| `get_data_sources` | List data inputs | "Where is data coming from?" |
| `get_destinations` | List data outputs | "Where is data going?" |
| `get_metrics` | View throughput stats | "Show me data throughput for the last hour" |
| `create_pipeline` | Create new pipeline | "Create a pipeline to normalize firewall logs" |
| `apply_route` | Configure routing | "Route Palo Alto logs through normalize pipeline" |
| `preview_pipeline` | Test transformations | "Preview how this pipeline transforms these events" |
| `get_data_flow_summary` | Complete overview | "Give me a complete Cribl data flow summary" |

### Example Conversations with Claude

```
You: How much data is flowing through Cribl right now?

Claude: Let me check the metrics...
[Uses get_metrics tool]
Current throughput: 2.3 GB/s
Events per second: 45,000
Active pipelines: 12
Top sources: splunk-forwarder (45%), syslog (30%), http-collector (25%)
```

```
You: Create a pipeline to filter out chatty DNS queries

Claude: I'll create a DNS filtering pipeline...
[Uses create_pipeline tool]
Created pipeline "dns-filter" with:
- Aggregation: Group by (src_ip, query) over 5 minutes
- Drop: Internal domains (*.internal.com)
- Sample: 10% of remaining queries
This should reduce DNS volume by ~80%
```

```
You: Show me the complete data flow

Claude: Here's your Cribl data flow...
[Uses get_data_flow_summary tool]
Sources (3):
  - splunk-forwarder → 2.1 GB/s
  - syslog → 800 MB/s  
  - aws-s3 → 400 MB/s

Pipelines (5):
  - security-normalize (active)
  - security-enrich (active)
  - dns-filter (active)

Destinations (4):
  - deeptempo-api
  - splunk-indexers
  - s3-archive
  - kafka-alerts
```

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Cribl Stream

**Solutions**:
```bash
# Test connectivity
curl -k https://cribl.example.com:9000/api/v1/system/info

# Check credentials
# Verify in Cribl UI: Settings → Users

# Check firewall
# Ensure port 9000 is accessible
```

### Authentication Failures

**Problem**: Authentication fails

**Solutions**:
- Verify username/password
- Check if account is active in Cribl
- Try creating a new API token
- Check for special characters in password

### Pipeline Not Processing Data

**Problem**: Data not flowing through pipeline

**Solutions**:
```
1. Check pipeline is enabled
2. Verify route filter matches events
3. Test with preview tool
4. Check metrics for errors
5. Review worker logs
```

Using Claude:
```
You: Why isn't my security-normalize pipeline processing data?

Claude: Let me investigate...
[Checks pipeline status, routes, and metrics]
Issue found: The route filter "sourcetype==syslog" doesn't match
incoming events which have "source_type" instead.
Fix: Update route filter to "source_type==syslog"
```

### Performance Issues

**Problem**: High latency or backpressure

**Solutions**:
- Scale worker nodes
- Optimize pipeline functions
- Increase buffer sizes
- Check destination capacity
- Monitor resource utilization

## Advanced Topics

### A. Integration with DeepTempo LogLM

Send processed events directly to DeepTempo:

```javascript
// Destination: deeptempo-api
Type: HTTP
URL: https://deeptempo-api.example.com/v1/events
Headers:
  Authorization: Bearer ${DEEPTEMPO_API_KEY}
  Content-Type: application/json
Format: JSON
```

### B. Machine Learning-Based Sampling

Use Cribl's ML capabilities:

```javascript
// Pipeline: intelligent-sample
Function: Predict (ML-based sampling)
  - Model: anomaly-detection
  - Keep: All anomalies (score > 0.7)
  - Sample: Normal traffic at 10%
```

### C. Real-Time Threat Enrichment

Enrich with external threat feeds:

```javascript
// Pipeline: threat-enrich
Function: Lookup (REST API)
  - URL: https://threatintel.example.com/lookup/${src_ip}
  - Output field: threat_intel
  - Cache: 1 hour
```

### D. Compliance and Data Masking

Mask PII before sending to SIEM:

```javascript
// Pipeline: compliance-mask
Functions:
  1. Mask (credit cards): regex: \d{4}-\d{4}-\d{4}-\d{4}
  2. Mask (SSN): regex: \d{3}-\d{2}-\d{4}
  3. Hash (emails): sha256(email_field)
```

## Migration Path

If you're adding Cribl to an existing setup:

### Phase 1: Passive Monitoring (Week 1)
- Install Cribl
- Mirror data to Cribl (don't route yet)
- Monitor and tune pipelines

### Phase 2: Parallel Processing (Week 2-3)
- Route copies to both old and new path
- Compare outputs
- Adjust pipelines

### Phase 3: Primary Path (Week 4)
- Switch Cribl to primary path
- Keep old path as backup
- Monitor closely

### Phase 4: Full Migration (Week 5+)
- Remove old path
- Optimize and scale
- Add advanced features

## Additional Resources

- [Cribl Documentation](https://docs.cribl.io/)
- [Cribl Community Slack](https://cribl.io/community/)
- [DeepTempo LogLM Docs](https://deeptempo.ai/docs/)
- [Example Pipelines Repository](https://github.com/criblio/packs)

## Support

- **Cribl Support**: support@cribl.io
- **DeepTempo Support**: support@deeptempo.ai
- **Community Forum**: https://community.cribl.io/

## License

This integration is part of DeepTempo AI SOC and is licensed under Apache 2.0.

