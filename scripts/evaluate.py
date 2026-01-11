#!/usr/bin/env python3
"""
Evaluation Framework

Calculates:
- Confusion matrix (TP, FP, FN, TN)
- Precision, Recall, F1 Score
- Mean Time to Detect (MTTD) per phase and overall
- Evasion analysis (what rules miss vs what LogLM catches)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any

SCENARIO_DIR = Path(__file__).parent.parent / "data" / "scenarios" / "default_attack"


def parse_timestamp(ts: str) -> datetime:
    """Parse ISO timestamp string."""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except:
        return datetime.fromisoformat(ts)


def evaluate_detection(detected_event_ids: Set[str], ground_truth: Dict) -> Dict:
    """
    Calculate confusion matrix and metrics.
    
    Args:
        detected_event_ids: Set of event IDs flagged as malicious
        ground_truth: Ground truth labels
    
    Returns:
        Confusion matrix and derived metrics
    """
    malicious_events = {
        eid for eid, info in ground_truth["events"].items()
        if info["label"] == "malicious"
    }
    benign_events = {
        eid for eid, info in ground_truth["events"].items()
        if info["label"] == "benign"
    }
    
    # Also track evasive events separately
    evasive_events = {
        eid for eid, info in ground_truth["events"].items()
        if info.get("evasive", False)
    }
    non_evasive_malicious = malicious_events - evasive_events
    
    tp = len(detected_event_ids & malicious_events)  # Correctly detected attacks
    fp = len(detected_event_ids & benign_events)     # False alarms
    fn = len(malicious_events - detected_event_ids)  # Missed attacks
    tn = len(benign_events - detected_event_ids)     # Correctly ignored benign
    
    # Evasive detection breakdown
    evasive_detected = len(detected_event_ids & evasive_events)
    evasive_missed = len(evasive_events - detected_event_ids)
    non_evasive_detected = len(detected_event_ids & non_evasive_malicious)
    non_evasive_missed = len(non_evasive_malicious - detected_event_ids)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    return {
        "confusion_matrix": {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn
        },
        "metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "accuracy": round((tp + tn) / (tp + tn + fp + fn), 4)
        },
        "counts": {
            "total_detected": len(detected_event_ids),
            "total_malicious": len(malicious_events),
            "total_benign": len(benign_events)
        },
        "evasion_analysis": {
            "total_evasive": len(evasive_events),
            "evasive_detected": evasive_detected,
            "evasive_missed": evasive_missed,
            "evasive_detection_rate": round(evasive_detected / len(evasive_events), 4) if evasive_events else 0,
            "non_evasive_detected": non_evasive_detected,
            "non_evasive_missed": non_evasive_missed,
            "non_evasive_detection_rate": round(non_evasive_detected / len(non_evasive_malicious), 4) if non_evasive_malicious else 0
        }
    }


def calculate_mttd(detections: List[Dict], ground_truth: Dict, event_id_field: str = "event_id") -> Dict:
    """
    Calculate Mean Time to Detect for each attack phase.
    
    Args:
        detections: List of detection objects with timestamps and event IDs
        ground_truth: Ground truth with attack timeline
        event_id_field: Field name containing the event ID in detections
    
    Returns:
        MTTD in minutes for each phase and overall
    """
    results = {}
    
    # Build detection lookup: event_id -> first detection timestamp
    detection_times = {}
    for det in detections:
        event_ids = det.get("event_ids", [det.get(event_id_field)])
        if not event_ids:
            continue
        det_time = parse_timestamp(det["timestamp"])
        for eid in event_ids:
            if eid and (eid not in detection_times or det_time < detection_times[eid]):
                detection_times[eid] = det_time
    
    # Calculate MTTD per phase
    overall_attack_start = None
    overall_first_detection = None
    
    for phase_info in ground_truth["attack_timeline"]:
        phase_num = phase_info["phase"]
        phase_start = parse_timestamp(phase_info["start_time"])
        phase_events = set(phase_info["event_ids"])
        is_evasive = phase_info.get("evasive", False)
        
        if overall_attack_start is None or phase_start < overall_attack_start:
            overall_attack_start = phase_start
        
        # Find first detection of any event in this phase
        first_detection = None
        for eid in phase_events:
            if eid in detection_times:
                det_time = detection_times[eid]
                if first_detection is None or det_time < first_detection:
                    first_detection = det_time
        
        if first_detection:
            mttd_minutes = (first_detection - phase_start).total_seconds() / 60
            results[f"phase_{phase_num}"] = {
                "phase_name": phase_info["name"],
                "detected": True,
                "mttd_minutes": round(max(0, mttd_minutes), 1),
                "phase_start": phase_start.isoformat(),
                "first_detection": first_detection.isoformat(),
                "evasive": is_evasive
            }
            
            if overall_first_detection is None or first_detection < overall_first_detection:
                overall_first_detection = first_detection
        else:
            results[f"phase_{phase_num}"] = {
                "phase_name": phase_info["name"],
                "detected": False,
                "mttd_minutes": None,
                "phase_start": phase_start.isoformat(),
                "first_detection": None,
                "evasive": is_evasive
            }
    
    # Overall MTTD
    if overall_first_detection and overall_attack_start:
        overall_mttd = (overall_first_detection - overall_attack_start).total_seconds() / 60
        results["overall"] = {
            "detected": True,
            "mttd_minutes": round(max(0, overall_mttd), 1),
            "attack_start": overall_attack_start.isoformat(),
            "first_detection": overall_first_detection.isoformat()
        }
    else:
        results["overall"] = {
            "detected": False,
            "mttd_minutes": None
        }
    
    # Calculate average MTTD across detected phases
    detected_mttds = [
        v["mttd_minutes"] for k, v in results.items()
        if k.startswith("phase_") and v["detected"]
    ]
    if detected_mttds:
        results["average_phase_mttd"] = round(sum(detected_mttds) / len(detected_mttds), 1)
    else:
        results["average_phase_mttd"] = None
    
    # Count phases detected (separate evasive and non-evasive)
    phases_detected = sum(1 for k, v in results.items() if k.startswith("phase_") and v["detected"])
    total_phases = sum(1 for k in results.keys() if k.startswith("phase_"))
    evasive_phases_detected = sum(1 for k, v in results.items() if k.startswith("phase_") and v["detected"] and v.get("evasive"))
    total_evasive_phases = sum(1 for k, v in results.items() if k.startswith("phase_") and v.get("evasive"))
    
    results["phases_detected"] = f"{phases_detected}/{total_phases}"
    results["evasive_phases_detected"] = f"{evasive_phases_detected}/{total_evasive_phases}" if total_evasive_phases > 0 else "N/A"
    
    return results


def run_evaluation():
    """Run full evaluation comparing both detection methods."""
    print("=" * 60)
    print("Running Evaluation")
    print("=" * 60)
    
    # Load ground truth
    with open(SCENARIO_DIR / "ground_truth.json") as f:
        ground_truth = json.load(f)
    
    # Load rules alerts
    with open(SCENARIO_DIR / "rules_output" / "alerts.json") as f:
        rules_alerts = json.load(f)
    
    # Load LogLM findings
    with open(SCENARIO_DIR / "loglm_output" / "findings.json") as f:
        loglm_findings = json.load(f)
    
    # Extract detected event IDs
    rules_detected = set()
    for alert in rules_alerts:
        if alert.get("event_id"):
            rules_detected.add(alert["event_id"])
    
    loglm_detected = set()
    for finding in loglm_findings:
        for eid in finding.get("event_ids", []):
            loglm_detected.add(eid)
    
    print(f"\nRules detected {len(rules_detected)} unique events")
    print(f"LogLM detected {len(loglm_detected)} unique events")
    
    # Calculate confusion matrices
    rules_eval = evaluate_detection(rules_detected, ground_truth)
    loglm_eval = evaluate_detection(loglm_detected, ground_truth)
    
    # Calculate MTTD
    rules_mttd = calculate_mttd(rules_alerts, ground_truth, "event_id")
    loglm_mttd = calculate_mttd(loglm_findings, ground_truth, "event_ids")
    
    # Compile results
    results = {
        "rules_only": {
            **rules_eval,
            "mttd": rules_mttd,
            "alert_count": len(rules_alerts)
        },
        "loglm": {
            **loglm_eval,
            "mttd": loglm_mttd,
            "finding_count": len(loglm_findings)
        },
        "comparison": {
            "precision_improvement": round(loglm_eval["metrics"]["precision"] - rules_eval["metrics"]["precision"], 4),
            "recall_improvement": round(loglm_eval["metrics"]["recall"] - rules_eval["metrics"]["recall"], 4),
            "f1_improvement": round(loglm_eval["metrics"]["f1_score"] - rules_eval["metrics"]["f1_score"], 4),
            "alert_reduction": round(1 - len(loglm_findings) / len(rules_alerts), 4) if rules_alerts else 0,
            "mttd_improvement_minutes": round(
                (rules_mttd["overall"]["mttd_minutes"] or 999) - (loglm_mttd["overall"]["mttd_minutes"] or 999), 1
            ) if rules_mttd["overall"]["detected"] and loglm_mttd["overall"]["detected"] else None,
            "evasion_detection_improvement": round(
                loglm_eval["evasion_analysis"]["evasive_detection_rate"] - 
                rules_eval["evasion_analysis"]["evasive_detection_rate"], 4
            )
        }
    }
    
    # Save results
    with open(SCENARIO_DIR / "evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    
    print("\n📊 CONFUSION MATRIX COMPARISON")
    print("-"*60)
    print(f"{'Metric':<25} {'Rules-Only':<15} {'LogLM':<15}")
    print("-"*60)
    print(f"{'True Positives':<25} {rules_eval['confusion_matrix']['true_positives']:<15} {loglm_eval['confusion_matrix']['true_positives']:<15}")
    print(f"{'False Positives':<25} {rules_eval['confusion_matrix']['false_positives']:<15} {loglm_eval['confusion_matrix']['false_positives']:<15}")
    print(f"{'False Negatives':<25} {rules_eval['confusion_matrix']['false_negatives']:<15} {loglm_eval['confusion_matrix']['false_negatives']:<15}")
    print(f"{'True Negatives':<25} {rules_eval['confusion_matrix']['true_negatives']:<15} {loglm_eval['confusion_matrix']['true_negatives']:<15}")
    
    print("\n📈 PERFORMANCE METRICS")
    print("-"*60)
    print(f"{'Metric':<25} {'Rules-Only':<15} {'LogLM':<15}")
    print("-"*60)
    print(f"{'Precision':<25} {rules_eval['metrics']['precision']*100:.1f}%{'':<10} {loglm_eval['metrics']['precision']*100:.1f}%")
    print(f"{'Recall':<25} {rules_eval['metrics']['recall']*100:.1f}%{'':<10} {loglm_eval['metrics']['recall']*100:.1f}%")
    print(f"{'F1 Score':<25} {rules_eval['metrics']['f1_score']:.3f}{'':<11} {loglm_eval['metrics']['f1_score']:.3f}")
    print(f"{'False Positive Rate':<25} {rules_eval['metrics']['false_positive_rate']*100:.1f}%{'':<10} {loglm_eval['metrics']['false_positive_rate']*100:.1f}%")
    
    print("\n🥷 EVASION ANALYSIS")
    print("-"*60)
    print(f"{'Metric':<25} {'Rules-Only':<15} {'LogLM':<15}")
    print("-"*60)
    rules_evasion = rules_eval["evasion_analysis"]
    loglm_evasion = loglm_eval["evasion_analysis"]
    print(f"{'Total Evasive Events':<25} {rules_evasion['total_evasive']:<15} {loglm_evasion['total_evasive']:<15}")
    print(f"{'Evasive Detected':<25} {rules_evasion['evasive_detected']:<15} {loglm_evasion['evasive_detected']:<15}")
    print(f"{'Evasive Missed':<25} {rules_evasion['evasive_missed']:<15} {loglm_evasion['evasive_missed']:<15}")
    print(f"{'Evasive Detection Rate':<25} {rules_evasion['evasive_detection_rate']*100:.1f}%{'':<10} {loglm_evasion['evasive_detection_rate']*100:.1f}%")
    
    print("\n⏱️ MEAN TIME TO DETECT (MTTD)")
    print("-"*60)
    print(f"{'Phase':<35} {'Rules-Only':<15} {'LogLM':<15}")
    print("-"*60)
    
    for phase_key in sorted([k for k in rules_mttd.keys() if k.startswith("phase_")]):
        rules_phase = rules_mttd[phase_key]
        loglm_phase = loglm_mttd[phase_key]
        
        rules_val = f"{rules_phase['mttd_minutes']} min" if rules_phase['detected'] else "NOT DETECTED"
        loglm_val = f"{loglm_phase['mttd_minutes']} min" if loglm_phase['detected'] else "NOT DETECTED"
        
        evasive_marker = " [EVASIVE]" if rules_phase.get("evasive") else ""
        print(f"{rules_phase['phase_name'][:30]}{evasive_marker:<5} {rules_val:<15} {loglm_val:<15}")
    
    print("-"*60)
    rules_overall = f"{rules_mttd['overall']['mttd_minutes']} min" if rules_mttd['overall']['detected'] else "NOT DETECTED"
    loglm_overall = f"{loglm_mttd['overall']['mttd_minutes']} min" if loglm_mttd['overall']['detected'] else "NOT DETECTED"
    print(f"{'OVERALL':<35} {rules_overall:<15} {loglm_overall:<15}")
    print(f"{'Phases Detected':<35} {rules_mttd['phases_detected']:<15} {loglm_mttd['phases_detected']:<15}")
    print(f"{'Evasive Phases Detected':<35} {rules_mttd['evasive_phases_detected']:<15} {loglm_mttd['evasive_phases_detected']:<15}")
    
    print("\n🎯 SUMMARY")
    print("-"*60)
    print(f"Rules-Only: {len(rules_alerts)} alerts, {rules_eval['metrics']['precision']*100:.1f}% precision")
    print(f"LogLM:      {len(loglm_findings)} findings, {loglm_eval['metrics']['precision']*100:.1f}% precision")
    print(f"\nLogLM reduces alerts by {results['comparison']['alert_reduction']*100:.0f}% while improving precision by {results['comparison']['precision_improvement']*100:.1f} percentage points")
    
    print(f"\n🥷 EVASION DETECTION:")
    print(f"  Rules-Only catches {rules_evasion['evasive_detection_rate']*100:.0f}% of evasive attacks")
    print(f"  LogLM catches {loglm_evasion['evasive_detection_rate']*100:.0f}% of evasive attacks")
    print(f"  Improvement: +{results['comparison']['evasion_detection_improvement']*100:.0f} percentage points")
    
    if results['comparison']['mttd_improvement_minutes']:
        print(f"\nLogLM detects attacks {results['comparison']['mttd_improvement_minutes']:.0f} minutes faster on average")
    
    return results


if __name__ == "__main__":
    run_evaluation()
