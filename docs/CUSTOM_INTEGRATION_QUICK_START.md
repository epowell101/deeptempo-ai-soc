# Quick Start: Build Your First Custom Integration in 5 Minutes

## What You'll Build

In this quick start, you'll create a custom integration for a hypothetical "ThreatWatch API" in under 5 minutes.

## Prerequisites

✅ Claude API configured in Settings  
✅ DeepTempo AI SOC running  
✅ 5 minutes of your time

## Step-by-Step Guide

### Step 1: Open the Builder (30 seconds)

1. Navigate to **Settings** page
2. Click the **Integrations** tab
3. Click the **"Build Custom Integration"** button (top-right)

### Step 2: Provide Documentation (1 minute)

Copy and paste this sample API documentation:

```markdown
# ThreatWatch API Documentation

## Authentication
Bearer token authentication. Include in header:
Authorization: Bearer YOUR_API_TOKEN

## Base URL
https://api.threatwatch.example.com/v1

## Endpoints

### Get Recent Threats
GET /threats/recent

Returns the most recent security threats.

Parameters:
- limit (integer, optional): Maximum number of results (default: 10, max: 100)
- severity (string, optional): Filter by severity (low, medium, high, critical)
- type (string, optional): Threat type (malware, phishing, ransomware, apt)

Response:
{
  "threats": [
    {
      "id": "threat-12345",
      "title": "APT28 Campaign Detected",
      "severity": "critical",
      "type": "apt",
      "indicators": ["203.0.113.50", "malicious.example.com"],
      "first_seen": "2024-01-15T10:30:00Z",
      "confidence": 95
    }
  ],
  "count": 42
}

### Search Threats
GET /threats/search

Search for specific threats.

Parameters:
- query (string, required): Search query
- limit (integer, optional): Max results

Response: Same as Get Recent Threats

### Get Threat Details
GET /threats/{threat_id}

Get detailed information about a specific threat.

Parameters:
- threat_id (string, required): Threat identifier

Response:
{
  "id": "threat-12345",
  "title": "APT28 Campaign Detected",
  "description": "Detailed threat description...",
  "severity": "critical",
  "type": "apt",
  "indicators": [
    {
      "type": "ip",
      "value": "203.0.113.50",
      "confidence": 95
    }
  ],
  "mitigation": "Recommended actions...",
  "references": ["https://..."]
}

### Check IOC
POST /ioc/check

Check if an indicator of compromise is known.

Request Body:
{
  "indicator": "203.0.113.50",
  "type": "ip"  // ip, domain, hash, email
}

Response:
{
  "found": true,
  "threat_level": "high",
  "associated_threats": ["threat-12345"],
  "last_seen": "2024-01-15T10:30:00Z"
}

## Rate Limits
- 100 requests per minute per API token
- 1000 requests per hour per API token

## Error Codes
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 429: Rate Limit Exceeded
- 500: Internal Server Error
```

**Configuration:**
- **Category**: Select "Threat Intelligence"
- **Name**: Leave blank (will auto-generate "ThreatWatch")

### Step 3: Generate (1 minute)

1. Click **"Generate"** button
2. Wait ~30-60 seconds while Claude analyzes the documentation
3. Claude will generate:
   - Integration metadata
   - Complete MCP server code with 4 tools
   - Configuration schema

### Step 4: Review (1 minute)

You'll see:

**Integration Details:**
- Name: ThreatWatch
- ID: custom-threatwatch
- Category: Threat Intelligence
- Configuration Fields:
  - API Token (password field)
  - Base URL (url field)
  - Rate Limit (number field)

**Generated Tools:**
- `get_recent_threats` - Get recent security threats
- `search_threats` - Search for specific threats
- `get_threat_details` - Get detailed threat information
- `check_ioc` - Check if an IOC is known

**Server Code:**
- Complete Python MCP server
- ~200-300 lines of code
- Includes error handling, rate limiting, authentication

Click **"View Full Code"** to review the generated Python code (optional).

### Step 5: Validate & Save (1 minute)

1. Click **"Validate"** button
2. System checks:
   - ✅ Syntax valid
   - ✅ Has server initialization
   - ✅ Has list_tools decorator
   - ✅ Has call_tool decorator
   - ✅ Has main function
3. Click **"Save Integration"**
4. Success! 🎉

### Step 6: Configure & Enable (1 minute)

1. Close the builder dialog
2. Scroll to the **"Custom"** category
3. Find **ThreatWatch** integration
4. Click **"Configure"**
5. Enter your API credentials:
   - **API Token**: `your-api-token-here`
   - **Base URL**: `https://api.threatwatch.example.com/v1`
6. Click **"Save"**
7. Toggle the switch to **Enable** the integration

### Step 7: Use It!

Your custom integration is now ready! You can use it in Claude conversations:

```
You: "Check ThreatWatch for recent critical threats"

Claude: [uses get_recent_threats tool]
"Found 3 critical threats in ThreatWatch:
1. APT28 Campaign - First seen today at 10:30 AM
2. Ransomware Activity - Targeting healthcare sector
3. Zero-day Exploit - CVE-2024-12345"

You: "Get details on the APT28 campaign"

Claude: [uses get_threat_details tool]
"The APT28 campaign involves:
- IOCs: 203.0.113.50, malicious.example.com
- Confidence: 95%
- Mitigation: Block listed IPs, scan for persistence..."
```

## What Just Happened?

You just:
1. ✅ Provided API documentation
2. ✅ Let Claude AI analyze it
3. ✅ Generated a complete MCP server integration
4. ✅ Validated the code
5. ✅ Saved and configured the integration
6. ✅ Enabled it for use
7. ✅ Started using it in investigations

**Total Time**: ~5 minutes  
**Lines of Code Written**: 0  
**Lines of Code Generated**: ~200-300  

## Next Steps

### Try with Real APIs

Now that you've seen how it works, try with real security tools:

1. **Threat Intelligence Feeds**
   - VirusTotal alternatives
   - Custom threat feeds
   - Internal threat databases

2. **Security Tools**
   - EDR platforms
   - SIEM systems
   - Cloud security tools

3. **Custom Internal Tools**
   - Ticketing systems
   - Asset databases
   - Automation platforms

### Tips for Best Results

✅ **Include in your documentation:**
- Authentication method (API key, Bearer token, OAuth)
- Base URL / endpoint
- Request examples
- Response examples
- Parameter descriptions
- Error codes

❌ **Avoid:**
- Incomplete endpoint descriptions
- Missing authentication details
- No examples

### Common Patterns

**Basic GET Endpoint:**
```markdown
### Get Items
GET /api/v1/items

Parameters:
- limit (integer): Max results
- filter (string): Filter criteria

Response:
{
  "items": [...],
  "count": 42
}
```

**POST with Body:**
```markdown
### Create Item
POST /api/v1/items

Request Body:
{
  "name": "Item Name",
  "type": "item_type"
}

Response:
{
  "id": "item-123",
  "status": "created"
}
```

**Authentication:**
```markdown
## Authentication
API Key: Include in header as X-API-Key: your_key_here
OR
Bearer Token: Authorization: Bearer your_token_here
```

## Troubleshooting

### "Claude API is not configured"
→ Go to Settings → Claude API, add your API key

### Generated code has errors
→ Click "View Full Code" and edit manually  
→ Or regenerate with more detailed documentation

### Integration doesn't appear
→ Refresh the Settings page  
→ Check the Custom category

### Can't enable integration
→ Make sure you've configured it with API credentials first

## Need Help?

- 📖 **Full Documentation**: `docs/custom-integration-builder.md`
- 🔧 **Technical Details**: `CUSTOM_INTEGRATION_BUILDER.md`
- 💬 **Examples**: See the full guide for more examples

## What's Next?

Explore advanced features:
- Edit generated code manually
- Add custom tools to existing integrations
- Share integrations with your team
- Create integration templates

---

**Congratulations! You've built your first AI-generated security integration!** 🎉

