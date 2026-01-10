#!/usr/bin/env python3
"""
DeepTempo AI SOC Demo Script

This script demonstrates the core functionality of the AI SOC:
1. Loading sample findings
2. Searching for similar findings
3. Generating technique rollups
4. Exporting ATT&CK Navigator layers
5. Creating investigation cases

Usage:
    python scripts/demo.py
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from adapters.deeptempo_offline_export.loader import (
    generate_sample_findings,
    save_findings,
    load_findings,
)
from mcp.deeptempo_findings_server.server import (
    get_finding_by_id,
    cosine_similarity,
    filter_findings,
)
from mcp.case_store_server.server import (
    load_cases,
    save_cases,
    generate_case_id,
)

import numpy as np


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def demo_load_findings():
    """Demo: Load sample findings."""
    print_header("Step 1: Loading Sample Findings")
    
    findings = generate_sample_findings(50)
    save_findings(findings)
    
    print(f"Generated {len(findings)} sample findings")
    print(f"\nSample finding:")
    sample = findings[0]
    print(f"  ID: {sample['finding_id']}")
    print(f"  Data Source: {sample['data_source']}")
    print(f"  Anomaly Score: {sample['anomaly_score']}")
    print(f"  MITRE Predictions: {sample['mitre_predictions']}")
    print(f"  Embedding dimensions: {len(sample['embedding'])}")
    
    return findings


def demo_nearest_neighbors(findings: list[dict]):
    """Demo: Find similar findings."""
    print_header("Step 2: Finding Similar Findings (Nearest Neighbors)")
    
    # Pick a high-severity finding as seed
    seed = None
    for f in findings:
        if f.get("severity") == "high" and f.get("cluster_id"):
            seed = f
            break
    
    if not seed:
        seed = findings[0]
    
    print(f"Seed finding: {seed['finding_id']}")
    print(f"  Cluster: {seed.get('cluster_id', 'None')}")
    print(f"  Anomaly Score: {seed['anomaly_score']}")
    
    # Find nearest neighbors
    seed_embedding = np.array(seed['embedding'])
    similarities = []
    
    for f in findings:
        if f['finding_id'] == seed['finding_id']:
            continue
        
        embedding = np.array(f['embedding'])
        sim = cosine_similarity(seed_embedding, embedding)
        similarities.append((f, sim))
    
    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\nTop 5 similar findings:")
    for f, sim in similarities[:5]:
        print(f"  {f['finding_id']}: similarity={sim:.4f}, cluster={f.get('cluster_id', 'None')}")
    
    return seed, similarities[:10]


def demo_technique_rollup(findings: list[dict]):
    """Demo: Aggregate MITRE ATT&CK techniques."""
    print_header("Step 3: MITRE ATT&CK Technique Rollup")
    
    # Aggregate techniques
    technique_data = {}
    for finding in findings:
        for tech_id, confidence in finding.get("mitre_predictions", {}).items():
            if confidence < 0.5:
                continue
            
            if tech_id not in technique_data:
                technique_data[tech_id] = {
                    "count": 0,
                    "confidences": []
                }
            
            technique_data[tech_id]["count"] += 1
            technique_data[tech_id]["confidences"].append(confidence)
    
    # Build results
    results = []
    for tech_id, data in technique_data.items():
        results.append({
            "technique_id": tech_id,
            "finding_count": data["count"],
            "avg_confidence": sum(data["confidences"]) / len(data["confidences"])
        })
    
    results.sort(key=lambda x: x["finding_count"], reverse=True)
    
    print(f"Techniques detected (min confidence 0.5):")
    print(f"\n{'Technique':<12} {'Count':<8} {'Avg Confidence':<15}")
    print("-" * 35)
    for r in results[:10]:
        print(f"{r['technique_id']:<12} {r['finding_count']:<8} {r['avg_confidence']:.3f}")
    
    return results


def demo_attack_layer(technique_rollup: list[dict]):
    """Demo: Generate ATT&CK Navigator layer."""
    print_header("Step 4: Generating ATT&CK Navigator Layer")
    
    techniques = []
    for tech in technique_rollup:
        volume_factor = min(1.0, tech["finding_count"] / 10)
        confidence_factor = tech["avg_confidence"]
        score = int((volume_factor * 0.4 + confidence_factor * 0.6) * 100)
        
        techniques.append({
            "techniqueID": tech["technique_id"],
            "score": score,
            "comment": f"{tech['finding_count']} findings, avg conf {tech['avg_confidence']:.2f}",
            "enabled": True,
            "showSubtechniques": True
        })
    
    layer = {
        "name": "DeepTempo Demo Layer",
        "versions": {
            "attack": "14",
            "navigator": "4.9.1",
            "layer": "4.5"
        },
        "domain": "enterprise-attack",
        "description": "Demo ATT&CK layer generated from sample findings",
        "techniques": techniques,
        "gradient": {
            "colors": ["#ffffff", "#66b3ff", "#ff6666"],
            "minValue": 0,
            "maxValue": 100
        }
    }
    
    # Save layer
    layer_path = PROJECT_ROOT / "data" / "demo_layer.json"
    with open(layer_path, 'w') as f:
        json.dump(layer, f, indent=2)
    
    print(f"Generated ATT&CK Navigator layer with {len(techniques)} techniques")
    print(f"Saved to: {layer_path}")
    print(f"\nTo view: Open https://mitre-attack.github.io/attack-navigator/")
    print(f"         Click 'Open Existing Layer' > 'Upload from local'")
    
    return layer


def demo_create_case(seed_finding: dict, neighbors: list):
    """Demo: Create an investigation case."""
    print_header("Step 5: Creating Investigation Case")
    
    # Get finding IDs
    finding_ids = [seed_finding['finding_id']]
    finding_ids.extend([f['finding_id'] for f, _ in neighbors[:4]])
    
    # Create case
    now = datetime.utcnow().isoformat() + "Z"
    case = {
        "case_id": generate_case_id(),
        "title": f"Investigation: {seed_finding.get('cluster_id', 'Suspicious Activity')}",
        "description": f"Automated case created from finding {seed_finding['finding_id']} and {len(finding_ids)-1} similar findings",
        "finding_ids": finding_ids,
        "status": "new",
        "priority": "high" if seed_finding.get("severity") in ["high", "critical"] else "medium",
        "assignee": "",
        "tags": ["auto-generated", "demo"],
        "notes": [],
        "timeline": [
            {"timestamp": now, "event": "Case created by demo script"}
        ],
        "created_at": now,
        "updated_at": now
    }
    
    # Save case
    cases = load_cases()
    cases.append(case)
    save_cases(cases)
    
    print(f"Created case: {case['case_id']}")
    print(f"  Title: {case['title']}")
    print(f"  Priority: {case['priority']}")
    print(f"  Findings: {len(case['finding_ids'])}")
    
    return case


def demo_summary(findings: list[dict]):
    """Print demo summary."""
    print_header("Demo Summary")
    
    # Count by source
    by_source = {}
    for f in findings:
        source = f.get("data_source", "unknown")
        by_source[source] = by_source.get(source, 0) + 1
    
    # Count by severity
    by_severity = {}
    for f in findings:
        sev = f.get("severity", "unknown")
        by_severity[sev] = by_severity.get(sev, 0) + 1
    
    # Count clusters
    clusters = set(f.get("cluster_id") for f in findings if f.get("cluster_id"))
    
    print(f"Total Findings: {len(findings)}")
    print(f"\nBy Data Source:")
    for source, count in sorted(by_source.items()):
        print(f"  {source}: {count}")
    
    print(f"\nBy Severity:")
    for sev in ["critical", "high", "medium", "low"]:
        print(f"  {sev}: {by_severity.get(sev, 0)}")
    
    print(f"\nClusters: {len(clusters)}")
    
    print(f"\nData files created:")
    print(f"  - data/findings.json")
    print(f"  - data/cases.json")
    print(f"  - data/demo_layer.json")


def main():
    """Run the demo."""
    print("\n" + "="*60)
    print(" DeepTempo AI SOC - Demo")
    print("="*60)
    
    # Step 1: Load findings
    findings = demo_load_findings()
    
    # Step 2: Find similar findings
    seed, neighbors = demo_nearest_neighbors(findings)
    
    # Step 3: Technique rollup
    rollup = demo_technique_rollup(findings)
    
    # Step 4: Generate ATT&CK layer
    layer = demo_attack_layer(rollup)
    
    # Step 5: Create case
    case = demo_create_case(seed, neighbors)
    
    # Summary
    demo_summary(findings)
    
    print("\n" + "="*60)
    print(" Demo Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
