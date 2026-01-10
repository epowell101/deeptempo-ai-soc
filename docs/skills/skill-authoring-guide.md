# Skill Authoring Guide

This guide explains how to create and maintain Claude Skills for the DeepTempo AI SOC.

## What is a Skill?

A **Skill** is a self-contained folder that teaches Claude how to perform a specific SOC task. Skills provide:

- **Instructions**: Step-by-step guidance for completing tasks
- **Context**: Domain knowledge and best practices
- **Examples**: Sample inputs and expected outputs
- **Guardrails**: Safety constraints and validation rules

## Skill Structure

Each skill follows this folder structure:

```
skills/
└── my-skill/
    ├── SKILL.md           # Required: Skill definition
    ├── instructions.md    # Optional: Detailed instructions
    └── evals/             # Optional: Test cases
        ├── golden_cases/
        └── expected_outputs/
```

## SKILL.md Format

The `SKILL.md` file is the entry point for every skill. It uses YAML frontmatter followed by Markdown content.

### Required Fields

```yaml
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---
```

### Optional Fields

```yaml
---
name: my-skill-name
description: A clear description of what this skill does
version: 1.0.0
author: Your Name
tags:
  - soc
  - triage
  - investigation
requires:
  - mcp/deeptempo-findings-server
  - mcp/evidence-snippets-server
---
```

### Content Sections

After the frontmatter, include these sections:

```markdown
# Skill Name

Brief overview of the skill's purpose.

## When to Use

Describe the scenarios when this skill should be invoked.

## Prerequisites

List any required data, permissions, or context.

## Instructions

Step-by-step instructions for Claude to follow.

## Examples

### Example 1: Basic Usage

Input:
```
[Example input]
```

Output:
```
[Expected output]
```

## Guidelines

- Guideline 1
- Guideline 2

## Constraints

- What the skill should NOT do
- Safety boundaries
```

## SOC Skill Best Practices

### 1. Be Specific About Data Sources

```markdown
## Data Sources

This skill works with:
- **Flow findings**: Network traffic patterns
- **DNS findings**: Domain resolution anomalies
- **WAF findings**: Web application attacks

Always specify which data source you're analyzing.
```

### 2. Reference MITRE ATT&CK

```markdown
## MITRE ATT&CK Mapping

When analyzing findings, map observations to MITRE techniques:

| Observation | Likely Technique |
|-------------|-----------------|
| Periodic beaconing | T1071.001 - Web Protocols |
| DNS tunneling | T1071.004 - DNS |
| Encoded payloads | T1027 - Obfuscated Files |
```

### 3. Define Clear Output Formats

```markdown
## Output Format

Generate a triage report with these sections:

### Summary
One paragraph executive summary.

### Key Findings
Bullet list of important observations.

### MITRE Techniques
Table of detected techniques with confidence scores.

### Recommended Actions
Numbered list of next steps.

### Evidence References
Links to supporting findings and evidence.
```

### 4. Include Safety Guardrails

```markdown
## Constraints

- **Never auto-execute** response actions
- **Always recommend** human review for critical decisions
- **Redact PII** in all outputs
- **Cite evidence** for all claims
```

### 5. Handle Uncertainty

```markdown
## Handling Uncertainty

When confidence is low:
1. State the uncertainty explicitly
2. List alternative explanations
3. Recommend additional investigation steps
4. Avoid definitive conclusions
```

## Example: SOC Triage Skill

```yaml
---
name: soc-triage
description: Generate an initial triage report from a finding and its nearest neighbors
version: 1.0.0
tags:
  - soc
  - triage
  - investigation
requires:
  - mcp/deeptempo-findings-server
---

# SOC Triage

Generate a comprehensive triage report for security findings.

## When to Use

Use this skill when:
- A new high-severity finding is detected
- An analyst needs to quickly understand a finding
- Starting a new investigation

## Prerequisites

- Access to the DeepTempo Findings Server
- Finding ID to investigate
- Nearest neighbor context (k=10 recommended)

## Instructions

1. **Retrieve the finding** using `get_finding(finding_id)`

2. **Get similar findings** using `nearest_neighbors(finding_id, k=10)`

3. **Analyze the pattern**:
   - What behavior does the embedding represent?
   - Are the neighbors from the same entity or distributed?
   - What MITRE techniques are predicted?

4. **Assess severity**:
   - Anomaly score significance
   - Technique confidence levels
   - Entity criticality

5. **Generate the report** following the output format

## Output Format

### Triage Report: [Finding ID]

**Generated**: [Timestamp]
**Analyst**: Claude AI (requires human review)

#### Executive Summary
[One paragraph summary of the finding and its significance]

#### Finding Details
| Field | Value |
|-------|-------|
| Finding ID | ... |
| Timestamp | ... |
| Data Source | ... |
| Anomaly Score | ... |
| Severity | ... |

#### Entity Context
[Table of involved entities]

#### MITRE ATT&CK Analysis
| Technique | Name | Confidence | Tactic |
|-----------|------|------------|--------|
| ... | ... | ... | ... |

#### Similar Findings
[Summary of nearest neighbors and patterns]

#### Recommended Actions
1. [Action 1]
2. [Action 2]
3. [Action 3]

#### Evidence References
- [Link to evidence 1]
- [Link to evidence 2]

---
*This report requires human review before action*

## Guidelines

- Always start with the highest confidence MITRE technique
- Group similar findings by entity when possible
- Highlight any critical assets involved
- Note temporal patterns (clustering in time)

## Constraints

- Do not access raw logs without explicit request
- Do not recommend automated response actions
- Always include the "requires human review" disclaimer
- Redact any PII in the output
```

## Testing Skills

### Golden Cases

Create test cases in `evals/golden_cases/`:

```json
{
    "test_id": "triage-001",
    "description": "Basic triage of C2 beaconing finding",
    "input": {
        "finding_id": "f-test-001"
    },
    "expected_sections": [
        "Executive Summary",
        "MITRE ATT&CK Analysis",
        "Recommended Actions"
    ],
    "expected_techniques": ["T1071.001"]
}
```

### Expected Outputs

Store reference outputs in `evals/expected_outputs/`:

```markdown
# Expected Output: triage-001

## Executive Summary
The finding f-test-001 represents a high-confidence detection of 
command and control beaconing activity...
```

## Skill Versioning

Use semantic versioning in the SKILL.md frontmatter:

- **Major**: Breaking changes to output format
- **Minor**: New capabilities, backward compatible
- **Patch**: Bug fixes, documentation updates

```yaml
---
name: soc-triage
version: 1.2.0
---
```

## Integration with MCP

Skills can reference MCP servers they depend on:

```yaml
---
requires:
  - mcp/deeptempo-findings-server
  - mcp/evidence-snippets-server
---
```

This helps Claude understand what tools are available when the skill is active.
