# SOC Agents Quick Reference Card

## Agent Selection Guide

### 🎯 **Triage Agent** - "What needs attention?"
**Use when:** You have multiple alerts to prioritize  
**Speed:** ⚡⚡⚡ Very Fast  
**Ask:** "Prioritize these alerts", "Is this a false positive?", "What's urgent?"

### 🔍 **Investigation Agent** - "What happened?"
**Use when:** Deep-dive investigation needed  
**Speed:** ⚡ Thorough  
**Ask:** "Investigate this incident", "What's the root cause?", "Build a timeline"

### 🎣 **Threat Hunter** - "What are we missing?"
**Use when:** Proactive threat hunting  
**Speed:** ⚡⚡ Balanced  
**Ask:** "Hunt for ransomware", "Find anomalies", "Search for APTs"

### 🔗 **Correlation Agent** - "How are these related?"
**Use when:** Multiple alerts need connecting  
**Speed:** ⚡⚡ Balanced  
**Ask:** "Correlate these findings", "Find patterns", "Link these alerts"

### 🚨 **Response Agent** - "What should we do?"
**Use when:** Need immediate action items  
**Speed:** ⚡⚡⚡ Very Fast  
**Ask:** "How do we contain this?", "What's the response plan?", "Remediation steps?"

### 📊 **Reporting Agent** - "How do we communicate this?"
**Use when:** Need documentation or reports  
**Speed:** ⚡⚡ Balanced  
**Ask:** "Create executive summary", "Write technical report", "Document findings"

### 🎭 **MITRE Analyst** - "What techniques were used?"
**Use when:** Need ATT&CK mapping  
**Speed:** ⚡⚡ Balanced  
**Ask:** "Map to MITRE ATT&CK", "What tactics?", "Identify techniques"

### 🔬 **Forensics Agent** - "What does the evidence show?"
**Use when:** Detailed artifact analysis needed  
**Speed:** ⚡ Thorough  
**Ask:** "Analyze this artifact", "Forensic timeline", "Evidence examination"

### 🌐 **Threat Intel Agent** - "Who is behind this?"
**Use when:** Need threat intelligence context  
**Speed:** ⚡⚡ Balanced  
**Ask:** "Enrich these IOCs", "Who is this actor?", "What's the campaign?"

### 📋 **Compliance Agent** - "Are we compliant?"
**Use when:** Policy or compliance checks  
**Speed:** ⚡⚡ Balanced  
**Ask:** "Check PCI compliance", "Policy violations?", "Audit status?"

### 🦠 **Malware Analyst** - "What does this malware do?"
**Use when:** Analyzing suspicious files  
**Speed:** ⚡ Thorough  
**Ask:** "Analyze this file", "What's the malware family?", "Extract IOCs"

### 🌐 **Network Analyst** - "What's happening on the network?"
**Use when:** Network traffic analysis  
**Speed:** ⚡⚡ Balanced  
**Ask:** "Analyze this traffic", "Lateral movement?", "Data exfiltration?"

---

## Common Workflows

### 🚨 Incident Response
```
🎯 Triage → 🔍 Investigate → 🚨 Respond → 📊 Report
```

### 🔍 Full Investigation
```
🔍 Investigate → 🎭 MITRE → 🔗 Correlate → 🚨 Respond → 📊 Report
```

### 🎣 Threat Hunt
```
🎣 Hunt → 🌐 Network → 🦠 Malware → 🌐 Threat Intel → 📊 Report
```

### 🔬 Forensic Analysis
```
🔬 Forensics → 🦠 Malware → 🌐 Network → 📊 Report
```

### 📋 Compliance Check
```
📋 Compliance → 🔍 Investigate → 📊 Report
```

---

## Speed vs. Depth

**Need Speed? ⚡⚡⚡**
- 🎯 Triage Agent
- 🚨 Response Agent

**Balanced ⚡⚡**
- 🎣 Threat Hunter
- 🔗 Correlation Agent
- 📊 Reporting Agent
- 🎭 MITRE Analyst
- 🌐 Threat Intel Agent
- 📋 Compliance Agent
- 🌐 Network Analyst

**Need Depth? ⚡**
- 🔍 Investigation Agent
- 🔬 Forensics Agent
- 🦠 Malware Analyst

---

## Extended Thinking

**Agents with Extended Thinking** (better for complex analysis):
- 🔍 Investigation Agent
- 🎣 Threat Hunter
- 🔗 Correlation Agent
- 🎭 MITRE Analyst
- 🔬 Forensics Agent
- 🌐 Threat Intel Agent
- 🦠 Malware Analyst
- 🌐 Network Analyst

**Agents without Extended Thinking** (optimized for speed):
- 🎯 Triage Agent
- 🚨 Response Agent
- 📊 Reporting Agent
- 📋 Compliance Agent

---

## Quick Tips

✅ **Match agent to task** - Choose the specialist for your current need  
✅ **Switch freely** - Change agents mid-conversation  
✅ **Use workflows** - Combine multiple agents for complete analysis  
✅ **Start with Triage** - When unsure, start with quick assessment  
✅ **End with Reporter** - Document your findings  

---

## Keyboard Shortcuts

*(Future enhancement)*
- `Ctrl+1` - Triage Agent
- `Ctrl+2` - Investigation Agent
- `Ctrl+3` - Threat Hunter
- `Ctrl+4` - Correlation Agent
- `Ctrl+5` - Response Agent
- `Ctrl+6` - Reporting Agent

---

**Print this card for quick reference!** 📄

