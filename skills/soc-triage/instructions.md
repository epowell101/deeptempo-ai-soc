# SOC Triage - Detailed Instructions

This document provides detailed instructions for the SOC Triage skill.

## Understanding DeepTempo Findings

### What is a Finding?

A finding represents a behavioral observation from DeepTempo's LogLM. Each finding contains:

1. **Embedding**: A 768-dimensional vector capturing the semantic meaning of the behavior
2. **Anomaly Score**: How unusual this behavior is compared to baseline (0-1)
3. **MITRE Predictions**: Predicted ATT&CK techniques with confidence scores
4. **Entity Context**: Who/what was involved (IPs, hosts, users)
5. **Evidence Links**: Pointers to the underlying log data

### Interpreting Anomaly Scores

| Score Range | Interpretation |
|-------------|----------------|
| 0.9 - 1.0 | Extremely unusual, high priority |
| 0.7 - 0.9 | Significantly anomalous, investigate |
| 0.5 - 0.7 | Moderately unusual, review if time permits |
| 0.3 - 0.5 | Slightly unusual, likely benign |
| 0.0 - 0.3 | Normal behavior |

### Interpreting MITRE Predictions

The LogLM classifier predicts MITRE ATT&CK techniques based on behavioral patterns:

- **>0.8 confidence**: Strong match to known technique patterns
- **0.6-0.8 confidence**: Moderate match, consider alternatives
- **0.4-0.6 confidence**: Weak match, use as hypothesis only
- **<0.4 confidence**: Low confidence, don't emphasize

## Triage Workflow

### Phase 1: Initial Assessment

```
1. Retrieve the finding
2. Note the anomaly score and severity
3. Identify the data source (flow/dns/waf)
4. Review entity context
```

**Questions to answer**:
- Is this a critical asset?
- Is the anomaly score significant?
- What data source generated this finding?

### Phase 2: Context Gathering

```
1. Get nearest neighbors (k=10)
2. Analyze neighbor distribution
3. Check for temporal clustering
4. Identify common entities
```

**Questions to answer**:
- Are similar behaviors seen elsewhere?
- Is this part of a larger pattern?
- When did similar behaviors occur?

### Phase 3: MITRE Analysis

```
1. List all predicted techniques
2. Research technique descriptions
3. Map to tactics
4. Assess technique plausibility
```

**Questions to answer**:
- Do the techniques make sense for this behavior?
- What attack stage does this represent?
- Are there technique combinations suggesting a chain?

### Phase 4: Synthesis

```
1. Combine all observations
2. Form a hypothesis
3. Assess confidence
4. Identify gaps
```

**Questions to answer**:
- What's the most likely explanation?
- How confident are we?
- What would change our assessment?

### Phase 5: Recommendations

```
1. Prioritize by urgency
2. Be specific and actionable
3. Include investigation steps
4. Note escalation criteria
```

**Questions to answer**:
- What should happen immediately?
- What investigation is needed?
- When should this escalate?

## Common Patterns

### Pattern: C2 Beaconing

**Indicators**:
- Regular timing intervals
- Consistent destination
- Small, regular data transfers
- T1071.001 or T1571 predictions

**Triage Focus**:
- Destination IP/domain reputation
- Beacon interval analysis
- Data volume assessment
- Host compromise indicators

### Pattern: Data Exfiltration

**Indicators**:
- Large outbound transfers
- Unusual destinations
- Off-hours activity
- T1048 predictions

**Triage Focus**:
- Data volume quantification
- Destination analysis
- User context
- Data sensitivity assessment

### Pattern: Lateral Movement

**Indicators**:
- Internal-to-internal traffic
- Authentication patterns
- Multiple host involvement
- T1021 predictions

**Triage Focus**:
- Source host assessment
- Target host criticality
- Credential usage
- Movement timeline

### Pattern: DNS Anomalies

**Indicators**:
- Unusual query patterns
- High entropy domains
- Tunneling signatures
- T1071.004 predictions

**Triage Focus**:
- Domain analysis
- Query frequency
- Response patterns
- Baseline comparison

## Writing Effective Summaries

### Executive Summary Structure

```
[What] was detected [when] involving [who/what].
The behavior is [significant/concerning] because [reason].
[Confidence level] confidence based on [evidence].
Recommended priority: [level].
```

### Example Executive Summaries

**High Severity**:
> A high-confidence C2 beaconing pattern was detected on 2024-01-15 from workstation-042 (10.0.1.15) to external IP 203.0.113.50. The behavior exhibits regular 60-second intervals with consistent small payloads, strongly matching MITRE T1071.001 (Web Protocols). High confidence (87%) based on timing regularity and 12 similar findings from the same host. Recommended priority: HIGH - immediate investigation required.

**Medium Severity**:
> Unusual DNS query patterns were observed from server-db-01 on 2024-01-15, with queries to high-entropy subdomains of example-cdn.com. The pattern partially matches DNS tunneling (T1071.004) but could also indicate legitimate CDN usage. Medium confidence (62%) due to ambiguous domain reputation. Recommended priority: MEDIUM - investigate within 24 hours.

**Low Severity**:
> Slightly elevated outbound traffic was detected from laptop-sales-03 to cloud storage provider. The anomaly score (0.45) is below typical investigation threshold, and the destination is a known business application. Low confidence of malicious activity. Recommended priority: LOW - log for baseline adjustment.

## Quality Checklist

Before finalizing the triage report:

- [ ] Executive summary is one paragraph
- [ ] All MITRE techniques include tactic context
- [ ] Anomaly score is interpreted, not just stated
- [ ] Similar findings are summarized meaningfully
- [ ] Recommendations are specific and prioritized
- [ ] Confidence level is stated with reasoning
- [ ] Human review disclaimer is included
- [ ] No raw PII in output
