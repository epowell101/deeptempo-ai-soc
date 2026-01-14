# AI-Powered Custom Integration Builder

## Overview

The Custom Integration Builder is an AI-powered tool that automatically generates complete MCP (Model Context Protocol) server integrations from API documentation. Simply provide documentation for any security tool, and Claude AI will analyze it and generate:

- Integration metadata (UI configuration)
- Complete MCP server code
- Configuration schemas
- Tool definitions

## Features

✨ **AI-Powered Analysis**: Uses Claude to understand API documentation
💬 **Interactive Mode**: Claude asks clarifying questions when needed
🔧 **Complete Code Generation**: Generates production-ready MCP server code
📝 **Automatic Configuration**: Creates UI fields and validation automatically
🎯 **Multi-Step Wizard**: Guided process from documentation to deployment
✅ **Code Validation**: Validates generated code before saving
🔄 **Dynamic Loading**: Custom integrations appear alongside built-in ones

## How to Use

### Step 1: Access the Builder

1. Navigate to **Settings** → **Integrations** tab
2. Click the **"Build Custom Integration"** button in the top-right corner

### Step 2: Provide Documentation

You have two options:

**Option A: Upload a Documentation File**
- Click "Upload Documentation File"
- Select a text file (.txt, .md, .pdf, .doc)
- Supported formats: Text, Markdown, PDF, Word documents

**Option B: Paste Documentation**
- Paste API documentation directly into the text area
- Include:
  - API endpoints and methods
  - Authentication details
  - Request/response examples
  - Parameter descriptions

**Configuration Options:**
- **Integration Category**: Choose the most appropriate category (Threat Intelligence, EDR/XDR, etc.)
- **Integration Name** (optional): Specify a custom name, or leave blank to auto-generate

### Interactive Mode (Optional)

If your documentation is unclear or incomplete, Claude may ask clarifying questions:

```
Claude: "I have some questions:

1. Which endpoints should I prioritize?
2. What authentication method should I use?
3. Should I include rate limiting?"

Your Answer: "Focus on search and details endpoints.
Use API key in X-API-Key header.
Yes, rate limit is 100/min."
```

See [Interactive Integration Mode](./INTERACTIVE_INTEGRATION_MODE.md) for complete details.

### Step 3: Review & Edit

After Claude generates the integration (or after you answer questions), you'll see:

- **Integration Details**: Name, ID, category, description
- **Configuration Fields**: Auto-generated fields for API keys, URLs, etc.
- **MCP Server Code**: Complete Python implementation

You can:
- Review the generated metadata
- View and edit the server code
- Preview the complete implementation

### Step 4: Test & Save

The wizard will:
1. Validate the generated code syntax
2. Check for required MCP server components
3. Display validation results

After validation:
- Click **"Save Integration"** to add it to your system
- The integration will appear in the integrations list
- Configure it with your API credentials
- Enable it to start using it

## What Gets Generated

### 1. Integration Metadata

```json
{
  "id": "custom-my-security-tool",
  "name": "My Security Tool",
  "category": "Threat Intelligence",
  "description": "Brief description of the tool",
  "functionality_type": "Data Enrichment",
  "fields": [
    {
      "name": "api_key",
      "label": "API Key",
      "type": "password",
      "required": true,
      "placeholder": "Your API key",
      "helpText": "Get your API key from..."
    }
  ],
  "docs_url": "https://..."
}
```

### 2. MCP Server Code

A complete Python MCP server implementation including:
- Configuration loading from `config_utils`
- Tool definitions with schemas
- Error handling
- API client integration
- Async/await patterns

Example structure:
```python
"""MCP Server for Custom Integration."""
import asyncio
import logging
from mcp.server import Server
import mcp.types as types

server = Server("custom-integration-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_threats",
            description="Search for threats",
            inputSchema={...}
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    # Implementation here
    pass
```

## Best Practices

### Documentation Quality

For best results, provide comprehensive documentation:

✅ **Good Documentation Includes:**
- Clear API endpoint descriptions
- Authentication methods (API key, OAuth, etc.)
- Request/response examples
- Parameter types and descriptions
- Error codes and handling
- Rate limits and best practices

❌ **Poor Documentation:**
- Incomplete endpoint information
- Missing authentication details
- No examples or parameter descriptions

### Example Documentation Format

```markdown
# MyTool API Documentation

## Authentication
API Key authentication via header: `X-API-Key: your_key_here`

## Endpoints

### Search Threats
GET /api/v1/threats/search

Parameters:
- query (string, required): Search query
- limit (integer, optional): Max results (default: 10)

Response:
{
  "threats": [...],
  "count": 42
}

### Get Threat Details
GET /api/v1/threats/{threat_id}

Returns detailed information about a specific threat.
```

## File Locations

Generated integrations are stored in:
- **Metadata**: `~/.deeptempo/custom_integrations/metadata.json`
- **Server Code**: `~/.deeptempo/custom_integrations/{integration-id}_server.py`

## API Endpoints

The Custom Integration Builder exposes these REST API endpoints:

### Generate Integration
```
POST /api/custom-integrations/generate
Body: {
  "documentation": "...",
  "integration_name": "My Tool" (optional),
  "category": "Threat Intelligence"
}
```

### Generate from File
```
POST /api/custom-integrations/generate/upload
Body (multipart/form-data):
- file: documentation file
- integration_name: optional
- category: optional
```

### Save Integration
```
POST /api/custom-integrations/save
Body: {
  "integration_id": "...",
  "metadata": {...},
  "server_code": "..."
}
```

### List Custom Integrations
```
GET /api/custom-integrations/list
```

### Validate Integration
```
POST /api/custom-integrations/{integration_id}/validate
```

### Delete Integration
```
DELETE /api/custom-integrations/{integration_id}
```

## Advanced Usage

### Manual Code Editing

If the generated code needs adjustments:

1. In the "Review & Edit" step, click **"View Full Code"**
2. Edit the Python code directly in the dialog
3. The edited code will be saved instead of the original

### Adding Custom Tools

After generation, you can manually add more tools to the MCP server:

1. Open the generated file: `~/.deeptempo/custom_integrations/{id}_server.py`
2. Add new tool definitions in `handle_list_tools()`
3. Implement handlers in `handle_call_tool()`
4. Save and restart the MCP server

### Integration Categories

Custom integrations can be assigned to any category:
- Threat Intelligence
- EDR/XDR
- SIEM
- Cloud Security
- Identity & Access
- Network Security
- Incident Management
- Communications
- Sandbox Analysis
- Forensics & Analysis
- **Custom** (default for generated integrations)

## Troubleshooting

### Claude API Not Configured

**Error**: "Claude API is not configured"

**Solution**: Configure Claude API key in Settings → Claude API Configuration

### Invalid Generated Code

**Issue**: Validation fails with syntax errors

**Solutions**:
1. Review the documentation provided - it may be unclear or incomplete
2. Edit the generated code manually in the preview dialog
3. Try regenerating with more detailed documentation

### Integration Not Appearing

**Issue**: Custom integration doesn't show up after saving

**Solutions**:
1. Refresh the settings page
2. Check browser console for errors
3. Verify the integration was saved: check `~/.deeptempo/custom_integrations/metadata.json`

### MCP Server Won't Start

**Issue**: Custom integration MCP server fails to start

**Solutions**:
1. Validate the integration code via the API
2. Check the MCP server logs
3. Ensure all required Python packages are installed
4. Verify the configuration is complete

## Examples

### Example 1: Threat Feed API

**Input Documentation:**
```
ThreatFeed API v2

Authentication: Bearer token in Authorization header

GET /api/v2/feeds/latest
Returns the latest threat feed entries

Parameters:
- limit: integer (max 100)
- category: string (malware, phishing, etc.)

Response:
{
  "entries": [
    {
      "id": "...",
      "indicator": "...",
      "type": "ip",
      "confidence": 85
    }
  ]
}
```

**Generated Integration:**
- ID: `custom-threatfeed`
- Name: ThreatFeed
- Category: Threat Intelligence
- Tools: `get_latest_threats`, `search_by_indicator`
- Config Fields: `api_token`, `base_url`

### Example 2: EDR Platform

**Input Documentation:**
```
SecureEDR API Documentation

Authentication: API Key via X-Api-Key header

Endpoints:
1. GET /v1/devices - List all monitored devices
2. GET /v1/alerts - Get security alerts
3. POST /v1/isolate - Isolate a device

Alert Object:
{
  "id": "...",
  "severity": "high",
  "device_id": "...",
  "description": "..."
}
```

**Generated Integration:**
- ID: `custom-secureedr`
- Name: SecureEDR
- Category: EDR/XDR
- Tools: `list_devices`, `get_alerts`, `isolate_device`
- Config Fields: `api_key`, `base_url`

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────┐
│           Frontend (React)                   │
│  ┌───────────────────────────────────────┐  │
│  │  CustomIntegrationBuilder Component   │  │
│  │  - Multi-step wizard                  │  │
│  │  - Documentation input                │  │
│  │  - Code preview & editing             │  │
│  │  - Validation display                 │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    ↓ REST API
┌─────────────────────────────────────────────┐
│           Backend (FastAPI)                  │
│  ┌───────────────────────────────────────┐  │
│  │  custom_integrations.py (API Router)  │  │
│  │  - /generate                          │  │
│  │  - /save                              │  │
│  │  - /list                              │  │
│  │  - /validate                          │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│        Services (Business Logic)             │
│  ┌───────────────────────────────────────┐  │
│  │  CustomIntegrationService             │  │
│  │  - Uses Claude API for analysis       │  │
│  │  - Generates metadata & code          │  │
│  │  - Saves to filesystem                │  │
│  │  - Validates Python code              │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│            Claude Service                    │
│  - Analyzes documentation                    │
│  - Generates integration code                │
│  - Uses structured prompts                   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Filesystem Storage                   │
│  ~/.deeptempo/custom_integrations/           │
│  - metadata.json                             │
│  - {integration-id}_server.py                │
└─────────────────────────────────────────────┘
```

### Data Flow

1. **User provides documentation** → Frontend wizard
2. **Documentation sent to backend** → `POST /api/custom-integrations/generate`
3. **Backend calls Claude** → `CustomIntegrationService.generate_integration()`
4. **Claude analyzes & generates** → Returns JSON with metadata + code
5. **Backend parses response** → Validates structure
6. **Returns to frontend** → Displays in wizard
7. **User reviews & saves** → `POST /api/custom-integrations/save`
8. **Backend saves files** → Filesystem storage
9. **Integration loads dynamically** → Appears in UI

## Security Considerations

### API Key Handling

- Generated integrations use the same secure configuration system as built-in integrations
- API keys are stored using `config_utils.py` and the secrets manager
- Keys are never exposed in logs or error messages

### Code Validation

- All generated code is validated before saving
- Syntax errors are caught and reported
- Required MCP server components are checked

### File Permissions

- Custom integration files are stored in user's home directory
- Proper file permissions are enforced
- Only the user can read/write integration files

## Future Enhancements

Planned improvements:
- [ ] Support for more authentication methods (OAuth, JWT, etc.)
- [ ] Visual tool builder for manual customization
- [ ] Integration testing framework
- [ ] Community sharing of custom integrations
- [ ] Templates for common API patterns
- [ ] Automatic dependency detection and installation
- [ ] Version control for custom integrations
- [ ] Integration marketplace

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review generated code in `~/.deeptempo/custom_integrations/`
3. Check backend logs for detailed error messages
4. Ensure Claude API is properly configured

## Related Documentation

- [MCP Servers Guide](./mcp-servers-inventory.md)
- [Integration Wizard Guide](./integration-wizard-guide.md)
- [Secrets Management](./secrets-management.md)
- [Agent Quick Reference](./agent-quick-reference.md)

