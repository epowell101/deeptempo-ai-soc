# Cribl Stream Quick Start Guide

Get Cribl Stream integrated with DeepTempo AI SOC in 15 minutes.

## Quick Overview

Cribl Stream optimizes your security data pipeline by:
- 📊 **Normalizing** logs before AI analysis → Better accuracy
- 💰 **Reducing** data volume → 30-50% cost savings
- 🔍 **Enriching** events with context → Faster investigations
- 🚀 **Routing** to multiple destinations → Flexible architecture

## Prerequisites Checklist

- [ ] Cribl Stream instance (Cloud or self-hosted)
- [ ] Cribl admin credentials
- [ ] Network access to Cribl API (port 9000)
- [ ] DeepTempo AI SOC installed

## 5-Minute Setup

### Step 1: Get Cribl Stream (Choose One)

#### Option A: Cribl Cloud (Easiest)
```bash
# Sign up for free trial
open https://cribl.cloud/signup

# Get your credentials from the welcome email
# Server URL will be: https://<your-org>.cribl.cloud:9000
```

#### Option B: Docker (Fastest Local Setup)
```bash
# Start Cribl Stream
docker run -d \
  --name cribl-stream \
  -p 9000:9000 \
  -p 10080:10080 \
  -e CRIBL_ADMIN_PASSWORD=your-password \
  cribl/cribl:latest

# Access UI at http://localhost:9000
# Default user: admin / Password: your-password
```

#### Option C: Download Binary
```bash
# Download from https://cribl.io/download/
curl -o cribl.tgz https://cdn.cribl.io/dl/latest/cribl-linux-x64.tgz
tar xvfz cribl.tgz
cd cribl
bin/cribl start
```

### Step 2: Configure in DeepTempo

#### Via Web UI (Recommended)
```bash
# 1. Start DeepTempo web UI
cd /path/to/deeptempo-ai-soc
./start_web.sh

# 2. Open browser
open http://localhost:5173

# 3. Navigate to Settings → Integrations
# 4. Find "Cribl Stream" under "Data Pipeline"
# 5. Click Configure and enter:
Server URL: https://your-cribl-instance.com:9000
Username: admin
Password: your-password
Worker Group: default
Verify SSL: false (for testing)

# 6. Click "Test Connection"
# 7. Click "Save"
```

#### Via Environment Variables
```bash
# Add to ~/.deeptempo/.env
cat >> ~/.deeptempo/.env << EOF

# Cribl Stream Configuration
CRIBL_URL="https://your-cribl.example.com:9000"
CRIBL_USERNAME="admin"
CRIBL_PASSWORD="your-password"
CRIBL_WORKER_GROUP="default"
CRIBL_VERIFY_SSL="false"
EOF
```

### Step 3: Enable MCP Server

Add to your MCP config:

**For Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
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

**For project MCP config** (`mcp-config.json`):
```json
{
  "cribl-stream": {
    "command": "python",
    "args": ["-m", "mcp_servers.cribl_stream_server.server"],
    "cwd": ".",
    "env": {
      "PYTHONPATH": "."
    }
  }
}
```

### Step 4: Verify Setup

```bash
# Test the service
cd /path/to/deeptempo-ai-soc
source venv/bin/activate
python << EOF
from services.cribl_service import CriblService
cribl = CriblService(
    "https://your-cribl:9000",
    "admin",
    "your-password"
)
success, msg = cribl.test_connection()
print(f"✓ {msg}" if success else f"✗ {msg}")
EOF
```

Ask Claude:
```
You: What Cribl pipelines are configured?
Claude: [Lists your pipelines]

You: Show me Cribl data flow summary
Claude: [Shows sources, pipelines, routes, destinations]
```

## First Pipeline: Security Log Normalization

Let's create your first pipeline using Claude:

```
You: Create a Cribl pipeline called "security-normalize" that:
1. Parses common security log formats
2. Normalizes these fields: src_ip, dest_ip, timestamp, severity
3. Drops health check events

Claude: I'll create that security normalization pipeline...
[Creates pipeline with proper functions]
Done! Pipeline "security-normalize" is ready.
```

Or manually via Cribl UI:
1. Open Cribl UI: http://your-cribl:9000
2. Go to **Processing → Pipelines**
3. Click **Add Pipeline**
4. Name it: `security-normalize`
5. Add functions:
   - **Parser** (auto-detect)
   - **Eval**: Normalize fields
   - **Drop**: Filter noise
6. Click **Commit & Deploy**

## First Route: Send to DeepTempo

Route security logs through your pipeline:

```
You: Create a Cribl route that sends all syslog data through 
security-normalize pipeline to my DeepTempo instance

Claude: I'll set up that route...
[Creates route with appropriate filters]
```

Or manually:
1. Go to **Routing → Routes**
2. Click **Add Route**
3. Configure:
   - **Filter**: `__inputId=="syslog:main"`
   - **Pipeline**: `security-normalize`
   - **Output**: `deeptempo-http`
4. **Commit & Deploy**

## Common Use Cases

### Use Case 1: Reduce Splunk Costs

**Problem**: Splunk costs are high

**Solution**:
```
You: Configure Cribl to filter debug logs and sample 
50% of info logs before sending to Splunk, but send 
everything to DeepTempo

Claude: I'll set up cost-optimized routing...
[Creates two routes with different filters]

Route 1: Splunk (filtered)
  - Drops: severity="debug"
  - Samples: 50% of severity="info"
  - Full: severity in ["warning", "error", "critical"]

Route 2: DeepTempo (complete)
  - Sends: All events
  - Pipeline: normalize + enrich
```

**Result**: 40% reduction in Splunk costs, full data in DeepTempo

### Use Case 2: Enrich Before AI Analysis

**Problem**: AI lacks context

**Solution**:
```
You: Add GeoIP lookup and threat intelligence enrichment 
to all security events before DeepTempo analysis

Claude: I'll create an enrichment pipeline...
[Creates pipeline with lookup functions]

Pipeline: security-enrich
  - GeoIP: Adds location to src_ip
  - Threat Intel: Checks IPs against threat feeds
  - Asset Lookup: Adds asset classification

Applied to route → DeepTempo
```

**Result**: 30% improvement in threat detection accuracy

### Use Case 3: Multi-Destination Routing

**Problem**: Need to send different data to different systems

**Solution**:
```
Route High-Severity → DeepTempo + Splunk + PagerDuty
Route Medium-Severity → DeepTempo + Splunk
Route Low-Severity → S3 Archive
```

## Monitoring Your Pipeline

### View Metrics
```
You: Show me Cribl throughput metrics for the last hour

Claude: Current metrics:
- Data In: 2.3 GB/s
- Data Out: 1.8 GB/s  
- Reduction: 22%
- Events/sec: 45,000
- Active Workers: 3
- CPU: 45%
- Memory: 62%
```

### Check Health
```
You: Is Cribl healthy?

Claude: Cribl Stream Status: ✓ Healthy
- All workers: Online
- All routes: Active  
- No backpressure
- API: Responsive
```

## Troubleshooting

### Cannot Connect to Cribl

```bash
# Test connectivity
curl -k https://your-cribl:9000/api/v1/system/info

# Check credentials
# Verify username/password in Cribl UI

# Check firewall
# Ensure port 9000 is accessible
```

### Pipeline Not Processing

```
You: My security-normalize pipeline isn't processing data

Claude: Let me investigate...
[Checks pipeline status, routes, metrics]

Found issues:
1. Pipeline is disabled - enabling it now
2. No routes pointing to this pipeline - creating route
3. Input source is down - check syslog collector

Fixed items 1 and 2. Please check your syslog collector.
```

### Authentication Fails

```bash
# Verify credentials in Cribl UI
# Try creating a new API token

# In Cribl UI:
# Settings → API Tokens → Create New Token
# Use token instead of password
```

## Best Practices

### 1. Start Simple
- ✅ Begin with one pipeline
- ✅ Test with sample data
- ✅ Preview before deploying
- ❌ Don't create complex pipelines initially

### 2. Monitor Performance
- ✅ Check metrics regularly
- ✅ Set up alerts for backpressure
- ✅ Monitor reduction ratio
- ✅ Track CPU/memory usage

### 3. Security
- ✅ Use TLS for all connections
- ✅ Enable authentication
- ✅ Restrict network access
- ✅ Rotate credentials regularly

### 4. AI Optimization
- ✅ Normalize field names
- ✅ Enrich with context
- ✅ Remove duplicate events
- ✅ Keep timestamps accurate

## Next Steps

1. **Read Full Guide**: See `docs/cribl-integration.md`
2. **Example Pipelines**: Check Cribl Packs library
3. **Advanced Features**: Explore ML-based sampling
4. **Scale Up**: Add worker nodes for production

## Quick Reference Commands

```bash
# Test connection
python -m services.cribl_service

# View logs
tail -f ~/.deeptempo/api.log | grep cribl

# Restart MCP server
pkill -f cribl_stream_server

# Check configuration
cat ~/.deeptempo/config.json | jq .cribl
```

## Claude Integration Examples

### List Pipelines
```
You: What Cribl pipelines exist?
Claude: [Lists all pipelines with descriptions]
```

### Create Pipeline
```
You: Create a pipeline to drop noisy DNS logs
Claude: [Creates and deploys pipeline]
```

### Check Data Flow
```
You: Show complete Cribl data flow
Claude: [Displays sources → pipelines → destinations]
```

### Get Metrics
```
You: What's the data reduction rate?
Claude: Current reduction: 35% (2.3 GB/s → 1.5 GB/s)
```

### Route Configuration
```
You: Route firewall logs through normalize pipeline to Splunk
Claude: [Creates and activates route]
```

## Support & Resources

- 📖 **Full Documentation**: `docs/cribl-integration.md`
- 💬 **Cribl Community**: https://cribl.io/community/
- 📺 **Video Tutorials**: https://cribl.io/resources/videos/
- 🎓 **Cribl University**: https://cribl.io/university/
- 📧 **Support**: support@cribl.io

## Cost Savings Calculator

Estimate your savings:

```
Current Splunk Ingestion: 1 TB/day = $3,000/month
With Cribl (35% reduction): 650 GB/day = $1,950/month
Monthly Savings: $1,050
Annual Savings: $12,600

Cribl License: ~$500/month
Net Annual Savings: $6,600
ROI: 13x
```

## Success Metrics

After 30 days with Cribl, you should see:

- ✓ 30-50% reduction in SIEM costs
- ✓ 20-30% improvement in AI accuracy  
- ✓ 50% faster incident investigations
- ✓ Unified data format across all sources
- ✓ Real-time enrichment of all events

---

**Need Help?** Ask Claude: "Help me troubleshoot Cribl integration"

**Ready for More?** Read the full guide: `docs/cribl-integration.md`

