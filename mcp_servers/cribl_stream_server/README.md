# Cribl Stream MCP Server

Model Context Protocol (MCP) server for Cribl Stream integration with DeepTempo AI SOC.

## Overview

This MCP server exposes Cribl Stream data pipeline capabilities to Claude, enabling natural language control of security data processing, routing, and enrichment.

## Features

- **Pipeline Management**: List, create, and preview data processing pipelines
- **Route Configuration**: Configure intelligent data routing
- **Source/Destination Management**: View data inputs and outputs
- **Metrics & Monitoring**: Real-time throughput and performance data
- **Health Checks**: System status and worker health
- **Data Flow Visualization**: Complete pipeline overview

## Available Tools

### 1. `get_pipelines`
List all configured data processing pipelines.

**Example**:
```
You: What Cribl pipelines are configured?
Claude: You have 5 pipelines:
  1. security-normalize - Normalizes security log formats
  2. security-enrich - Adds GeoIP and threat intel
  3. dns-filter - Filters noisy DNS queries
  4. compliance-mask - Masks PII data
  5. cost-reduce - Samples high-volume logs
```

### 2. `get_routes`
List all routing configurations.

**Example**:
```
You: Show me Cribl routes
Claude: Active routes:
  1. High severity → security-enrich → deeptempo + splunk
  2. Medium severity → security-normalize → deeptempo
  3. Low severity → cost-reduce → s3-archive
```

### 3. `get_data_sources`
List all data input sources.

**Example**:
```
You: Where is data coming from?
Claude: Data sources:
  1. splunk-forwarder (syslog) - 2.1 GB/s
  2. aws-cloudwatch (http) - 800 MB/s
  3. palo-alto-fw (syslog) - 400 MB/s
```

### 4. `get_destinations`
List all data output destinations.

**Example**:
```
You: Where is data going?
Claude: Destinations:
  1. deeptempo-api (http) - AI analysis
  2. splunk-indexers (splunk-hec) - SIEM
  3. s3-archive (s3) - Long-term storage
  4. kafka-alerts (kafka) - Real-time alerts
```

### 5. `get_metrics`
Retrieve throughput and performance metrics.

**Example**:
```
You: Show me Cribl metrics for the last hour
Claude: Cribl Stream Metrics (1h):
  Data In: 2.3 GB/s (45,000 events/sec)
  Data Out: 1.8 GB/s (35,000 events/sec)
  Reduction: 22%
  CPU: 45%
  Memory: 62%
  Workers: 3 active
  Backpressure: None
```

### 6. `get_health_status`
Check system health.

**Example**:
```
You: Is Cribl healthy?
Claude: ✓ Cribl Stream is healthy
  - All workers online
  - All routes active
  - No backpressure
  - API responsive
```

### 7. `create_pipeline`
Create a new data processing pipeline.

**Example**:
```
You: Create a pipeline to normalize firewall logs
Claude: Creating pipeline "firewall-normalize"...
  Functions:
    1. Parser (auto-detect)
    2. Eval (normalize src_ip, dest_ip, port)
    3. Drop (filter health checks)
  Pipeline created and deployed!
```

### 8. `apply_route`
Configure data routing.

**Example**:
```
You: Route Palo Alto logs through firewall-normalize to DeepTempo
Claude: Creating route...
  Filter: __inputId=="palo-alto-fw"
  Pipeline: firewall-normalize
  Output: deeptempo-api
  Route created and active!
```

### 9. `preview_pipeline`
Test pipeline with sample data.

**Example**:
```
You: Preview how security-enrich transforms this event: {src_ip: "1.2.3.4"}
Claude: Pipeline Preview:
  Input:  {"src_ip": "1.2.3.4"}
  Output: {
    "src_ip": "1.2.3.4",
    "src_geo": {"country": "CN", "city": "Beijing"},
    "threat_score": 85,
    "asset_type": "server"
  }
```

### 10. `get_data_flow_summary`
Get complete pipeline overview.

**Example**:
```
You: Give me a complete Cribl data flow summary
Claude: Cribl Stream Data Flow:
  
  Sources (3):
    - splunk-forwarder: 2.1 GB/s
    - aws-cloudwatch: 800 MB/s
    - palo-alto-fw: 400 MB/s
  
  Pipelines (5):
    - security-normalize (active)
    - security-enrich (active)
    - dns-filter (active)
    - compliance-mask (active)
    - cost-reduce (active)
  
  Routes (3):
    - High severity → security-enrich → deeptempo + splunk
    - Medium severity → security-normalize → deeptempo
    - Low severity → cost-reduce → s3-archive
  
  Destinations (4):
    - deeptempo-api (http)
    - splunk-indexers (splunk-hec)
    - s3-archive (s3)
    - kafka-alerts (kafka)
```

## Configuration

### Environment Variables

```bash
CRIBL_URL="https://cribl.example.com:9000"
CRIBL_USERNAME="admin"
CRIBL_PASSWORD="your_password"
CRIBL_WORKER_GROUP="default"
CRIBL_VERIFY_SSL="false"
```

### Config File

Add to `~/.deeptempo/config.json`:

```json
{
  "cribl": {
    "server_url": "https://cribl.example.com:9000",
    "username": "admin",
    "password": "your_password",
    "worker_group": "default",
    "verify_ssl": false
  }
}
```

### MCP Configuration

Add to your MCP config file:

```json
{
  "cribl-stream": {
    "command": "python",
    "args": ["-m", "mcp_servers.cribl_stream_server.server"],
    "cwd": "/path/to/deeptempo-ai-soc",
    "env": {
      "PYTHONPATH": "/path/to/deeptempo-ai-soc"
    }
  }
}
```

## Installation

### 1. Install Dependencies

```bash
cd /path/to/deeptempo-ai-soc
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Cribl Connection

```bash
# Via environment
export CRIBL_URL="https://your-cribl:9000"
export CRIBL_USERNAME="admin"
export CRIBL_PASSWORD="your_password"

# Or via config file
cat >> ~/.deeptempo/config.json << EOF
{
  "cribl": {
    "server_url": "https://your-cribl:9000",
    "username": "admin",
    "password": "your_password"
  }
}
EOF
```

### 3. Test Connection

```bash
python << EOF
from services.cribl_service import CriblService
cribl = CriblService(
    "https://your-cribl:9000",
    "admin",
    "your_password"
)
success, msg = cribl.test_connection()
print(msg)
EOF
```

### 4. Start MCP Server

```bash
# Standalone
python -m mcp_servers.cribl_stream_server.server

# Or via MCP client
# (automatically started when configured in mcp-config.json)
```

## Usage Examples

### Example 1: Monitor Data Pipeline

```
You: How much data is flowing through Cribl?

Claude: [Uses get_metrics]
Current throughput: 2.3 GB/s
Events per second: 45,000
Data reduction: 22%
All systems healthy
```

### Example 2: Create Security Pipeline

```
You: Create a pipeline to:
1. Parse security logs
2. Normalize IP and port fields
3. Add GeoIP data
4. Drop health check events

Claude: [Uses create_pipeline]
Created "security-complete" pipeline with:
  - Parser (auto-detect format)
  - Eval (normalize src_ip, dest_ip, src_port, dest_port)
  - GeoIP lookup on src_ip
  - Drop filter for health checks
Pipeline deployed and ready!
```

### Example 3: Investigate Data Quality

```
You: Why is my AI detection accuracy low?

Claude: Let me check the data pipeline...
[Uses get_data_flow_summary]

Found potential issues:
1. Logs from "aws-cloudwatch" are not normalized
2. No enrichment pipeline applied
3. 35% of events have missing fields

Recommendation: Route aws-cloudwatch through 
security-normalize and security-enrich pipelines.

Shall I configure this?
```

### Example 4: Cost Optimization

```
You: Help me reduce Splunk costs

Claude: [Analyzes current routing]
Current: All data → Splunk (1 TB/day = $3,000/month)

Recommendations:
1. Filter debug logs (saves 20%)
2. Sample info logs at 50% (saves 15%)
3. Keep all warnings/errors/critical (0% reduction)
4. Route full feed to DeepTempo for AI analysis

Estimated savings: $1,050/month

Shall I create these routes?
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Claude Desktop                          │
│              (Natural Language Interface)                │
└───────────────────────┬─────────────────────────────────┘
                        │ MCP Protocol
                        ▼
┌─────────────────────────────────────────────────────────┐
│            Cribl Stream MCP Server                       │
│                                                          │
│  Tools:                                                  │
│  • get_pipelines       • create_pipeline                │
│  • get_routes          • apply_route                    │
│  • get_data_sources    • preview_pipeline               │
│  • get_destinations    • get_health_status              │
│  • get_metrics         • get_data_flow_summary          │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP/HTTPS (REST API)
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  Cribl Stream API                        │
│              (https://cribl:9000/api/v1)                │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 Cribl Stream System                      │
│  • Workers  • Pipelines  • Routes  • Metrics            │
└─────────────────────────────────────────────────────────┘
```

## Error Handling

The server handles common errors gracefully:

### Not Configured
```
Error: Cribl Stream not configured
Message: Please configure connection in ~/.deeptempo/config.json
Required:
  - server_url
  - username
  - password
```

### Connection Failed
```
Error: Connection failed
Message: Could not reach Cribl Stream at https://cribl:9000
Check: Network connectivity, firewall rules, SSL settings
```

### Authentication Failed
```
Error: Authentication failed
Message: Invalid credentials
Check: Username and password in configuration
```

### Pipeline Error
```
Error: Failed to create pipeline
Message: Invalid function configuration
Details: [specific error from Cribl API]
```

## Troubleshooting

### Server Won't Start

```bash
# Check Python path
which python
python --version  # Should be 3.10+

# Check dependencies
pip list | grep mcp

# Check PYTHONPATH
echo $PYTHONPATH

# Try manual start
cd /path/to/deeptempo-ai-soc
python -m mcp_servers.cribl_stream_server.server
```

### Cannot Connect to Cribl

```bash
# Test connectivity
curl -k https://your-cribl:9000/api/v1/system/info

# Check credentials
# Verify in Cribl UI: Settings → Users

# Check SSL
# If using self-signed cert, set verify_ssl=false
```

### Tools Not Available in Claude

```bash
# Check MCP config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Restart Claude Desktop
pkill Claude
open -a Claude

# Check logs
tail -f ~/Library/Logs/Claude/mcp-server-cribl-stream.log
```

## Development

### Running Tests

```bash
# Unit tests
python -m pytest tests/test_cribl_service.py

# Integration tests (requires Cribl instance)
CRIBL_URL="https://test-cribl:9000" \
CRIBL_USERNAME="admin" \
CRIBL_PASSWORD="test" \
python -m pytest tests/test_cribl_integration.py
```

### Adding New Tools

1. Add tool definition to `handle_list_tools()`
2. Add tool implementation to `handle_call_tool()`
3. Update this README
4. Add tests

## API Reference

See `services/cribl_service.py` for the underlying Python API.

## Documentation

- **Quick Start**: `docs/cribl-quick-start.md`
- **Full Integration Guide**: `docs/cribl-integration.md`
- **Architecture**: `docs/cribl-architecture-diagram.md`
- **Implementation Summary**: `CRIBL_INTEGRATION_SUMMARY.md`

## Support

- **Cribl Docs**: https://docs.cribl.io/
- **MCP Specification**: https://modelcontextprotocol.io/
- **DeepTempo Support**: support@deeptempo.ai

## License

Apache 2.0 - See LICENSE file

