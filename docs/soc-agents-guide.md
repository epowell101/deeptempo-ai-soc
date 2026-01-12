

# SOC AI Agents Guide

## Overview

DeepTempo AI SOC now features **12 specialized AI agents**, each optimized for specific security operations tasks. You can switch between agents during your work, and each agent brings unique expertise and system prompts tailored to their role.

## Available Agents

### 1. 🎯 Triage Agent
**Specialization:** Alert Triage & Prioritization

**Best for:**
- Rapid alert assessment
- Prioritizing incoming findings
- Identifying false positives
- Quick initial categorization

**Capabilities:**
- Fast decision-making
- Severity assessment
- Business impact evaluation
- Escalation recommendations

**When to use:** When you have a queue of alerts and need to quickly determine what needs immediate attention.

---

### 2. 🔍 Investigation Agent
**Specialization:** Deep Security Investigations

**Best for:**
- Thorough incident analysis
- Root cause determination
- Evidence collection
- Timeline reconstruction

**Capabilities:**
- Extended thinking enabled
- Methodical investigation workflows
- Cross-source correlation
- Comprehensive documentation

**When to use:** When you need a deep-dive investigation into a security incident with thorough analysis.

---

### 3. 🎣 Threat Hunter
**Specialization:** Proactive Threat Hunting

**Best for:**
- Searching for hidden threats
- Hypothesis-driven hunting
- Anomaly detection
- APT discovery

**Capabilities:**
- Extended thinking enabled
- Creative query formulation
- Pattern recognition
- Statistical analysis

**When to use:** When proactively searching for threats that may have bypassed automated detection.

---

### 4. 🔗 Correlation Agent
**Specialization:** Signal Correlation & Pattern Analysis

**Best for:**
- Linking related alerts
- Multi-stage attack detection
- Campaign identification
- Entity relationship mapping

**Capabilities:**
- Extended thinking enabled
- Cross-signal analysis
- Temporal correlation
- Attack chain reconstruction

**When to use:** When you have multiple alerts and need to understand how they relate to each other.

---

### 5. 🚨 Response Agent
**Specialization:** Incident Response & Containment

**Best for:**
- Immediate response actions
- Containment recommendations
- Remediation steps
- Impact assessment

**Capabilities:**
- Fast decision-making
- NIST IR framework
- Evidence preservation
- Blast radius assessment

**When to use:** When an incident is confirmed and you need actionable response recommendations.

---

### 6. 📊 Reporting Agent
**Specialization:** Reporting & Communication

**Best for:**
- Executive summaries
- Technical reports
- Metrics and KPIs
- Stakeholder communications

**Capabilities:**
- Clear communication
- Audience-tailored content
- Actionable recommendations
- Business impact focus

**When to use:** When you need to document findings or communicate with stakeholders.

---

### 7. 🎭 MITRE ATT&CK Analyst
**Specialization:** MITRE ATT&CK Analysis

**Best for:**
- Technique identification
- TTP mapping
- Attack flow analysis
- Framework contextualization

**Capabilities:**
- Extended thinking enabled
- Comprehensive ATT&CK knowledge
- Technique ID mapping
- Kill chain analysis

**When to use:** When you need to map observed behaviors to MITRE ATT&CK techniques.

---

### 8. 🔬 Forensics Agent
**Specialization:** Digital Forensics

**Best for:**
- Artifact analysis
- Evidence examination
- Timeline reconstruction
- Chain of custody

**Capabilities:**
- Extended thinking enabled
- Multi-domain forensics
- Meticulous documentation
- Legal awareness

**When to use:** When you need detailed forensic analysis of digital artifacts.

---

### 9. 🌐 Threat Intel Agent
**Specialization:** Threat Intelligence

**Best for:**
- Indicator enrichment
- Actor attribution
- Campaign tracking
- Threat contextualization

**Capabilities:**
- Extended thinking enabled
- OSINT integration
- Geopolitical context
- Predictive analysis

**When to use:** When you need to enrich findings with external threat intelligence.

---

### 10. 📋 Compliance Agent
**Specialization:** Compliance & Policy

**Best for:**
- Policy validation
- Regulatory compliance
- Control assessment
- Audit preparation

**Capabilities:**
- Framework knowledge (NIST, ISO, PCI, HIPAA, etc.)
- Risk assessment
- Compliance reporting
- Control effectiveness

**When to use:** When assessing compliance with security policies or regulations.

---

### 11. 🦠 Malware Analyst
**Specialization:** Malware Analysis

**Best for:**
- Malware identification
- Capability assessment
- IOC extraction
- Family classification

**Capabilities:**
- Extended thinking enabled
- Static and dynamic analysis
- Reverse engineering knowledge
- C2 identification

**When to use:** When analyzing suspicious files or malware samples.

---

### 12. 🌐 Network Analyst
**Specialization:** Network Security Analysis

**Best for:**
- Traffic analysis
- Protocol examination
- Lateral movement detection
- Exfiltration identification

**Capabilities:**
- Extended thinking enabled
- Flow analysis
- Packet inspection
- Anomaly detection

**When to use:** When investigating network-based threats or suspicious traffic patterns.

---

## How to Use Agents

### In the Chat Interface

1. **Select an Agent:**
   - Use the agent dropdown in the chat interface
   - Click the ℹ️ button to see agent details

2. **Switch Agents:**
   - Change agents at any time during your work
   - The chat will show which agent you're talking to
   - Conversation history is preserved when switching

3. **Auto-Select:**
   - Describe what you want to do
   - The system recommends the best agent

### Agent Selection Tips

**For a typical SOC workflow:**

1. **Start with Triage Agent** → Quick assessment of new alerts
2. **Switch to Investigation Agent** → Deep-dive on high-priority items
3. **Use Correlation Agent** → Link related findings
4. **Consult MITRE Analyst** → Map to ATT&CK framework
5. **Engage Response Agent** → Get containment recommendations
6. **Finish with Reporting Agent** → Document and communicate

**For threat hunting:**

1. **Threat Hunter** → Formulate and execute hunts
2. **Network/Forensics Analyst** → Analyze specific artifacts
3. **Threat Intel Agent** → Enrich with external intelligence
4. **Correlation Agent** → Connect the dots

**For compliance:**

1. **Compliance Agent** → Assess policy adherence
2. **Reporting Agent** → Generate compliance reports

## Agent Capabilities Comparison

| Agent | Extended Thinking | Max Tokens | Speed | Specialization |
|-------|------------------|------------|-------|----------------|
| Triage | ❌ | 2K | ⚡⚡⚡ | Fast decisions |
| Investigator | ✅ | 8K | ⚡ | Deep analysis |
| Threat Hunter | ✅ | 6K | ⚡⚡ | Proactive search |
| Correlator | ✅ | 6K | ⚡⚡ | Pattern finding |
| Responder | ❌ | 4K | ⚡⚡⚡ | Quick action |
| Reporter | ❌ | 8K | ⚡⚡ | Communication |
| MITRE Analyst | ✅ | 6K | ⚡⚡ | Framework mapping |
| Forensics | ✅ | 8K | ⚡ | Evidence analysis |
| Threat Intel | ✅ | 6K | ⚡⚡ | Enrichment |
| Compliance | ❌ | 4K | ⚡⚡ | Policy check |
| Malware Analyst | ✅ | 8K | ⚡ | Malware analysis |
| Network Analyst | ✅ | 6K | ⚡⚡ | Traffic analysis |

**Legend:**
- ⚡⚡⚡ = Very Fast (optimized for speed)
- ⚡⚡ = Balanced (speed + depth)
- ⚡ = Thorough (depth over speed)

## System Prompts

Each agent has a specialized system prompt that:
- Defines their role and responsibilities
- Provides methodology and frameworks
- Sets the tone and approach
- Includes domain-specific knowledge

You can view an agent's full system prompt in the agent details panel.

## Best Practices

### 1. Match Agent to Task
Choose the agent whose specialization best matches your current task.

### 2. Switch Agents as Needed
Don't hesitate to switch agents mid-conversation. Each brings different expertise.

### 3. Use Extended Thinking Agents for Complex Tasks
Agents with extended thinking (Investigator, Threat Hunter, etc.) are better for complex analysis.

### 4. Use Fast Agents for Quick Tasks
Triage and Response agents are optimized for speed when you need quick answers.

### 5. Combine Agent Insights
Use multiple agents for different aspects of the same investigation:
- Investigator for facts
- MITRE Analyst for technique mapping
- Responder for actions
- Reporter for documentation

### 6. Leverage Recommended Tools
Each agent has recommended MCP tools that align with their specialization.

## Example Workflows

### Incident Investigation Workflow

```
1. 🎯 Triage Agent: "Assess this alert for severity"
   → Quick prioritization

2. 🔍 Investigation Agent: "Investigate this incident thoroughly"
   → Deep analysis with evidence

3. 🎭 MITRE Analyst: "Map the observed behaviors to ATT&CK"
   → Technique identification

4. 🔗 Correlation Agent: "Find related alerts"
   → Campaign detection

5. 🚨 Response Agent: "Recommend containment steps"
   → Action items

6. 📊 Reporting Agent: "Create executive summary"
   → Documentation
```

### Threat Hunting Workflow

```
1. 🎣 Threat Hunter: "Hunt for signs of ransomware"
   → Hypothesis-driven search

2. 🌐 Network Analyst: "Analyze suspicious network connections"
   → Traffic analysis

3. 🦠 Malware Analyst: "Analyze this suspicious file"
   → Malware assessment

4. 🌐 Threat Intel Agent: "Enrich these IOCs"
   → External intelligence

5. 📊 Reporting Agent: "Document findings"
   → Hunt report
```

### Compliance Audit Workflow

```
1. 📋 Compliance Agent: "Check PCI-DSS compliance status"
   → Policy assessment

2. 🔍 Investigation Agent: "Investigate this policy violation"
   → Deep-dive on issues

3. 📊 Reporting Agent: "Generate compliance report"
   → Audit documentation
```

## Advanced Features

### Auto-Select Agent
The system can recommend an agent based on your query:
- "triage these alerts" → Triage Agent
- "investigate this incident" → Investigation Agent
- "hunt for threats" → Threat Hunter
- "create a report" → Reporting Agent

### Agent Context Awareness
Agents are aware of:
- Available MCP tools
- Your organization's data
- Previous conversation context
- Their own limitations

### Thinking Budget
Agents with extended thinking can use additional tokens for deeper reasoning. This is automatically configured per agent.

## Customization

### Future Enhancements
- Custom agent creation
- Agent personality tuning
- Organization-specific agents
- Team collaboration with agents
- Agent performance metrics

## Troubleshooting

**Agent not responding as expected?**
- Check if you're using the right agent for the task
- Try switching to a more specialized agent
- Verify MCP tools are available

**Need faster responses?**
- Switch to agents without extended thinking (Triage, Response, Compliance)
- Use non-streaming mode

**Need deeper analysis?**
- Switch to agents with extended thinking
- Increase thinking budget in settings

## Summary

The SOC AI Agents system provides:
- ✅ 12 specialized agents for different SOC tasks
- ✅ Easy switching between agents
- ✅ Optimized system prompts per agent
- ✅ Extended thinking for complex analysis
- ✅ Flexible workflows
- ✅ MCP tool integration

Choose the right agent for each task, and let them guide you with their specialized expertise!

