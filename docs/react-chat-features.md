# React UI Chat Features - Complete Guide

## Overview

The new React UI now has **full feature parity** with the old PyQt UI, including all chat settings, deep thinking capabilities, token limits, image/file uploads, and more.

## Features Implemented

### 1. **Chat Settings Panel** ⚙️

Access the settings panel by clicking the gear icon in the top-right of the chat drawer.

#### Model Selection
- Choose from multiple Claude models:
  - **Claude 4.5 Sonnet** - Most intelligent model for complex tasks
  - **Claude 3.5 Sonnet** - Balanced performance
  - **Claude 3.5 Haiku** - Fastest model for simple tasks
- Models are loaded dynamically from the backend

#### Token Configuration
- **Max Tokens**: Set the maximum token limit for responses (256-8192)
- Configurable per conversation
- Default can be set in Settings page

### 2. **Extended Thinking** 🧠

Enable deep reasoning and analysis for complex queries:

- **Toggle**: Enable/disable extended thinking mode
- **Thinking Budget**: Set budget in thousands of tokens (1k-100k)
- When enabled, Claude will use additional compute to reason through complex problems
- Perfect for:
  - Security analysis
  - Complex investigations
  - Multi-step reasoning
  - Technical troubleshooting

**Example Usage:**
```
Enable thinking → Set budget to 20k tokens → Ask complex security question
```

### 3. **File and Image Uploads** 📎

Upload files and images directly to your chat:

#### Supported File Types:
- **Images**: PNG, JPG, JPEG, GIF, WEBP
- **Text Files**: TXT, JSON, CSV, MD
- **Multiple files**: Upload several files at once

#### How to Use:
1. Click the "Attach" button in the chat input area
2. Select one or more files from your computer
3. Images appear as thumbnails in the preview area
4. Text files are automatically inserted into your message
5. Send your message with the attached files

#### Backend Processing:
- Images are encoded as base64 and sent as content blocks
- Text files are decoded and inserted as text
- All uploads are validated and processed securely

### 4. **Agent Selection** 🤖

Choose specialized AI agents for different tasks:

- **SOC Triage Agent**: For initial alert triage and classification
- **Security Analyst Agent**: For deep security analysis
- **Incident Responder Agent**: For incident response workflows
- **Threat Hunter Agent**: For proactive threat hunting
- **Custom Agents**: Configure your own agents with specific prompts

Agents come with pre-configured:
- System prompts
- Token limits
- Thinking settings
- Specialized knowledge

### 5. **MCP Tools Status** 🔧

Real-time status indicator showing Model Context Protocol tools:

- **Green Chip**: MCP tools are available and running
- **Red Chip**: MCP tools are unavailable or errored
- **Tool Count**: Shows how many MCP tools are active
- **Refresh Button**: Reload MCP status without refreshing the page

MCP tools enable Claude to:
- List and analyze findings
- Create and manage cases
- Query security data sources
- Execute investigative workflows

### 6. **Token Usage Tracking** 📊

Visual indicators for token usage:

- **Token Counter**: Shows estimated tokens used vs. limit
- **Progress Bar**: Visual representation of token usage
- **Color Coding**: 
  - Blue: Normal usage
  - Orange: Approaching limit
  - Red: At or over limit

Token estimation includes:
- All previous messages in conversation
- Current input text
- Attached images (~85 tokens each)
- System prompts

### 7. **Streaming Mode** 🌊

Enable streaming for real-time responses:

- **Toggle**: Enable/disable streaming in settings
- **Benefits**: 
  - See responses as they're generated
  - Better user experience for long responses
  - Early indication of response quality
- **Backend**: Uses Server-Sent Events (SSE) for streaming

### 8. **Tabbed Conversations** 📑

Manage multiple conversations simultaneously:

- **Multiple Tabs**: Create separate chat sessions
- **Tab Management**: Close individual tabs (minimum 1 tab)
- **Independent History**: Each tab maintains its own conversation
- **Context Isolation**: Conversations don't interfere with each other

**Shortcuts:**
- Click "New" to create a new tab
- Click X on tab to close it
- Switch between tabs to access different conversations

### 9. **System Prompts** 📝

Customize Claude's behavior with system prompts:

- **Custom Instructions**: Define how Claude should respond
- **Personality**: Set tone and style preferences
- **Context**: Add domain-specific knowledge
- **Constraints**: Set boundaries and rules

**Example System Prompt:**
```
You are a cybersecurity expert specializing in SOC operations. 
Always provide MITRE ATT&CK technique IDs when relevant.
Format responses with clear sections: Summary, Analysis, Recommendations.
```

### 10. **Conversation Management** 🗂️

Tools to manage your chat history:

- **Clear History**: Remove all messages from current tab
- **Persistent Tabs**: Conversations persist during session
- **Scroll to Bottom**: Auto-scroll to latest messages
- **Message Styling**: 
  - User messages: Right-aligned, blue background
  - Assistant messages: Left-aligned, default background

## Settings Page Integration

The Settings page now includes comprehensive Claude configuration:

### Global Defaults
Set default values that apply to all new conversations:

1. **Default Model**: Choose your preferred Claude model
2. **Max Tokens**: Set default token limit
3. **Extended Thinking**: Enable by default if desired
4. **Thinking Budget**: Set default thinking budget

### API Configuration
- **API Key**: Securely store your Anthropic API key
- **Status**: Visual indicator of API key configuration
- **Validation**: Test connection before saving

## Technical Architecture

### Backend Updates

#### ChatMessage Model
```python
class ContentBlock(BaseModel):
    type: str  # "text" or "image"
    text: Optional[str] = None
    source: Optional[Dict[str, Any]] = None

class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[ContentBlock]]
```

#### New Endpoints
- `POST /claude/upload-file`: Upload files and images
- `POST /claude/chat/stream`: Streaming chat responses
- `GET /claude/models`: Get available models

### Frontend Components

#### Enhanced ClaudeDrawer
- Material-UI components for modern, responsive design
- State management for all chat settings
- Real-time token estimation
- Dynamic file upload handling
- MCP status integration

#### API Service Updates
- Support for content blocks
- File upload with multipart/form-data
- Streaming response handling
- Comprehensive type definitions

## Usage Examples

### Example 1: Security Analysis with Thinking

1. Open Claude chat drawer
2. Click settings gear icon
3. Enable "Extended Thinking"
4. Set budget to 20k tokens
5. Select "Security Analyst" agent
6. Ask: "Analyze this suspicious login pattern and correlate with MITRE ATT&CK techniques"
7. Claude will use extended thinking to provide deep analysis

### Example 2: Image Analysis

1. Click "Attach" button
2. Select a screenshot of security logs
3. Type: "What anomalies do you see in these logs?"
4. Send message
5. Claude will analyze the image and provide insights

### Example 3: Multi-Tab Investigation

1. Create Tab 1 for initial triage
2. Create Tab 2 for malware analysis
3. Create Tab 3 for timeline reconstruction
4. Switch between tabs as investigation progresses
5. Each tab maintains independent context

### Example 4: Custom Agent with System Prompt

1. In settings, add system prompt:
   ```
   You are a threat hunting expert. Focus on IOCs, 
   TTPs, and provide actionable detection rules.
   ```
2. Set model to Claude 4.5 Sonnet
3. Set max tokens to 8192
4. Save configuration
5. Use for threat hunting conversations

## Performance Considerations

### Token Estimation
- Rough estimation: ~4 characters per token
- Images: ~85 tokens each
- Actual usage may vary based on content

### File Size Limits
- Images: Recommended < 5MB
- Text files: Recommended < 1MB
- Backend enforces reasonable limits

### Streaming Benefits
- Reduced perceived latency
- Better UX for long responses
- Early error detection

## Troubleshooting

### MCP Tools Not Available
1. Check MCP servers are running
2. Click refresh button
3. Verify mcp-config.json is correct
4. Check backend logs for errors

### File Upload Fails
1. Check file type is supported
2. Verify file size is reasonable
3. Check network connection
4. Review browser console for errors

### Token Limit Exceeded
1. Clear conversation history
2. Increase max tokens in settings
3. Use a smaller model
4. Reduce image attachments

### Thinking Mode Not Working
1. Verify thinking is enabled
2. Check thinking budget is set
3. Confirm model supports thinking
4. Review API response for errors

## Best Practices

### Token Management
- Monitor token usage with progress bar
- Clear history when approaching limits
- Use appropriate max tokens for task
- Consider model size vs. task complexity

### Extended Thinking
- Use for complex analysis only
- Set appropriate budget (10k-30k typical)
- Not needed for simple queries
- Monitor response time

### File Uploads
- Compress large images before uploading
- Use text files for structured data
- Batch related files together
- Remove files after sending if not needed

### Agent Selection
- Choose agent based on task type
- Use custom system prompts for specialized tasks
- Test agent responses before production use
- Document agent configurations

### Multi-Tab Usage
- One tab per investigation thread
- Name tabs descriptively
- Close unused tabs to reduce clutter
- Consider conversation context boundaries

## Feature Comparison: Old UI vs New UI

| Feature | Old UI (PyQt) | New UI (React) | Status |
|---------|---------------|----------------|---------|
| Extended Thinking | ✅ | ✅ | ✅ Complete |
| Thinking Budget | ✅ | ✅ | ✅ Complete |
| Image Upload | ✅ | ✅ | ✅ Complete |
| File Upload | ✅ | ✅ | ✅ Complete |
| Model Selection | ✅ | ✅ | ✅ Complete |
| Max Tokens | ✅ | ✅ | ✅ Complete |
| Streaming | ✅ | ✅ | ✅ Complete |
| Agent Selector | ✅ | ✅ | ✅ Complete |
| MCP Status | ✅ | ✅ | ✅ Complete |
| Token Counter | ✅ | ✅ | ✅ Complete |
| Clear History | ✅ | ✅ | ✅ Complete |
| Tabbed Chats | ✅ | ✅ | ✅ Complete |
| System Prompts | ✅ | ✅ | ✅ Complete |
| Settings Panel | ✅ | ✅ | ✅ Complete |

## Migration from Old UI

If you were using the old PyQt UI, here's what you need to know:

### Settings Migration
- API keys are stored in the same location
- Settings will be automatically loaded
- No manual migration required

### Feature Location Changes
- **Old**: Separate widgets for each feature
- **New**: Unified settings panel (click gear icon)
- **Old**: Dock-based layout
- **New**: Drawer-based layout

### Keyboard Shortcuts
- **Send Message**: Enter (both UIs)
- **New Line**: Shift+Enter (both UIs)
- **Focus Input**: Same behavior

### Data Persistence
- Conversation history: Session-only (both UIs)
- Settings: Persistent (both UIs)
- API keys: Securely stored (both UIs)

## Conclusion

Your new React UI now has **complete feature parity** with the old PyQt UI, plus additional benefits:

✅ Modern, responsive design  
✅ Better mobile support  
✅ Improved performance  
✅ Easier to extend and maintain  
✅ Better error handling  
✅ More intuitive UI/UX  

All the same powerful features you had before, now in a modern web interface!

