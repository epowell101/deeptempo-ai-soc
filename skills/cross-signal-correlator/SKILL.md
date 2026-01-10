---
name: cross-signal-correlator
description: Corroborate findings across multiple data sources (Flow, DNS, WAF) to build a comprehensive view of suspicious activity and strengthen or weaken threat hypotheses
version: 1.0.0
author: DeepTempo
tags:
  - soc
  - correlation
  - investigation
  - multi-source
requires:
  - mcp/deeptempo-findings-server
---

# Cross-Signal Correlator

Correlate findings across Flow, DNS, and WAF data sources to build comprehensive threat narratives.

## When to Use

Use this skill when:
- A finding from one data source needs corroboration
- Building a complete picture of an incident
- Validating or refuting a threat hypothesis
- Investigating multi-stage attacks

## Prerequisites

- Access to the DeepTempo Findings Server MCP
- An anchor finding to correlate from
- Understanding of how different data sources relate

## Data Source Relationships

### Flow → DNS Correlation

| Flow Observation | Look for in DNS |
|------------------|-----------------|
| Connection to external IP | DNS query resolving to that IP |
| Periodic beaconing | Regular DNS queries to same domain |
| Large data transfer | DNS tunneling indicators |

### Flow → WAF Correlation

| Flow Observation | Look for in WAF |
|------------------|-----------------|
| Inbound connection | Corresponding HTTP request |
| Attack source IP | Blocked/allowed requests from IP |
| Data exfiltration | Upload attempts to external |

### DNS → Flow Correlation

| DNS Observation | Look for in Flow |
|-----------------|------------------|
| Suspicious domain query | Connection to resolved IP |
| High query frequency | Corresponding traffic volume |
| DGA-like domains | Beaconing patterns |

### DNS → WAF Correlation

| DNS Observation | Look for in WAF |
|-----------------|------------------|
| Domain resolution | HTTP requests to domain |
| CDN/cloud domains | API calls, data uploads |

## Instructions

### Step 1: Establish the Anchor

Start with your primary finding:

```
get_finding(finding_id="<anchor_finding_id>")
```

Document:
- Data source (flow/dns/waf)
- Key entities (IPs, domains, hosts)
- Time window of interest
- Initial hypothesis

### Step 2: Identify Correlation Targets

Based on the anchor, determine what to look for:

**If anchor is Flow**:
- DNS queries from same source IP
- WAF requests to same destination
- DNS resolutions to destination IP

**If anchor is DNS**:
- Flow connections to resolved IPs
- WAF requests to queried domain
- Other DNS queries from same host

**If anchor is WAF**:
- Flow connections from attacker IP
- DNS queries for target domain
- Related WAF events (same attack)

### Step 3: Search for Corroborating Findings

Use nearest neighbors with source filters:

```
# Find related DNS findings
nearest_neighbors(
    query="<anchor_id>",
    k=20,
    filters={"data_source": "dns"}
)

# Find related Flow findings
nearest_neighbors(
    query="<anchor_id>",
    k=20,
    filters={"data_source": "flow"}
)

# Find related WAF findings
nearest_neighbors(
    query="<anchor_id>",
    k=20,
    filters={"data_source": "waf"}
)
```

### Step 4: Entity-Based Correlation

Search for findings sharing key entities:

```
# Findings with same source IP
list_findings(filters={"entity_context.src_ip": "<ip>"})

# Findings with same destination
list_findings(filters={"entity_context.dst_ip": "<ip>"})

# Findings from same host
list_findings(filters={"entity_context.hostname": "<host>"})
```

### Step 5: Build the Timeline

Order all correlated findings chronologically:

1. Collect all relevant findings
2. Sort by timestamp
3. Identify the sequence of events
4. Note gaps or inconsistencies

### Step 6: Assess Correlation Strength

Evaluate how well findings corroborate each other:

| Correlation Type | Strength |
|------------------|----------|
| Same entity, same time, complementary data | Strong |
| Same entity, close time, related behavior | Moderate |
| Related entity, same time, similar behavior | Weak |
| Different entity, different time | None |

### Step 7: Generate Correlation Report

Document findings following the output format.

## Output Format

```markdown
# Cross-Signal Correlation Report

**Anchor Finding**: [Finding ID]
**Correlation Timestamp**: [Current Time]
**Status**: Requires Human Review

## Anchor Summary

| Attribute | Value |
|-----------|-------|
| Finding ID | [ID] |
| Data Source | [source] |
| Timestamp | [time] |
| Key Entity | [entity] |
| Initial Hypothesis | [hypothesis] |

## Correlation Search

### Search Parameters
- Time Window: [start] to [end]
- Entity Focus: [entities]
- Data Sources Searched: Flow, DNS, WAF

### Findings by Source

| Source | Findings Found | Relevant | Corroborating |
|--------|----------------|----------|---------------|
| Flow | [n] | [n] | [n] |
| DNS | [n] | [n] | [n] |
| WAF | [n] | [n] | [n] |

## Correlated Findings

### Flow Findings
| Finding ID | Time | Relevance | Key Observation |
|------------|------|-----------|-----------------|
| [ID] | [time] | [High/Med/Low] | [observation] |

### DNS Findings
| Finding ID | Time | Relevance | Key Observation |
|------------|------|-----------|-----------------|
| [ID] | [time] | [High/Med/Low] | [observation] |

### WAF Findings
| Finding ID | Time | Relevance | Key Observation |
|------------|------|-----------|-----------------|
| [ID] | [time] | [High/Med/Low] | [observation] |

## Timeline Reconstruction

```
[Time 1] [Source] - [Event description]
[Time 2] [Source] - [Event description]
[Time 3] [Source] - [Event description]
...
```

## Correlation Analysis

### Supporting Evidence
[What findings support the hypothesis]

### Contradicting Evidence
[What findings contradict or complicate the hypothesis]

### Gaps
[What data is missing that would help]

## Hypothesis Assessment

### Original Hypothesis
[State the initial hypothesis]

### Updated Assessment
[Strengthened/Weakened/Unchanged]

### Reasoning
[Explain why based on correlated evidence]

### Confidence Level
[High/Medium/Low] based on:
- Correlation strength: [assessment]
- Evidence completeness: [assessment]
- Alternative explanations: [assessment]

## Recommended Actions

### If Hypothesis Confirmed
1. [Action]
2. [Action]

### If Hypothesis Refuted
1. [Action]
2. [Action]

### Additional Investigation Needed
1. [What to investigate]
2. [What data to gather]

---
*This report was generated by Claude using the Cross-Signal Correlator skill.*
*All conclusions require human validation.*
```

## Examples

### Example 1: C2 Corroboration

**Anchor**: Flow finding showing periodic beaconing
**Correlation Goal**: Confirm C2 with DNS evidence

**Expected Correlations**:
- DNS queries to beacon destination domain
- Query timing matching beacon intervals
- Possibly DGA-like domain patterns

### Example 2: Data Exfiltration Investigation

**Anchor**: WAF finding showing large POST to external
**Correlation Goal**: Understand data source and method

**Expected Correlations**:
- Flow showing data transfer volume
- DNS resolution of upload destination
- Prior reconnaissance activity

## Guidelines

1. **Start with clear hypothesis** - Know what you're trying to prove/disprove
2. **Cast a wide net initially** - Don't filter too aggressively at first
3. **Time alignment matters** - Correlated events should be temporally close
4. **Entity consistency** - Look for shared entities across sources
5. **Document negative results** - Absence of correlation is also informative
6. **Consider alternative explanations** - Don't force-fit evidence

## Constraints

- **Do not over-interpret** weak correlations
- **Acknowledge gaps** in available data
- **Note confidence levels** for all conclusions
- **Require human review** before acting on correlations
- **Consider benign explanations** for correlated activity
