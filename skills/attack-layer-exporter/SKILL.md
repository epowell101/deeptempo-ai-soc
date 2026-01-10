---
name: attack-layer-exporter
description: Generate MITRE ATT&CK Navigator layer JSON files from DeepTempo findings, enabling visualization of detected techniques across the ATT&CK matrix
version: 1.0.0
author: DeepTempo
tags:
  - soc
  - mitre
  - visualization
  - reporting
requires:
  - mcp/deeptempo-findings-server
---

# ATT&CK Layer Exporter

Generate MITRE ATT&CK Navigator layer JSON files for visualization.

## When to Use

Use this skill when:
- Creating executive reports on threat landscape
- Visualizing technique coverage over time
- Comparing detection capabilities
- Documenting incident scope in ATT&CK terms

## Prerequisites

- Access to the DeepTempo Findings Server MCP
- Understanding of MITRE ATT&CK framework
- ATT&CK Navigator for viewing layers (optional)

## ATT&CK Navigator Overview

The [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/) is a web-based tool for visualizing ATT&CK matrices. It uses JSON layer files to:

- Highlight specific techniques
- Show technique scores/confidence
- Add comments and metadata
- Compare multiple layers

## Instructions

### Step 1: Define the Scope

Determine what findings to include:

```
# Get technique rollup for time window
technique_rollup(
    time_window={
        "start": "2024-01-15T00:00:00Z",
        "end": "2024-01-15T23:59:59Z"
    },
    scope={
        "data_sources": ["flow", "dns", "waf"]
    },
    min_confidence=0.5
)
```

### Step 2: Analyze Technique Distribution

Review the rollup results:
- Which techniques are most prevalent?
- What are the confidence levels?
- Which tactics are represented?

### Step 3: Configure Layer Settings

Decide on visualization options:

| Setting | Options | Recommendation |
|---------|---------|----------------|
| Scoring | Count, Confidence, Combined | Combined |
| Colors | Gradient, Discrete | Gradient |
| Filters | Platforms, Tactics | Based on scope |
| Metadata | Finding counts, Time range | Include both |

### Step 4: Generate the Layer

Use the export tool:

```
export_attack_layer(
    time_window={
        "start": "2024-01-15T00:00:00Z",
        "end": "2024-01-15T23:59:59Z"
    },
    scope={},
    layer_name="DeepTempo Findings - 2024-01-15"
)
```

### Step 5: Review and Refine

Check the generated layer:
- Are technique scores appropriate?
- Are comments informative?
- Is metadata complete?

## Output Format

### Layer JSON Structure

```json
{
    "name": "DeepTempo Findings - [Date Range]",
    "versions": {
        "attack": "14",
        "navigator": "4.9.1",
        "layer": "4.5"
    },
    "domain": "enterprise-attack",
    "description": "MITRE ATT&CK techniques detected by DeepTempo LogLM",
    "filters": {
        "platforms": ["Windows", "Linux", "macOS", "Network"]
    },
    "sorting": 3,
    "layout": {
        "layout": "side",
        "aggregateFunction": "average",
        "showID": true,
        "showName": true,
        "showAggregateScores": true,
        "countUnscored": false
    },
    "hideDisabled": false,
    "techniques": [
        {
            "techniqueID": "T1071.001",
            "tactic": "command-and-control",
            "score": 85,
            "color": "",
            "comment": "15 findings, avg confidence 0.82",
            "enabled": true,
            "metadata": [
                {"name": "finding_count", "value": "15"},
                {"name": "avg_confidence", "value": "0.82"},
                {"name": "max_confidence", "value": "0.95"},
                {"name": "data_sources", "value": "flow, dns"}
            ],
            "links": [],
            "showSubtechniques": true
        }
    ],
    "gradient": {
        "colors": ["#ffffff", "#66b3ff", "#ff6666"],
        "minValue": 0,
        "maxValue": 100
    },
    "legendItems": [
        {"label": "Low confidence", "color": "#66b3ff"},
        {"label": "High confidence", "color": "#ff6666"}
    ],
    "metadata": [
        {"name": "generated_by", "value": "DeepTempo AI SOC"},
        {"name": "generation_time", "value": "[timestamp]"},
        {"name": "time_range_start", "value": "[start]"},
        {"name": "time_range_end", "value": "[end]"},
        {"name": "total_findings", "value": "[count]"},
        {"name": "total_techniques", "value": "[count]"}
    ],
    "links": [],
    "showTacticRowBackground": true,
    "tacticRowBackground": "#dddddd",
    "selectTechniquesAcrossTactics": true,
    "selectSubtechniquesWithParent": false,
    "selectVisibleTechniques": false
}
```

### Report Summary

Along with the JSON, provide a summary:

```markdown
# ATT&CK Layer Export Summary

**Layer Name**: [Name]
**Generated**: [Timestamp]
**Time Range**: [Start] to [End]

## Coverage Summary

| Metric | Value |
|--------|-------|
| Total Findings | [n] |
| Unique Techniques | [n] |
| Tactics Covered | [n]/14 |

## Top Techniques

| Rank | Technique | Name | Findings | Avg Confidence |
|------|-----------|------|----------|----------------|
| 1 | T1071.001 | Web Protocols | 15 | 0.82 |
| 2 | T1048.003 | Exfil Over Unencrypted | 8 | 0.75 |
| ... | ... | ... | ... | ... |

## Tactic Distribution

| Tactic | Techniques | Findings |
|--------|------------|----------|
| Command and Control | 3 | 25 |
| Exfiltration | 2 | 12 |
| ... | ... | ... |

## Notable Observations

- [Observation 1]
- [Observation 2]

## Usage Instructions

1. Open [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/)
2. Click "Open Existing Layer"
3. Select "Upload from local"
4. Choose the exported JSON file
5. Explore the visualization

---
*Layer generated by DeepTempo AI SOC*
```

## Scoring Strategies

### Strategy 1: Finding Count

Score based on number of findings per technique:

```python
score = min(100, finding_count * 10)
```

Pros: Simple, shows volume
Cons: Doesn't reflect confidence

### Strategy 2: Confidence-Based

Score based on average confidence:

```python
score = avg_confidence * 100
```

Pros: Reflects detection quality
Cons: Ignores volume

### Strategy 3: Combined (Recommended)

Combine count and confidence:

```python
volume_factor = min(1.0, finding_count / 10)
confidence_factor = avg_confidence
score = (volume_factor * 0.4 + confidence_factor * 0.6) * 100
```

Pros: Balanced view
Cons: More complex

## Color Schemes

### Confidence Gradient

```json
{
    "colors": ["#ffffff", "#ff6666"],
    "minValue": 0,
    "maxValue": 100
}
```

White (low) → Red (high confidence)

### Severity Gradient

```json
{
    "colors": ["#ffffcc", "#ffeda0", "#feb24c", "#f03b20"],
    "minValue": 0,
    "maxValue": 100
}
```

Yellow (low) → Orange → Red (high severity)

### Detection Coverage

```json
{
    "colors": ["#ffffff", "#2166ac"],
    "minValue": 0,
    "maxValue": 100
}
```

White (no detection) → Blue (detected)

## Examples

### Example 1: Daily Threat Summary

**Use Case**: Daily report for SOC leadership
**Scope**: Last 24 hours, all data sources
**Scoring**: Combined (count + confidence)
**Output**: Layer + executive summary

### Example 2: Incident Documentation

**Use Case**: Document techniques in specific incident
**Scope**: Incident time window, specific entities
**Scoring**: Confidence-based
**Output**: Layer + detailed technique analysis

### Example 3: Detection Gap Analysis

**Use Case**: Identify techniques not being detected
**Scope**: Last 30 days
**Scoring**: Finding count
**Output**: Layer highlighting gaps

## Guidelines

1. **Match scope to purpose** - Don't include irrelevant findings
2. **Use appropriate scoring** - Choose based on audience needs
3. **Add meaningful comments** - Help viewers understand context
4. **Include metadata** - Document generation parameters
5. **Provide summary** - Not everyone will open the Navigator

## Constraints

- **Validate technique IDs** - Ensure they exist in ATT&CK
- **Use current ATT&CK version** - Keep version metadata accurate
- **Don't overstate coverage** - Low-confidence detections should show as such
- **Document limitations** - Note what the layer doesn't show
