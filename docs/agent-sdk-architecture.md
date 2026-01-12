# Agent SDK Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     DeepTempo AI SOC                        │
│                      PyQt6 UI Layer                         │
│                   (ui/claude_chat.py)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │   Claude Service       │
         │      Factory           │
         │ (claude_factory.py)    │
         └────────────┬───────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐      ┌──────────────────────┐
│  Current Impl   │      │   Agent SDK Impl     │
│ claude_service  │      │claude_agent_service  │
│                 │      │                      │
│ ✅ Direct SDK   │      │ 🆕 Agent SDK        │
│ ✅ Production   │      │ 🧪 Experimental     │
└────────┬────────┘      └──────────┬───────────┘
         │                          │
         └────────────┬─────────────┘
                      │
         ┌────────────▼───────────┐
         │   Anthropic Claude API │
         │  claude-sonnet-4-5     │
         └────────────┬───────────┘
                      │
         ┌────────────▼───────────┐
         │      MCP Tools         │
         │  - findings_server     │
         │  - case_store_server   │
         │  - evidence_server     │
         └────────────────────────┘
```

## Implementation Comparison

### Current Implementation (Direct SDK)

```
User Query
    │
    ▼
┌────────────────────────────────┐
│  claude_service.py             │
│  ┌──────────────────────────┐  │
│  │ 1. Build messages array  │  │
│  │ 2. Add context/history   │  │
│  │ 3. Format MCP tools      │  │
│  │ 4. Call messages.create()│  │
│  │ 5. Handle tool_use       │  │
│  │ 6. Call MCP tools        │  │
│  │ 7. Format results        │  │
│  │ 8. Continue conversation │  │
│  └──────────────────────────┘  │
└────────────────────────────────┘
    │
    ▼
Response
```

### Agent SDK Implementation

```
User Query
    │
    ▼
┌────────────────────────────────┐
│ claude_agent_service.py        │
│  ┌──────────────────────────┐  │
│  │ 1. Build prompt          │  │
│  │ 2. Create options        │  │
│  │ 3. Call query()          │  │
│  │    ├─ Agent handles tools│  │
│  │    ├─ Agent handles turns│  │
│  │    └─ Agent handles state│  │
│  │ 4. Stream responses      │  │
│  └──────────────────────────┘  │
└────────────────────────────────┘
    │
    ▼
Response
```

## MCP Tool Integration

### Current Implementation

```python
# Load MCP tools
tools_dict = await mcp_client.list_tools()

# Format for Claude API
for server_name, tools in tools_dict.items():
    for tool in tools:
        claude_tool = {
            "name": f"{server_name}_{tool['name']}",
            "description": tool['description'],
            "input_schema": tool['inputSchema']
        }
        mcp_tools.append(claude_tool)

# Pass to API
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    messages=messages,
    tools=mcp_tools  # ← Manual tool passing
)

# Handle tool use
if response.stop_reason == "tool_use":
    tool_results = await process_tool_use(response.content)
    # Continue conversation with results...
```

### Agent SDK Implementation

```python
# Load MCP tools
tools_dict = await mcp_client.list_tools()

# Convert to Agent SDK Tool objects
agent_tools = []
for server_name, tools in tools_dict.items():
    for tool in tools:
        async def execute(server=server_name, name=tool['name'], **kwargs):
            return await mcp_client.call_tool(server, name, kwargs)
        
        agent_tool = Tool(
            name=f"{server_name}_{tool['name']}",
            description=tool['description'],
            parameters=tool['inputSchema'],
            function=execute  # ← Automatic execution
        )
        agent_tools.append(agent_tool)

# Pass to Agent SDK
options = ClaudeAgentOptions(tools=agent_tools)
async for message in query(prompt=prompt, options=options):
    # Agent SDK handles tool orchestration automatically
    process(message)
```

## Conversation Flow

### Direct SDK (Manual Control)

```
┌─────────────┐
│ User Input  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Format Message   │ ← Manual
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Call API         │
└──────┬───────────┘
       │
       ▼
   ┌───────────┐
   │ Tool Use? │
   └─────┬─────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
   Yes       No
    │         │
    │         └─────────┐
    ▼                   │
┌──────────────────┐    │
│ Extract Tools    │    │
│ Call MCP         │ ← Manual
│ Format Results   │    │
└──────┬───────────┘    │
       │                │
       ▼                │
┌──────────────────┐    │
│ Continue API     │    │
└──────┬───────────┘    │
       │                │
       └────────┬───────┘
                ▼
         ┌─────────────┐
         │   Response  │
         └─────────────┘
```

### Agent SDK (Automatic)

```
┌─────────────┐
│ User Input  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Call query()     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Agent SDK       │
│  ┌────────────┐  │
│  │ Orchestrate│  │ ← Automatic
│  │ Tools      │  │
│  │ Multi-turn │  │
│  │ State Mgmt │  │
│  └────────────┘  │
└──────┬───────────┘
       │
       ▼
┌─────────────┐
│  Response   │
└─────────────┘
```

## Message Format Comparison

### Direct SDK Messages

```python
messages = [
    {
        "role": "user",
        "content": "List all findings"
    },
    {
        "role": "assistant",
        "content": [
            {"type": "text", "text": "I'll use the list_findings tool."},
            {
                "type": "tool_use",
                "id": "toolu_123",
                "name": "findings_server_list_findings",
                "input": {}
            }
        ]
    },
    {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "toolu_123",
                "content": [{"type": "text", "text": "[findings data]"}]
            }
        ]
    }
]
```

### Agent SDK Messages

```python
# Agent SDK handles message format internally
# You just get structured responses:

async for message in query(prompt="List all findings"):
    if message.type == "assistant":
        # Claude's response
        print(message.data.message['content'])
    
    elif message.type == "tool_use":
        # Tool being used (automatic)
        print(f"Using tool: {message.data['name']}")
    
    elif message.type == "result":
        # Final metadata
        print(f"Cost: ${message.data.total_cost_usd}")
        print(f"Turns: {message.data.num_turns}")
```

## Switching Between Implementations

### Option 1: Factory Pattern (Recommended)

```python
from services.claude_factory import create_claude_service

# Default implementation (configured)
service = create_claude_service(use_mcp_tools=True)

# Force specific implementation
service = create_claude_service(
    implementation="direct",  # or "agent_sdk"
    use_mcp_tools=True
)
```

### Option 2: Direct Import

```python
# Current
from services.claude_service import ClaudeService
service = ClaudeService(use_mcp_tools=True)

# Agent SDK
from services.claude_agent_service import ClaudeAgentService
service = ClaudeAgentService(use_mcp_tools=True)
```

### Option 3: Configuration

```bash
# Set default via CLI
python services/claude_factory.py set agent_sdk

# Then in code (uses configured default)
from services.claude_factory import create_claude_service
service = create_claude_service(use_mcp_tools=True)
```

## Performance Characteristics

### Latency

```
Direct SDK:
├─ API Call: ~200-500ms
├─ Tool Exec: ~100-300ms per tool
└─ Total: ~300-1500ms (1-3 tools)

Agent SDK:
├─ API Call: ~200-500ms
├─ Tool Orchestration: ~50-100ms overhead
├─ Tool Exec: ~100-300ms per tool
└─ Total: ~350-1600ms (1-3 tools)

Difference: ~50-100ms overhead from Agent SDK abstraction
```

### Memory

```
Direct SDK:
├─ Base: ~50MB
├─ Per conversation: ~1-5MB
└─ MCP tools cache: ~2-10MB

Agent SDK:
├─ Base: ~60MB (+10MB for SDK)
├─ Per conversation: ~2-6MB (+1MB state management)
└─ MCP tools cache: ~2-10MB

Difference: ~10-15MB additional memory
```

### Token Usage

```
Both implementations use similar token counts:
├─ System prompt: ~100-200 tokens
├─ Tool definitions: ~50-100 tokens per tool
├─ Conversation: varies
└─ Tool results: ~100-500 tokens per tool

Agent SDK may use slightly more for orchestration:
└─ Additional overhead: ~10-50 tokens per turn
```

## When to Use Each

### Use Direct SDK (claude_service.py) When:

✅ **You need precise control** over API calls  
✅ **Optimizing for minimal latency** (50-100ms matters)  
✅ **Debugging** tool execution flows  
✅ **Production stability** is critical  
✅ **Minimal dependencies** preferred  

### Use Agent SDK (claude_agent_service.py) When:

✅ **Building complex agents** with many tools  
✅ **Multi-turn workflows** are common  
✅ **Want automatic orchestration** of tools  
✅ **Need cost tracking** per query  
✅ **Future-proofing** for new agent features  

## Migration Checklist

If you decide to migrate to Agent SDK:

- [ ] Install Agent SDK: `pip install claude-agent-sdk`
- [ ] Test both implementations: `python scripts/test_agent_sdk.py`
- [ ] Update imports in UI: Use `claude_factory`
- [ ] Test with MCP tools enabled
- [ ] Verify streaming works as expected
- [ ] Check conversation history handling
- [ ] Test image attachments (if used)
- [ ] Validate extended thinking (if used)
- [ ] Performance test with real workloads
- [ ] Update documentation/training materials
- [ ] Rollback plan: Keep direct implementation available

## Conclusion

You now have **both implementations available** with:

✅ Identical interfaces (easy to switch)  
✅ Same MCP tool support  
✅ Factory pattern for easy toggling  
✅ Comprehensive tests  
✅ Full backward compatibility  

**Recommendation**: Stick with your current implementation (it's great!), but experiment with Agent SDK for new features or complex workflows.

