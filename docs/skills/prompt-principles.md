# Prompt Principles for SOC Skills

This document outlines the prompt engineering principles for creating effective SOC skills.

## Core Principles

### 1. Embeddings First, Logs Second

Always prioritize embedding-based analysis over raw log inspection:

```markdown
## Investigation Approach

1. **Start with embeddings**: Use similarity search to find related behavior
2. **Analyze patterns**: Look at clusters and temporal distribution
3. **Review MITRE mappings**: Understand the predicted techniques
4. **Request evidence only when needed**: Raw logs are supplementary
```

### 2. Structured Output

Define clear, consistent output formats:

```markdown
## Output Structure

Always produce output in this format:

### Summary
[Brief executive summary]

### Analysis
[Detailed analysis with evidence]

### Recommendations
[Actionable next steps]

### Confidence
[State confidence level and reasoning]
```

### 3. Explicit Uncertainty

Never overstate confidence:

```markdown
## Confidence Levels

- **High (>80%)**: Multiple corroborating signals, clear pattern
- **Medium (50-80%)**: Some supporting evidence, plausible interpretation
- **Low (<50%)**: Limited evidence, alternative explanations exist

Always state: "Confidence: [Level] because [reasoning]"
```

### 4. Human-in-the-Loop

Always defer critical decisions to humans:

```markdown
## Decision Points

For any action that could:
- Block traffic or users
- Trigger incident response
- Notify external parties
- Modify security controls

State: "Recommended action requires human approval"
```

## SOC-Specific Patterns

### Pattern 1: Triage Narrative

```markdown
## Triage Template

When triaging a finding, follow this narrative structure:

1. **What happened?**
   - Describe the observed behavior
   - Include relevant entity context

2. **Why is it suspicious?**
   - Anomaly score significance
   - MITRE technique implications
   - Deviation from baseline

3. **What else is related?**
   - Similar findings (nearest neighbors)
   - Temporal clustering
   - Entity relationships

4. **What should we do?**
   - Immediate actions
   - Investigation steps
   - Escalation criteria
```

### Pattern 2: Technique Analysis

```markdown
## MITRE Technique Analysis

When analyzing MITRE predictions:

1. **Primary Technique**
   - Technique ID and name
   - Confidence score
   - Tactic context

2. **Supporting Evidence**
   - What in the finding supports this technique?
   - Are there corroborating findings?

3. **Alternative Interpretations**
   - Could this be benign activity?
   - What other techniques might apply?

4. **Detection Gaps**
   - What additional data would help?
   - Are there blind spots?
```

### Pattern 3: Correlation Analysis

```markdown
## Cross-Signal Correlation

When correlating across data sources:

1. **Anchor Finding**
   - Start with the primary finding
   - Note its data source and entities

2. **Related Signals**
   - Search for findings with shared entities
   - Look across flow, DNS, and WAF

3. **Timeline Construction**
   - Order findings chronologically
   - Identify potential attack chain

4. **Synthesis**
   - What story do the signals tell together?
   - Is this more or less suspicious in context?
```

### Pattern 4: Response Recommendation

```markdown
## Response Recommendations

Structure recommendations by urgency:

### Immediate (< 1 hour)
- Containment actions
- Evidence preservation
- Stakeholder notification

### Short-term (< 24 hours)
- Detailed investigation
- Scope assessment
- Additional monitoring

### Long-term (> 24 hours)
- Root cause analysis
- Control improvements
- Process updates
```

## Prompt Templates

### Template 1: Finding Investigation

```markdown
You are investigating finding {finding_id}.

## Context
- Data Source: {data_source}
- Timestamp: {timestamp}
- Anomaly Score: {anomaly_score}

## Entity Information
{entity_context}

## MITRE Predictions
{mitre_predictions}

## Similar Findings
{nearest_neighbors}

## Task
Generate a triage report following the SOC Triage skill format.
Focus on:
1. Understanding the behavioral pattern
2. Assessing the threat level
3. Recommending next steps

Remember: Embeddings first, logs second.
```

### Template 2: Cluster Analysis

```markdown
You are analyzing behavior cluster {cluster_id}.

## Cluster Summary
- Finding Count: {finding_count}
- Time Range: {time_range}
- Top Techniques: {top_techniques}

## Involved Entities
{entities}

## Sample Findings
{sample_findings}

## Task
Characterize this cluster:
1. What behavior does it represent?
2. Is it likely malicious or benign?
3. What investigation is needed?
```

### Template 3: ATT&CK Layer Export

```markdown
You are generating an ATT&CK Navigator layer.

## Time Window
- Start: {start_time}
- End: {end_time}

## Scope
{scope_filters}

## Technique Rollup
{technique_rollup}

## Task
Generate a Navigator layer JSON that:
1. Highlights observed techniques
2. Uses color intensity for confidence
3. Includes finding counts in metadata
4. Adds relevant comments
```

## Anti-Patterns to Avoid

### 1. Log Diving

❌ **Don't**: Immediately request raw logs
✅ **Do**: Start with embedding analysis, request logs only when needed

### 2. Overconfidence

❌ **Don't**: "This is definitely a C2 beacon"
✅ **Do**: "High confidence (85%) C2 beaconing based on periodic timing and MITRE T1071.001 prediction"

### 3. Vague Recommendations

❌ **Don't**: "Investigate further"
✅ **Do**: "Search for DNS queries to suspicious-domain.com from other hosts in the 10.0.1.0/24 subnet"

### 4. Automation Assumptions

❌ **Don't**: "Block the IP address"
✅ **Do**: "Recommend blocking 203.0.113.50 pending human review of business impact"

### 5. Missing Context

❌ **Don't**: Present findings in isolation
✅ **Do**: Always include temporal context, entity relationships, and similar findings

## Quality Checklist

Before finalizing skill output, verify:

- [ ] Executive summary is clear and actionable
- [ ] All claims are supported by evidence
- [ ] Confidence levels are stated explicitly
- [ ] MITRE techniques are properly referenced
- [ ] Recommendations are specific and prioritized
- [ ] Human review requirement is noted
- [ ] PII is redacted
- [ ] Output format is consistent
