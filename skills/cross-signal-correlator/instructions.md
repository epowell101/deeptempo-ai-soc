# Cross-Signal Correlator - Detailed Instructions

## Understanding Multi-Source Correlation

### Why Correlate Across Sources?

Single-source detection has limitations:
- **Flow alone**: Sees traffic but not content or intent
- **DNS alone**: Sees queries but not resulting connections
- **WAF alone**: Sees web attacks but not broader context

Correlation provides:
- **Validation**: Confirm suspicious activity with multiple signals
- **Context**: Understand the full attack chain
- **Confidence**: Reduce false positives through corroboration

### Correlation Principles

1. **Temporal Proximity**: Related events happen close in time
2. **Entity Overlap**: Related events share entities (IPs, hosts, users)
3. **Behavioral Consistency**: Related events show consistent patterns
4. **Logical Sequence**: Events follow expected attack progressions

## Data Source Deep Dive

### Flow Data

**What it captures**:
- Source/destination IPs and ports
- Protocol information
- Byte/packet counts
- Connection timing and duration

**Correlation value**:
- Confirms actual connections occurred
- Quantifies data transfer
- Shows timing patterns

### DNS Data

**What it captures**:
- Query names and types
- Response codes and IPs
- Query timing
- Resolver information

**Correlation value**:
- Reveals intended destinations
- Shows domain-based C2
- Identifies DGA activity

### WAF Data

**What it captures**:
- HTTP methods and URIs
- Request/response details
- Attack signatures
- Block/allow decisions

**Correlation value**:
- Shows attack attempts
- Reveals exploitation methods
- Indicates attacker intent

## Correlation Patterns

### Pattern 1: DNS-to-Flow Chain

```
DNS Query → IP Resolution → Flow Connection

Timeline:
T+0:    DNS query for malicious.com
T+1:    DNS response: 203.0.113.50
T+2:    Flow: Internal → 203.0.113.50:443
```

### Pattern 2: Flow-to-WAF Chain

```
External Connection → Web Request → Attack Attempt

Timeline:
T+0:    Flow: 198.51.100.10 → Internal:443
T+1:    WAF: POST /api/upload from 198.51.100.10
T+2:    WAF: SQL injection detected, blocked
```

### Pattern 3: Full Attack Chain

```
Recon → Initial Access → C2 → Exfiltration

Timeline:
T+0:    DNS: Multiple subdomain queries (recon)
T+1:    WAF: Exploitation attempt
T+2:    Flow: Outbound beacon established
T+3:    DNS: Data exfil domain queries
T+4:    Flow: Large outbound transfer
```

## Correlation Techniques

### Technique 1: IP Pivot

Start with an IP and find all related activity:

```python
# Pseudo-code
anchor_ip = finding.entity_context.dst_ip

# Find DNS queries resolving to this IP
dns_findings = search(response_ip=anchor_ip)

# Find other flows to this IP
flow_findings = search(dst_ip=anchor_ip)

# Find WAF events from this IP
waf_findings = search(src_ip=anchor_ip)
```

### Technique 2: Time Window Correlation

Find all activity in a time window around the anchor:

```python
# Pseudo-code
anchor_time = finding.timestamp
window_start = anchor_time - 5_minutes
window_end = anchor_time + 5_minutes

# Find all findings in window
correlated = search(
    time_range=(window_start, window_end),
    entity=anchor_entity
)
```

### Technique 3: Behavioral Similarity

Use embedding similarity across sources:

```python
# Pseudo-code
anchor_embedding = finding.embedding

# Find similar DNS behaviors
dns_similar = nearest_neighbors(
    anchor_embedding,
    filter={"data_source": "dns"}
)

# Find similar Flow behaviors
flow_similar = nearest_neighbors(
    anchor_embedding,
    filter={"data_source": "flow"}
)
```

## Assessing Correlation Quality

### Strong Correlation Indicators

- Same entity appears in multiple sources
- Events occur within seconds/minutes
- Logical sequence (DNS → Flow → WAF)
- Consistent MITRE technique predictions
- Similar anomaly scores

### Weak Correlation Indicators

- Different entities
- Large time gaps
- No logical connection
- Conflicting technique predictions
- Mixed anomaly scores

### No Correlation Indicators

- No shared entities
- No temporal relationship
- Contradictory evidence
- Different behavioral patterns

## Common Pitfalls

### Pitfall 1: Forced Correlation

**Problem**: Connecting unrelated events because they share one attribute
**Solution**: Require multiple correlation factors

### Pitfall 2: Time Zone Confusion

**Problem**: Misaligning events due to time zone differences
**Solution**: Always use UTC, verify timestamp formats

### Pitfall 3: Entity Ambiguity

**Problem**: NAT, proxies, or shared IPs causing false correlations
**Solution**: Consider network topology, use multiple entity types

### Pitfall 4: Confirmation Bias

**Problem**: Only looking for evidence that supports hypothesis
**Solution**: Actively search for contradicting evidence

## Documentation Template

```markdown
## Correlation Session Log

### Session Info
- Analyst: [name]
- Start Time: [time]
- Anchor Finding: [ID]

### Hypothesis
[Clear statement of what you're trying to prove]

### Search Log
1. [Time] Searched [source] for [criteria]: [results]
2. [Time] Searched [source] for [criteria]: [results]
...

### Correlation Matrix
| Finding | Source | Time | Entity Match | Behavior Match | Strength |
|---------|--------|------|--------------|----------------|----------|
| [ID] | [src] | [t] | [Y/N] | [Y/N] | [S/M/W] |

### Conclusions
[Summary of what correlation revealed]

### Confidence
[High/Medium/Low] because [reasoning]
```
