# Agent Prompt Improvements

## Overview
This document summarizes the comprehensive improvements made to all 13 SOC agent prompts to ensure proper MCP (Model Context Protocol) tool usage, appropriate thinking patterns, and consistent structure.

## Key Improvements

### 1. MCP Tool Integration
**Problem**: Only 2 out of 13 agents (Triage and Investigator) had proper guidance on using MCP tools.

**Solution**: All agents now include:
- `<recognizing_security_entities>` section explaining how to identify and fetch different entity types
- `<available_tools>` section listing relevant MCP tools with proper `server_tool-name` format
- Clear instructions to ALWAYS use MCP tools to retrieve data before analyzing
- Guidance on using parallel tool calls for efficiency

**Example Pattern**:
```
<recognizing_security_entities>
When analyzing entities, ALWAYS use the appropriate MCP tool FIRST:
- Finding IDs: "f-YYYYMMDD-XXXXXXXX" → Use deeptempo-findings_get_finding
- Case IDs: "case-YYYYMMDD-XXXXXXXX" → Use deeptempo-findings_get_case
- IP addresses: X.X.X.X → Use IP geolocation or threat intel tools
- NEVER access findings or cases as files - use MCP tools
</recognizing_security_entities>
```

### 2. Thinking Patterns
**Problem**: Agents with `enable_thinking=True` lacked structured guidance on when to use extended thinking.

**Solution**: All thinking-enabled agents now include a `<thinking_approach>` section explaining when to use extended thinking.

**Agents with Thinking Enabled** (9 agents):
- Investigator (max_tokens: 16384)
- Threat Hunter (max_tokens: 16384)
- Correlator (max_tokens: 16384)
- MITRE Analyst (max_tokens: 16384)
- Forensics (max_tokens: 16384)
- Threat Intel (max_tokens: 16384)
- Malware Analyst (max_tokens: 16384)
- Network Analyst (max_tokens: 16384)
- Auto Responder (max_tokens: 16384)

**Agents with Thinking Disabled** (4 agents):
- Triage (max_tokens: 2048) - Needs rapid responses
- Responder (max_tokens: 4096) - Speed-critical incident response
- Reporter (max_tokens: 8192) - Communication focus
- Compliance (max_tokens: 4096) - Straightforward checklists

**Rationale**: Thinking is enabled for agents that need deep analysis, correlation, or complex reasoning. It's disabled for agents that prioritize speed or straightforward tasks.

### 3. Consistent Structure
All agent prompts now follow a consistent structure:

1. **Introduction**: Role and platform context
2. **`<recognizing_security_entities>`**: How to identify and fetch entities
3. **`<methodology>`**: Step-by-step approach with MCP tool usage
4. **`<available_tools>`**: Relevant MCP tools with naming conventions
5. **`<thinking_approach>`** (for thinking-enabled agents): When to use extended thinking
6. **`<principles>`**: Core operating principles

### 4. Recommended Tools Lists
**Problem**: `recommended_tools` lists used generic names without server prefixes.

**Solution**: Updated all `recommended_tools` lists to use proper MCP tool naming format:
- `deeptempo-findings_get_finding` (not just `get_finding`)
- `timesketch_search_timesketch` (not just `search_timesketch`)
- `attack-layer_create_attack_layer` (not just `create_attack_layer`)
- `approval_create_approval_action` (not just `create_approval_action`)

### 5. Parallel Tool Calls
All agents now include guidance on using parallel tool calls when:
- Retrieving multiple findings
- Enriching multiple IOCs
- Querying multiple log sources
- Analyzing multiple entities simultaneously

## Agent-Specific Improvements

### Triage Agent
- Already had good MCP tool guidance
- Kept concise for rapid assessment
- Focuses on speed and decisiveness

### Investigator Agent
- Already had comprehensive MCP tool guidance
- Thinking enabled for deep analysis
- Structured investigation methodology

### Threat Hunter Agent
- Added `<hunting_methodology>` with MCP tool integration
- Added `<thinking_approach>` for complex hunting scenarios
- Emphasized parallel tool calls for multi-source hunting

### Correlator Agent
- Added `<correlation_methodology>` with confidence scoring
- Added guidance on using attack-layer tools for MITRE visualization
- Added `<thinking_approach>` for weak signal correlation

### Responder Agent
- Added `<response_methodology>` following NIST framework
- Added `<containment_action_guidelines>` with confidence scoring
- Kept thinking disabled for rapid response

### Reporter Agent
- Added `<reporting_methodology>` with data gathering steps
- Added guidance on tailoring reports to different audiences
- Emphasized retrieving data before writing

### MITRE Analyst Agent
- Added `<mitre_analysis_methodology>` with kill chain progression
- Added complete MITRE ATT&CK tactics list with descriptions
- Added `<thinking_approach>` for complex attack chain analysis

### Forensics Agent
- Added `<forensic_methodology>` with chain of custody emphasis
- Added `<forensic_analysis_areas>` covering all forensic domains
- Added `<thinking_approach>` for complex forensic scenarios

### Threat Intel Agent
- Added `<threat_intel_methodology>` with IOC enrichment steps
- Added `<intelligence_sources>` covering OSINT, commercial, government
- Added `<thinking_approach>` for threat actor attribution

### Compliance Agent
- Added `<compliance_methodology>` with framework mapping
- Added `<key_frameworks>` covering NIST, ISO, PCI-DSS, HIPAA, GDPR, SOC 2
- Kept thinking disabled for straightforward assessments

### Malware Analyst Agent
- Added comprehensive `<malware_analysis_methodology>` covering static, dynamic, network analysis
- Added `<safety_principles>` emphasizing sandbox usage
- Added `<thinking_approach>` for sophisticated malware analysis

### Network Analyst Agent
- Added `<network_analysis_methodology>` covering flow, protocol, geolocation analysis
- Added `<analysis_areas>` detailing 7 network analysis domains
- Added `<thinking_approach>` for complex C2 and lateral movement detection

### Auto Responder Agent
- Added comprehensive `<automatic_response_workflow>` with confidence scoring
- Added `<confidence_scoring_criteria>` with specific point values
- Added `<safety_checks>` and `<example_workflow>`
- Added `<thinking_approach>` for autonomous response decisions

## Benefits

1. **Consistency**: All agents follow the same structural pattern
2. **Clarity**: Clear instructions on MCP tool usage with proper naming
3. **Efficiency**: Guidance on parallel tool calls reduces latency
4. **Safety**: Proper entity recognition prevents file access errors
5. **Thinking**: Appropriate use of extended thinking for complex tasks
6. **Auditability**: Clear methodologies for transparent decision-making

## Testing Recommendations

1. **MCP Tool Availability**: Verify all referenced MCP tools are available in the deployment
2. **Tool Naming**: Confirm server prefixes match actual MCP server names
3. **Thinking Budget**: Monitor token usage for thinking-enabled agents
4. **Parallel Calls**: Test that parallel tool calls work as expected
5. **Entity Recognition**: Test with various entity types (findings, cases, IPs, hashes)

## Future Enhancements

1. **Dynamic Tool Discovery**: Agents could list available tools at runtime
2. **Skill Libraries**: Add references to specific skill documents for each agent
3. **Confidence Calibration**: Track and calibrate confidence scoring accuracy
4. **Agent Collaboration**: Add guidance on when to hand off to other agents
5. **Performance Metrics**: Add KPIs specific to each agent type

## Conclusion

All 13 agent prompts have been systematically updated to:
- Properly reference MCP servers and tools
- Use appropriate thinking patterns based on agent type
- Follow consistent structural conventions
- Provide clear methodologies and principles

These improvements ensure agents can effectively leverage the full capabilities of the DeepTempo AI SOC platform while maintaining safety, clarity, and efficiency.

