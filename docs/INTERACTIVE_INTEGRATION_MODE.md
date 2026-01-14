# Interactive Integration Builder Mode

## Overview

The Custom Integration Builder now supports **interactive mode**, where Claude can ask you questions during the generation process to clarify unclear documentation and ensure a better integration.

## How It Works

### Traditional Mode (Automatic)
1. You provide documentation
2. Claude analyzes it
3. Integration is generated immediately

### Interactive Mode (With Questions)
1. You provide documentation
2. Claude analyzes it and **asks clarifying questions**
3. You answer the questions
4. Claude generates the integration with your guidance

## When Does Interactive Mode Activate?

Claude will automatically enter interactive mode when:
- 🔍 Documentation is unclear or incomplete
- ❓ Multiple interpretation options exist
- 🎯 Endpoint prioritization is needed
- 🔐 Authentication details are ambiguous
- 📊 Response format needs clarification

## Example Flow

### Step 1: Provide Documentation
```
You paste API documentation for "SecurityHub API"
Click "Generate"
```

### Step 2: Claude Asks Questions
```
Claude: "I have some questions:

1. Which endpoints should I prioritize for the integration?
   - GET /alerts
   - GET /incidents
   - POST /alerts/acknowledge
   - All of the above?

2. The authentication section mentions both API keys and OAuth.
   Which method should the integration use?

3. Should I include rate limiting handling? I see mentions
   of rate limits but no specific values documented."
```

### Step 3: You Answer
```
You respond: "Prioritize GET /alerts and POST /alerts/acknowledge.
Use API key authentication with the X-API-Key header.
Yes, include rate limiting - use 100 requests per minute as
mentioned in the overview section."

Click "Send Answer"
```

### Step 4: Claude Generates
```
Claude processes your answers and generates a complete integration
with exactly the features and configuration you specified.
```

## UI Experience

### Question Display

When Claude asks questions, you'll see:

```
┌─────────────────────────────────────────────┐
│  ℹ️  Claude needs more information          │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ AI │ I have some questions:          │ │
│  │    │                                 │ │
│  │    │ 1. Which endpoints...          │ │
│  │    │ 2. Authentication method...    │ │
│  │    │ 3. Should I include...         │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  Your Answer:                               │
│  ┌───────────────────────────────────────┐ │
│  │ Type your answer here...              │ │
│  │                                       │ │
│  │                                       │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  [Send Answer]                              │
└─────────────────────────────────────────────┘
```

### Benefits

✅ **Better Quality**: Clarifications lead to more accurate integrations
✅ **No Assumptions**: Claude asks instead of guessing
✅ **Customization**: You control what gets prioritized
✅ **Learning**: See what information is important for integrations

## Tips for Answering Questions

### Be Specific
❌ "Use the first method"
✅ "Use API key authentication with the X-API-Key header"

### Provide Context
❌ "Yes"
✅ "Yes, implement all CRUD operations for alerts - create, read, update, delete"

### Reference Documentation
❌ "Check the docs"
✅ "The authentication section on page 3 shows Bearer token format: 'Bearer {token}'"

### Prioritize When Asked
❌ "Everything is important"
✅ "Focus on: 1) Getting alerts, 2) Acknowledging alerts, 3) Adding comments. Skip the reporting endpoints for now."

## Common Questions Claude Might Ask

### 1. Endpoint Prioritization
```
"Your API has 15 endpoints. Which ones are most important
for security operations?"
```

**Good Answer:**
"Prioritize: search_threats, get_threat_details, and check_ioc.
These are the core SOC use cases. Skip the admin and reporting
endpoints."

### 2. Authentication Clarification
```
"The docs mention both API keys (section 2) and OAuth (section 5).
Which should the integration use?"
```

**Good Answer:**
"Use API key authentication. OAuth is only for the web UI.
The API key should be passed in the Authorization header as
'ApiKey {your-key}'."

### 3. Parameter Understanding
```
"The 'severity' parameter is mentioned but not documented.
What are the valid values?"
```

**Good Answer:**
"Valid values are: low, medium, high, critical.
These are case-sensitive lowercase strings.
Default should be 'medium' if not specified."

### 4. Error Handling
```
"How should the integration handle rate limiting?
Are there specific error codes to watch for?"
```

**Good Answer:**
"Rate limit is 1000 requests/hour. When exceeded, the API
returns HTTP 429 with a 'Retry-After' header.
The integration should respect that header and retry."

### 5. Response Format
```
"The sample responses show different formats.
Which is the current API version?"
```

**Good Answer:**
"Use the format from Example 2. That's for API v2 which
is current. Ignore the v1 examples (Example 1 and 3)."

## Multiple Rounds of Questions

Claude might ask follow-up questions:

```
Round 1:
Claude: "Which endpoints to prioritize?"
You: "Focus on alerts and incidents"

Round 2:
Claude: "For alerts, should I include the bulk operations
(bulk_acknowledge, bulk_resolve) or just single operations?"
You: "Include both single and bulk operations"

Final:
Claude generates integration with your complete specifications
```

## Disabling Interactive Mode

If you prefer Claude to generate without asking questions:

**Option 1: Provide Complete Documentation**
- Include all endpoint details
- Clear authentication instructions
- Parameter descriptions with types
- Response format examples

**Option 2: Add Instructions**
```
In your documentation, add:

"AUTO-GENERATE: Generate integration for all documented
endpoints using API key authentication. No questions needed."
```

## Troubleshooting

### Claude Keeps Asking Questions
**Issue**: Too many rounds of questions

**Solution**: 
- Provide more detailed documentation upfront
- Answer all questions in one response
- Add examples to your documentation

### Claude Doesn't Ask Questions When It Should
**Issue**: Documentation is unclear but Claude doesn't ask

**Solution**:
- Explicitly note: "Please ask if anything is unclear"
- Make your documentation more sparse (less detail forces questions)
- Use the feedback to improve the prompt

### Can't Progress Past Questions
**Issue**: Stuck in question loop

**Solution**:
- Provide complete answers to all questions at once
- Reference specific sections from your documentation
- Use "Skip this question, use your best judgment" for non-critical items

## Examples

### Example 1: Good Interactive Session

**Initial Doc:**
```
ThreatAPI v2
GET /threats - Returns threats
POST /threats/{id}/resolve - Resolves a threat
Auth: Header required
```

**Claude Questions:**
```
I have some questions:
1. What authentication header format?
2. What are the required/optional parameters for GET /threats?
3. What's the response format?
```

**Your Answer:**
```
1. Use Authorization: Bearer {token}
2. Required: none. Optional: severity (string), limit (int 1-100)
3. Returns: {"threats": [...], "total": N}
```

**Result:** ✅ Complete integration generated

### Example 2: Poor Interactive Session

**Claude Questions:**
```
I have some questions:
1. What authentication header format?
2. What are the parameters?
```

**Your Answer:**
```
Use the standard format. Parameters are in the docs.
```

**Result:** ❌ Claude has to ask again or makes assumptions

## Best Practices

1. **Read Questions Carefully**: Claude asks specific questions for a reason
2. **Answer Completely**: Cover all parts of multi-part questions
3. **Be Patient**: Interactive mode takes longer but produces better results
4. **Provide Examples**: When explaining formats, give concrete examples
5. **Save Time Long-term**: Better integrations = less manual editing later

## Technical Details

### How It Works

1. **Detection**: Service checks if Claude's response contains question indicators
2. **Conversation State**: Maintains message history between rounds
3. **Context Preservation**: All previous Q&A is included in subsequent requests
4. **Automatic Transition**: Switches to generation when ready

### API Changes

**Request Format:**
```json
{
  "documentation": "...",
  "integration_name": "My Tool",
  "category": "Threat Intelligence",
  "conversation_history": [...],  // Added for interactive mode
  "user_response": "..."           // Added for follow-up answers
}
```

**Response Format (With Questions):**
```json
{
  "success": true,
  "needs_clarification": true,
  "message": "I have some questions: ...",
  "conversation_history": [...]
}
```

**Response Format (Ready):**
```json
{
  "success": true,
  "needs_clarification": false,
  "integration_id": "custom-my-tool",
  "metadata": {...},
  "server_code": "..."
}
```

## Feedback

The interactive mode is designed to be:
- ⚡ **Fast**: Questions answered in seconds
- 🎯 **Focused**: Only asks when necessary
- 💬 **Natural**: Conversational style
- 🔄 **Iterative**: Multiple rounds if needed

If you have suggestions for improvement, let us know!

---

**Pro Tip**: Save your best Q&A sessions as templates for similar API types!

