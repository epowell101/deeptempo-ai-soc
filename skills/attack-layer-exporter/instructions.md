# ATT&CK Layer Exporter - Detailed Instructions

## MITRE ATT&CK Overview

### What is ATT&CK?

MITRE ATT&CK (Adversarial Tactics, Techniques, and Common Knowledge) is a knowledge base of adversary behavior based on real-world observations.

### Key Concepts

- **Tactics**: The "why" - adversary goals (e.g., Initial Access, Execution)
- **Techniques**: The "how" - methods to achieve goals (e.g., T1566 Phishing)
- **Sub-techniques**: More specific variations (e.g., T1566.001 Spearphishing Attachment)
- **Procedures**: Specific implementations by threat actors

### Enterprise ATT&CK Tactics

| ID | Tactic | Description |
|----|--------|-------------|
| TA0043 | Reconnaissance | Gathering information |
| TA0042 | Resource Development | Establishing resources |
| TA0001 | Initial Access | Getting into the network |
| TA0002 | Execution | Running malicious code |
| TA0003 | Persistence | Maintaining access |
| TA0004 | Privilege Escalation | Gaining higher permissions |
| TA0005 | Defense Evasion | Avoiding detection |
| TA0006 | Credential Access | Stealing credentials |
| TA0007 | Discovery | Learning the environment |
| TA0008 | Lateral Movement | Moving through network |
| TA0009 | Collection | Gathering target data |
| TA0011 | Command and Control | Communicating with compromised systems |
| TA0010 | Exfiltration | Stealing data |
| TA0040 | Impact | Disrupting availability |

## Navigator Layer Format

### Required Fields

```json
{
    "name": "Layer Name",
    "versions": {
        "attack": "14",
        "navigator": "4.9.1",
        "layer": "4.5"
    },
    "domain": "enterprise-attack",
    "techniques": []
}
```

### Technique Entry Format

```json
{
    "techniqueID": "T1071.001",
    "tactic": "command-and-control",
    "score": 85,
    "color": "",
    "comment": "Detection details",
    "enabled": true,
    "metadata": [],
    "showSubtechniques": true
}
```

### Important Notes

- `techniqueID`: Must be valid ATT&CK ID
- `tactic`: Must match technique's valid tactics
- `score`: 0-100, used for gradient coloring
- `color`: Override gradient with specific color
- `comment`: Shown on hover in Navigator

## Common Techniques in Network Security

### Command and Control

| ID | Name | Indicators |
|----|------|------------|
| T1071.001 | Web Protocols | HTTP/HTTPS beaconing |
| T1071.004 | DNS | DNS tunneling, DGA |
| T1573.001 | Symmetric Cryptography | Encrypted C2 |
| T1571 | Non-Standard Port | Unusual port usage |

### Exfiltration

| ID | Name | Indicators |
|----|------|------------|
| T1048.003 | Unencrypted Non-C2 | Large outbound transfers |
| T1041 | Exfil Over C2 | Data in beacon traffic |
| T1567 | Exfil to Cloud | Cloud storage uploads |

### Discovery

| ID | Name | Indicators |
|----|------|------------|
| T1046 | Network Service Discovery | Port scanning |
| T1018 | Remote System Discovery | Network enumeration |
| T1082 | System Information Discovery | System queries |

### Lateral Movement

| ID | Name | Indicators |
|----|------|------------|
| T1021.001 | Remote Desktop | RDP connections |
| T1021.002 | SMB/Windows Admin Shares | SMB lateral movement |
| T1021.006 | Windows Remote Management | WinRM usage |

## Layer Generation Process

### Step 1: Collect Technique Data

```python
# Pseudo-code
technique_data = {}
for finding in findings:
    for technique_id, confidence in finding.mitre_predictions.items():
        if technique_id not in technique_data:
            technique_data[technique_id] = {
                "findings": [],
                "confidences": []
            }
        technique_data[technique_id]["findings"].append(finding.id)
        technique_data[technique_id]["confidences"].append(confidence)
```

### Step 2: Calculate Scores

```python
# Pseudo-code
for technique_id, data in technique_data.items():
    count = len(data["findings"])
    avg_conf = sum(data["confidences"]) / count
    
    # Combined scoring
    volume = min(1.0, count / 10)
    score = int((volume * 0.4 + avg_conf * 0.6) * 100)
    
    data["score"] = score
    data["avg_confidence"] = avg_conf
```

### Step 3: Build Technique Entries

```python
# Pseudo-code
techniques = []
for technique_id, data in technique_data.items():
    entry = {
        "techniqueID": technique_id,
        "tactic": get_primary_tactic(technique_id),
        "score": data["score"],
        "comment": f"{len(data['findings'])} findings, avg conf {data['avg_confidence']:.2f}",
        "enabled": True,
        "metadata": [
            {"name": "finding_count", "value": str(len(data["findings"]))},
            {"name": "avg_confidence", "value": f"{data['avg_confidence']:.2f}"}
        ],
        "showSubtechniques": True
    }
    techniques.append(entry)
```

### Step 4: Assemble Layer

```python
# Pseudo-code
layer = {
    "name": layer_name,
    "versions": {"attack": "14", "navigator": "4.9.1", "layer": "4.5"},
    "domain": "enterprise-attack",
    "description": description,
    "techniques": techniques,
    "gradient": {
        "colors": ["#ffffff", "#ff6666"],
        "minValue": 0,
        "maxValue": 100
    },
    "metadata": [
        {"name": "generated_by", "value": "DeepTempo AI SOC"},
        {"name": "time_range", "value": f"{start} to {end}"}
    ]
}
```

## Validation Checklist

Before exporting:

- [ ] All technique IDs are valid
- [ ] Tactics match technique definitions
- [ ] Scores are within 0-100 range
- [ ] Comments are informative
- [ ] Metadata is complete
- [ ] Version numbers are current
- [ ] Domain is correct (enterprise-attack)

## Troubleshooting

### Layer Won't Load

- Check JSON syntax (use validator)
- Verify required fields present
- Check technique ID format

### Techniques Not Showing

- Verify `enabled: true`
- Check tactic spelling
- Ensure technique exists in ATT&CK version

### Colors Not Displaying

- Check gradient configuration
- Verify score values
- Look for color override conflicts
