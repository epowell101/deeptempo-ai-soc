"""
Tale of Two SOCs - Comparison Dashboard

This dashboard demonstrates the difference between:
- Rules-Only SOC: Traditional SIEM with Sigma rules
- LogLM-Enhanced SOC: DeepTempo LogLM with embeddings and correlation

Key features:
- Side-by-side comparison view
- Confusion matrix visualization
- MTTD (Mean Time to Detect) comparison
- Mode switching for Claude integration
- Rule visibility and evasion analysis
- Replay capability
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path
from datetime import datetime
import numpy as np

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
SCENARIO_DIR = DATA_DIR / "scenarios" / "default_attack"
MODE_FILE = DATA_DIR / "current_mode.txt"

st.set_page_config(
    page_title="Tale of Two SOCs",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .rules-box {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .loglm-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .evasion-box {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .metric-card {
        background-color: #f5f5f5;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .big-number {
        font-size: 48px;
        font-weight: bold;
    }
    .comparison-header {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .high-risk {
        color: #f44336;
        font-weight: bold;
    }
    .medium-risk {
        color: #ff9800;
        font-weight: bold;
    }
    .low-risk {
        color: #4caf50;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load all scenario data."""
    data = {}
    
    # Load manifest
    manifest_file = SCENARIO_DIR / "manifest.json"
    if manifest_file.exists():
        with open(manifest_file) as f:
            data["manifest"] = json.load(f)
    
    # Load ground truth
    gt_file = SCENARIO_DIR / "ground_truth.json"
    if gt_file.exists():
        with open(gt_file) as f:
            data["ground_truth"] = json.load(f)
    
    # Load rules alerts
    alerts_file = SCENARIO_DIR / "rules_output" / "alerts.json"
    if alerts_file.exists():
        with open(alerts_file) as f:
            data["alerts"] = json.load(f)
    
    # Load rule stats
    rule_stats_file = SCENARIO_DIR / "rules_output" / "rule_stats.json"
    if rule_stats_file.exists():
        with open(rule_stats_file) as f:
            data["rule_stats"] = json.load(f)
    
    # Load rule definitions
    rule_defs_file = SCENARIO_DIR / "rules_output" / "rule_definitions.json"
    if rule_defs_file.exists():
        with open(rule_defs_file) as f:
            data["rule_definitions"] = json.load(f)
    
    # Load LogLM findings
    findings_file = SCENARIO_DIR / "loglm_output" / "findings.json"
    if findings_file.exists():
        with open(findings_file) as f:
            data["findings"] = json.load(f)
    
    # Load incidents
    incidents_file = SCENARIO_DIR / "loglm_output" / "incidents.json"
    if incidents_file.exists():
        with open(incidents_file) as f:
            data["incidents"] = json.load(f)
    
    # Load evaluation results
    eval_file = SCENARIO_DIR / "evaluation_results.json"
    if eval_file.exists():
        with open(eval_file) as f:
            data["evaluation"] = json.load(f)
    
    return data


def get_current_mode():
    """Get current SOC mode."""
    if MODE_FILE.exists():
        return MODE_FILE.read_text().strip()
    return "loglm"


def set_mode(mode):
    """Set SOC mode."""
    MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
    MODE_FILE.write_text(mode)


def create_confusion_matrix_chart(cm_data, title):
    """Create a confusion matrix heatmap."""
    matrix = [
        [cm_data["true_positives"], cm_data["false_positives"]],
        [cm_data["false_negatives"], cm_data["true_negatives"]]
    ]
    
    labels = ["Detected", "Not Detected"]
    columns = ["Malicious", "Benign"]
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=columns,
        y=labels,
        text=[[str(v) for v in row] for row in matrix],
        texttemplate="%{text}",
        textfont={"size": 20},
        colorscale=[[0, "#e8f5e9"], [0.5, "#fff9c4"], [1, "#ffcdd2"]],
        showscale=False
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Ground Truth",
        yaxis_title="Detection",
        height=300
    )
    
    return fig


def create_mttd_comparison_chart(rules_mttd, loglm_mttd):
    """Create MTTD comparison bar chart."""
    phases = []
    rules_values = []
    loglm_values = []
    
    for key in sorted([k for k in rules_mttd.keys() if k.startswith("phase_")]):
        phase_name = rules_mttd[key]["phase_name"]
        phases.append(phase_name)
        
        rules_val = rules_mttd[key]["mttd_minutes"] if rules_mttd[key]["detected"] else None
        loglm_val = loglm_mttd[key]["mttd_minutes"] if loglm_mttd[key]["detected"] else None
        
        rules_values.append(rules_val)
        loglm_values.append(loglm_val)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name="Rules-Only",
        x=phases,
        y=rules_values,
        marker_color="#f44336",
        text=[f"{v:.1f} min" if v else "NOT DETECTED" for v in rules_values],
        textposition="outside"
    ))
    
    fig.add_trace(go.Bar(
        name="LogLM",
        x=phases,
        y=loglm_values,
        marker_color="#4caf50",
        text=[f"{v:.1f} min" if v else "NOT DETECTED" for v in loglm_values],
        textposition="outside"
    ))
    
    fig.update_layout(
        title="Mean Time to Detect (MTTD) by Attack Phase",
        xaxis_title="Attack Phase",
        yaxis_title="Minutes to Detect",
        barmode="group",
        height=400
    )
    
    return fig


def create_metrics_comparison_chart(rules_metrics, loglm_metrics):
    """Create metrics comparison radar chart."""
    categories = ["Precision", "Recall", "F1 Score", "1 - FPR"]
    
    rules_values = [
        rules_metrics["precision"],
        rules_metrics["recall"],
        rules_metrics["f1_score"],
        1 - rules_metrics["false_positive_rate"]
    ]
    
    loglm_values = [
        loglm_metrics["precision"],
        loglm_metrics["recall"],
        loglm_metrics["f1_score"],
        1 - loglm_metrics["false_positive_rate"]
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=rules_values + [rules_values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name="Rules-Only",
        line_color="#f44336",
        fillcolor="rgba(244, 67, 54, 0.3)"
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=loglm_values + [loglm_values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name="LogLM",
        line_color="#4caf50",
        fillcolor="rgba(76, 175, 80, 0.3)"
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title="Detection Performance Comparison",
        height=400
    )
    
    return fig


def create_evasion_chart(rule_stats):
    """Create chart showing rule evasion risk."""
    if not rule_stats:
        return None
    
    df = pd.DataFrame([
        {
            "Rule": v["name"][:30] + "..." if len(v["name"]) > 30 else v["name"],
            "Evasion Risk": v.get("evasion_risk", "UNKNOWN"),
            "Alerts": v["alert_count"]
        }
        for v in rule_stats.values()
    ])
    
    color_map = {"HIGH": "#f44336", "MEDIUM": "#ff9800", "LOW": "#4caf50", "UNKNOWN": "#9e9e9e"}
    df["Color"] = df["Evasion Risk"].map(color_map)
    
    fig = px.bar(
        df,
        x="Rule",
        y="Alerts",
        color="Evasion Risk",
        color_discrete_map=color_map,
        title="Alert Count by Rule (colored by Evasion Risk)"
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400
    )
    
    return fig


def main():
    """Main dashboard."""
    st.title("⚔️ Tale of Two SOCs")
    st.markdown("**Compare Rules-Only Detection vs. LogLM-Enhanced Detection**")
    
    # Load data
    data = load_data()
    
    if not data.get("evaluation"):
        st.error("Evaluation data not found. Please run the evaluation script first.")
        st.code("python scripts/evaluate.py", language="bash")
        return
    
    # Sidebar - Mode Control
    st.sidebar.header("🎛️ SOC Mode Control")
    
    current_mode = get_current_mode()
    
    mode_options = {
        "rules_only": "🔴 Rules-Only",
        "loglm": "🟢 LogLM-Enhanced"
    }
    
    selected_mode = st.sidebar.radio(
        "Select Mode for Claude",
        options=list(mode_options.keys()),
        format_func=lambda x: mode_options[x],
        index=0 if current_mode == "rules_only" else 1
    )
    
    if selected_mode != current_mode:
        set_mode(selected_mode)
        st.sidebar.success(f"Mode changed to {mode_options[selected_mode]}")
        st.sidebar.warning("⚠️ Start a new Claude conversation to use the new tools.")
    
    st.sidebar.markdown("---")
    
    # Sidebar - Scenario Info
    st.sidebar.header("📊 Scenario Info")
    manifest = data.get("manifest", {})
    st.sidebar.markdown(f"**{manifest.get('name', 'Unknown')}**")
    st.sidebar.markdown(f"Duration: {manifest.get('duration_hours', 0)} hours")
    st.sidebar.markdown(f"Total Events: {manifest.get('total_events', 0):,}")
    st.sidebar.markdown(f"Malicious: {manifest.get('malicious_events', 0)}")
    st.sidebar.markdown(f"  - Detectable: {manifest.get('detectable_events', 0)}")
    st.sidebar.markdown(f"  - Evasive: {manifest.get('evasive_events', 0)}")
    st.sidebar.markdown(f"Benign: {manifest.get('benign_events', 0):,}")
    
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **LogLM detects malicious BEHAVIORS, not just anomalies.**
    
    This is why it has high precision - it's trained to recognize actual attack patterns, not just statistical outliers.
    
    **LogLM catches evasive attacks** that rules miss through behavioral analysis of flow patterns.
    """)
    
    # Main content - Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Comparison Overview",
        "🔍 Detailed Metrics",
        "⏱️ MTTD Analysis",
        "📋 Rule Analysis",
        "🥷 Evasion Analysis"
    ])
    
    eval_data = data["evaluation"]
    rules_eval = eval_data["rules_only"]
    loglm_eval = eval_data["loglm"]
    
    # Tab 1: Comparison Overview
    with tab1:
        st.header("Side-by-Side Comparison")
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Alert Reduction",
                f"{eval_data['comparison']['alert_reduction']*100:.0f}%",
                help="LogLM reduces alert volume while maintaining coverage"
            )
        
        with col2:
            st.metric(
                "Precision Improvement",
                f"+{eval_data['comparison']['precision_improvement']*100:.1f}%",
                help="LogLM has much higher precision (fewer false positives)"
            )
        
        with col3:
            st.metric(
                "F1 Score Improvement",
                f"+{eval_data['comparison']['f1_improvement']:.3f}",
                help="Overall detection quality improvement"
            )
        
        with col4:
            phases_rules = rules_eval["mttd"]["phases_detected"]
            phases_loglm = loglm_eval["mttd"]["phases_detected"]
            st.metric(
                "Phases Detected",
                f"{phases_loglm}",
                delta=f"vs {phases_rules} (Rules)",
                help="Attack phases successfully detected"
            )
        
        st.markdown("---")
        
        # Side by side comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="rules-box">', unsafe_allow_html=True)
            st.subheader("🔴 Rules-Only SOC")
            st.markdown(f"""
            - **{rules_eval['alert_count']} alerts** generated
            - **{rules_eval['metrics']['precision']*100:.1f}% precision** (many false positives)
            - **{rules_eval['confusion_matrix']['false_positives']} false alarms**
            - No automatic correlation
            - No similarity search
            - No MITRE classification
            - ❌ **Misses evasive attacks**
            
            *Analyst must manually review each alert and correlate them.*
            """)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="loglm-box">', unsafe_allow_html=True)
            st.subheader("🟢 LogLM-Enhanced SOC")
            st.markdown(f"""
            - **{loglm_eval['finding_count']} findings** generated
            - **{loglm_eval['metrics']['precision']*100:.1f}% precision** (few false positives)
            - **{loglm_eval['confusion_matrix']['false_positives']} false alarms**
            - ✅ Automatic correlation into incidents
            - ✅ Embedding-based similarity search
            - ✅ MITRE ATT&CK classification
            - ✅ **Catches evasive attacks**
            
            *Analyst gets a clear attack narrative with correlated evidence.*
            """)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Radar chart
        st.plotly_chart(
            create_metrics_comparison_chart(
                rules_eval["metrics"],
                loglm_eval["metrics"]
            ),
            use_container_width=True
        )
    
    # Tab 2: Detailed Metrics
    with tab2:
        st.header("Confusion Matrix Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(
                create_confusion_matrix_chart(
                    rules_eval["confusion_matrix"],
                    "Rules-Only Confusion Matrix"
                ),
                use_container_width=True
            )
            
            st.markdown("**Rules-Only Metrics:**")
            metrics_df = pd.DataFrame([{
                "Metric": k.replace("_", " ").title(),
                "Value": f"{v*100:.2f}%" if v < 1 else f"{v:.4f}"
            } for k, v in rules_eval["metrics"].items()])
            st.dataframe(metrics_df, hide_index=True)
        
        with col2:
            st.plotly_chart(
                create_confusion_matrix_chart(
                    loglm_eval["confusion_matrix"],
                    "LogLM Confusion Matrix"
                ),
                use_container_width=True
            )
            
            st.markdown("**LogLM Metrics:**")
            metrics_df = pd.DataFrame([{
                "Metric": k.replace("_", " ").title(),
                "Value": f"{v*100:.2f}%" if v < 1 else f"{v:.4f}"
            } for k, v in loglm_eval["metrics"].items()])
            st.dataframe(metrics_df, hide_index=True)
        
        # Explanation
        st.markdown("---")
        st.markdown("""
        ### Understanding the Metrics
        
        | Metric | What It Means | Why LogLM Wins |
        |--------|---------------|----------------|
        | **Precision** | % of detections that are real attacks | LogLM identifies malicious *behaviors*, not just anomalies |
        | **Recall** | % of attacks that were detected | Both methods detect most attacks, but LogLM does it with less noise |
        | **F1 Score** | Balance of precision and recall | LogLM's high precision dramatically improves F1 |
        | **False Positive Rate** | % of benign events incorrectly flagged | LogLM's behavior-based detection minimizes false alarms |
        """)
    
    # Tab 3: MTTD Analysis
    with tab3:
        st.header("Mean Time to Detect (MTTD) Analysis")
        
        st.plotly_chart(
            create_mttd_comparison_chart(
                rules_eval["mttd"],
                loglm_eval["mttd"]
            ),
            use_container_width=True
        )
        
        # MTTD table
        st.markdown("### MTTD by Phase")
        
        mttd_data = []
        for key in sorted([k for k in rules_eval["mttd"].keys() if k.startswith("phase_")]):
            rules_phase = rules_eval["mttd"][key]
            loglm_phase = loglm_eval["mttd"][key]
            
            mttd_data.append({
                "Phase": rules_phase["phase_name"],
                "Rules-Only": f"{rules_phase['mttd_minutes']:.1f} min" if rules_phase["detected"] else "❌ NOT DETECTED",
                "LogLM": f"{loglm_phase['mttd_minutes']:.1f} min" if loglm_phase["detected"] else "❌ NOT DETECTED",
            })
        
        st.dataframe(pd.DataFrame(mttd_data), hide_index=True, use_container_width=True)
        
        # Overall MTTD
        col1, col2 = st.columns(2)
        with col1:
            overall_rules = rules_eval["mttd"]["overall"]
            if overall_rules["detected"]:
                st.metric("Rules-Only Overall MTTD", f"{overall_rules['mttd_minutes']:.1f} min")
            else:
                st.metric("Rules-Only Overall MTTD", "NOT DETECTED")
        
        with col2:
            overall_loglm = loglm_eval["mttd"]["overall"]
            if overall_loglm["detected"]:
                st.metric("LogLM Overall MTTD", f"{overall_loglm['mttd_minutes']:.1f} min")
            else:
                st.metric("LogLM Overall MTTD", "NOT DETECTED")
    
    # Tab 4: Rule Analysis
    with tab4:
        st.header("📋 Detection Rule Analysis")
        
        st.markdown("""
        This section shows the Sigma-like rules used in the Rules-Only SOC, 
        including their logic, thresholds, and **evasion risk**.
        """)
        
        rule_stats = data.get("rule_stats", {})
        rule_defs = data.get("rule_definitions", [])
        
        # Rule evasion chart
        if rule_stats:
            evasion_chart = create_evasion_chart(rule_stats)
            if evasion_chart:
                st.plotly_chart(evasion_chart, use_container_width=True)
        
        st.markdown("### Rule Definitions")
        
        # Create rule definitions from stats if not available
        if not rule_defs and rule_stats:
            rule_defs = list(rule_stats.values())
        
        for rule in rule_defs:
            rule_id = rule.get("id", rule.get("name", "Unknown"))
            evasion_risk = rule.get("evasion_risk", "UNKNOWN")
            risk_class = f"{evasion_risk.lower()}-risk"
            
            with st.expander(f"**{rule.get('name', rule_id)}** - {rule.get('severity', 'medium').upper()} - Evasion Risk: {evasion_risk}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Description:** {rule.get('description', 'N/A')}")
                    st.markdown(f"**Tactic:** {rule.get('tactic', 'N/A')}")
                    st.markdown(f"**Technique:** {rule.get('technique', 'N/A')}")
                    st.markdown(f"**Threshold:** {rule.get('threshold', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Alert Count:** {rule.get('alert_count', 0)}")
                    st.markdown(f"**Expected FP Rate:** {rule.get('false_positive_rate', 0)*100:.0f}%")
                    
                    if evasion_risk == "HIGH":
                        st.error(f"**Evasion Risk:** {evasion_risk}")
                    elif evasion_risk == "MEDIUM":
                        st.warning(f"**Evasion Risk:** {evasion_risk}")
                    else:
                        st.success(f"**Evasion Risk:** {evasion_risk}")
                
                st.markdown("---")
                st.markdown(f"**Rule Logic:** `{rule.get('logic_human', 'N/A')}`")
                st.markdown(f"**How to Evade:** {rule.get('evasion_method', 'N/A')}")
        
        # Summary stats
        st.markdown("---")
        st.markdown("### Rule Summary")
        
        if rule_stats:
            high_risk = len([r for r in rule_stats.values() if r.get("evasion_risk") == "HIGH"])
            med_risk = len([r for r in rule_stats.values() if r.get("evasion_risk") == "MEDIUM"])
            low_risk = len([r for r in rule_stats.values() if r.get("evasion_risk") == "LOW"])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("HIGH Evasion Risk", high_risk, help="Rules that are easily evaded")
            with col2:
                st.metric("MEDIUM Evasion Risk", med_risk)
            with col3:
                st.metric("LOW Evasion Risk", low_risk, help="Rules that are harder to evade")
    
    # Tab 5: Evasion Analysis
    with tab5:
        st.header("🥷 Signature Evasion Analysis")
        
        st.markdown("""
        This section analyzes how attackers can evade signature-based rules 
        and how LogLM catches these evasive attacks through behavioral analysis.
        """)
        
        manifest = data.get("manifest", {})
        ground_truth = data.get("ground_truth", {})
        findings = data.get("findings", [])
        
        # Evasion summary
        evasive_events = manifest.get("evasive_events", 0)
        detectable_events = manifest.get("detectable_events", 0)
        total_malicious = manifest.get("malicious_events", 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Malicious Events", total_malicious)
        with col2:
            st.metric("Detectable by Rules", detectable_events)
        with col3:
            st.metric("Evasive (Rules Miss)", evasive_events, 
                     delta=f"{evasive_events/total_malicious*100:.0f}% of attacks" if total_malicious > 0 else "0%")
        
        st.markdown("---")
        
        # Evasion techniques used
        evasion_techniques = manifest.get("evasion_techniques", [])
        if evasion_techniques:
            st.markdown("### Evasion Techniques Used in This Scenario")
            
            for i, technique in enumerate(evasion_techniques, 1):
                st.markdown(f"**{i}.** {technique}")
        
        st.markdown("---")
        
        # How LogLM catches evasive attacks
        st.markdown("### How LogLM Catches Evasive Attacks")
        
        st.markdown('<div class="evasion-box">', unsafe_allow_html=True)
        st.markdown("""
        **LogLM doesn't rely on signatures or thresholds.** Instead, it:
        
        1. **Analyzes flow patterns** - Even "low and slow" attacks have behavioral fingerprints
        2. **Recognizes malicious sequences** - The order of actions reveals intent
        3. **Uses embeddings** - Similar attacks cluster together, even if they look different on the surface
        4. **Trained on security data** - Knows what real attacks look like, not just statistical anomalies
        
        **Result:** LogLM catches attacks that rules miss, while maintaining high precision.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Evasive findings from LogLM
        evasive_findings = [f for f in findings if f.get("evasive", False)]
        
        if evasive_findings:
            st.markdown("### Evasive Attacks Detected by LogLM")
            st.markdown(f"**{len(evasive_findings)} evasive findings** that rules would have missed:")
            
            for finding in evasive_findings[:10]:
                with st.expander(f"🥷 {finding['title']}"):
                    st.markdown(f"**Description:** {finding['description']}")
                    st.markdown(f"**Confidence:** {finding['confidence']*100:.0f}%")
                    st.markdown(f"**Detection Method:** {finding.get('detection_method', 'behavioral_analysis')}")
                    if finding.get('evasion_technique'):
                        st.warning(f"**Evasion Technique Used:** {finding['evasion_technique']}")
                    st.markdown(f"**MITRE Technique:** {finding['mitre_predictions'][0]['technique_name']}")
        
        # Comparison table
        st.markdown("---")
        st.markdown("### Detection Comparison: Rules vs LogLM")
        
        comparison_data = [
            {
                "Attack Type": "Standard C2 Beaconing",
                "Rules": "✅ Detected",
                "LogLM": "✅ Detected",
                "Notes": "Both methods catch obvious patterns"
            },
            {
                "Attack Type": "DNS Tunneling (long subdomain)",
                "Rules": "✅ Detected",
                "LogLM": "✅ Detected",
                "Notes": "Signature matches long subdomain"
            },
            {
                "Attack Type": "Low-and-Slow DNS C2",
                "Rules": "❌ Missed",
                "LogLM": "✅ Detected",
                "Notes": "Short subdomains, A records, spread over hours"
            },
            {
                "Attack Type": "C2 via Legitimate CDN",
                "Rules": "❌ Missed",
                "LogLM": "✅ Detected",
                "Notes": "Uses AWS/Cloudflare IPs with jitter"
            },
            {
                "Attack Type": "Staged Exfiltration",
                "Rules": "❌ Missed",
                "LogLM": "✅ Detected",
                "Notes": "Small chunks under threshold"
            },
            {
                "Attack Type": "WMI/WinRM Lateral Movement",
                "Rules": "❌ Missed",
                "LogLM": "✅ Detected",
                "Notes": "Uses ports not monitored by RDP/SMB rules"
            },
        ]
        
        st.dataframe(pd.DataFrame(comparison_data), hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
