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
- Attack graph visualization (mode-aware)
- Replay capability
- AI-generated explanations
- Entity-centric investigation
- Investigation workflow status
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
import networkx as nx
from pyvis.network import Network
import tempfile
import streamlit.components.v1 as components
import time

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
SCENARIO_DIR = DATA_DIR / "scenarios" / "default_attack"
MODE_FILE = DATA_DIR / "current_mode.txt"
WORKFLOW_FILE = DATA_DIR / "workflow_status.json"

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
        margin-bottom: 10px;
    }
    .explanation-box {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        font-size: 14px;
    }
    .entity-high-risk {
        background-color: #ffebee;
        padding: 5px 10px;
        border-radius: 3px;
    }
    .entity-medium-risk {
        background-color: #fff3e0;
        padding: 5px 10px;
        border-radius: 3px;
    }
    .entity-low-risk {
        background-color: #e8f5e9;
        padding: 5px 10px;
        border-radius: 3px;
    }
    .workflow-new { color: #2196f3; font-weight: bold; }
    .workflow-inprogress { color: #ff9800; font-weight: bold; }
    .workflow-resolved { color: #4caf50; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_data():
    """Load all scenario data."""
    data = {}
    
    try:
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
        
        # Load rules output
        rules_dir = SCENARIO_DIR / "rules_output"
        if rules_dir.exists():
            alerts_file = rules_dir / "alerts.json"
            if alerts_file.exists():
                with open(alerts_file) as f:
                    data["alerts"] = json.load(f)
            
            rule_stats_file = rules_dir / "rule_stats.json"
            if rule_stats_file.exists():
                with open(rule_stats_file) as f:
                    data["rule_stats"] = json.load(f)
            
            rule_defs_file = rules_dir / "rule_definitions.json"
            if rule_defs_file.exists():
                with open(rule_defs_file) as f:
                    data["rule_definitions"] = json.load(f)
        
        # Load LogLM output
        loglm_dir = SCENARIO_DIR / "loglm_output"
        if loglm_dir.exists():
            findings_file = loglm_dir / "findings.json"
            if findings_file.exists():
                with open(findings_file) as f:
                    data["findings"] = json.load(f)
            
            incidents_file = loglm_dir / "incidents.json"
            if incidents_file.exists():
                with open(incidents_file) as f:
                    data["incidents"] = json.load(f)
            
            technique_stats_file = loglm_dir / "technique_stats.json"
            if technique_stats_file.exists():
                with open(technique_stats_file) as f:
                    data["technique_stats"] = json.load(f)
        
        # Load evaluation results
        eval_file = SCENARIO_DIR / "evaluation_results.json"
        if eval_file.exists():
            with open(eval_file) as f:
                data["evaluation"] = json.load(f)
        
        # Load raw logs for replay
        raw_logs_dir = SCENARIO_DIR / "raw_logs"
        if raw_logs_dir.exists():
            conn_file = raw_logs_dir / "zeek_conn.json"
            if conn_file.exists():
                with open(conn_file) as f:
                    data["conn_logs"] = json.load(f)
            
            dns_file = raw_logs_dir / "zeek_dns.json"
            if dns_file.exists():
                with open(dns_file) as f:
                    data["dns_logs"] = json.load(f)
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
    
    return data


def load_workflow_status():
    """Load workflow status from file."""
    if WORKFLOW_FILE.exists():
        with open(WORKFLOW_FILE) as f:
            return json.load(f)
    return {}


def save_workflow_status(status):
    """Save workflow status to file."""
    WORKFLOW_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WORKFLOW_FILE, 'w') as f:
        json.dump(status, f, indent=2)


def get_current_mode():
    """Get the current SOC mode."""
    if MODE_FILE.exists():
        return MODE_FILE.read_text().strip()
    return "loglm"


def set_mode(mode):
    """Set the SOC mode."""
    MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
    MODE_FILE.write_text(mode)


def extract_entities(findings, alerts):
    """Extract all unique entities from findings and alerts."""
    entities = {}
    
    # Extract from LogLM findings
    for finding in findings:
        # Source IP
        src_ip = finding.get("source_ip")
        if src_ip:
            if src_ip not in entities:
                entities[src_ip] = {"type": "IP", "findings": [], "alerts": [], "first_seen": None, "last_seen": None}
            entities[src_ip]["findings"].append(finding["id"])
            ts = finding.get("timestamp")
            if ts:
                if not entities[src_ip]["first_seen"] or ts < entities[src_ip]["first_seen"]:
                    entities[src_ip]["first_seen"] = ts
                if not entities[src_ip]["last_seen"] or ts > entities[src_ip]["last_seen"]:
                    entities[src_ip]["last_seen"] = ts
        
        # Dest IP
        dest_ip = finding.get("dest_ip")
        if dest_ip:
            if dest_ip not in entities:
                entities[dest_ip] = {"type": "IP", "findings": [], "alerts": [], "first_seen": None, "last_seen": None}
            entities[dest_ip]["findings"].append(finding["id"])
            ts = finding.get("timestamp")
            if ts:
                if not entities[dest_ip]["first_seen"] or ts < entities[dest_ip]["first_seen"]:
                    entities[dest_ip]["first_seen"] = ts
                if not entities[dest_ip]["last_seen"] or ts > entities[dest_ip]["last_seen"]:
                    entities[dest_ip]["last_seen"] = ts
        
        # Hostname
        hostname = finding.get("hostname")
        if hostname:
            if hostname not in entities:
                entities[hostname] = {"type": "Host", "findings": [], "alerts": [], "first_seen": None, "last_seen": None}
            entities[hostname]["findings"].append(finding["id"])
            ts = finding.get("timestamp")
            if ts:
                if not entities[hostname]["first_seen"] or ts < entities[hostname]["first_seen"]:
                    entities[hostname]["first_seen"] = ts
                if not entities[hostname]["last_seen"] or ts > entities[hostname]["last_seen"]:
                    entities[hostname]["last_seen"] = ts
        
        # User
        user = finding.get("user")
        if user:
            if user not in entities:
                entities[user] = {"type": "User", "findings": [], "alerts": [], "first_seen": None, "last_seen": None}
            entities[user]["findings"].append(finding["id"])
    
    # Extract from alerts
    for alert in alerts:
        src_ip = alert.get("source_ip")
        if src_ip:
            if src_ip not in entities:
                entities[src_ip] = {"type": "IP", "findings": [], "alerts": [], "first_seen": None, "last_seen": None}
            entities[src_ip]["alerts"].append(alert["id"])
        
        dest_ip = alert.get("dest_ip")
        if dest_ip:
            if dest_ip not in entities:
                entities[dest_ip] = {"type": "IP", "findings": [], "alerts": [], "first_seen": None, "last_seen": None}
            entities[dest_ip]["alerts"].append(alert["id"])
        
        hostname = alert.get("hostname")
        if hostname:
            if hostname not in entities:
                entities[hostname] = {"type": "Host", "findings": [], "alerts": [], "first_seen": None, "last_seen": None}
            entities[hostname]["alerts"].append(alert["id"])
    
    # Calculate risk scores
    for entity_name, entity_data in entities.items():
        finding_count = len(entity_data["findings"])
        alert_count = len(entity_data["alerts"])
        
        # Risk based on finding involvement (LogLM findings are higher quality)
        if finding_count >= 5:
            entity_data["risk"] = "HIGH"
            entity_data["risk_score"] = min(100, finding_count * 10 + alert_count * 2)
        elif finding_count >= 2:
            entity_data["risk"] = "MEDIUM"
            entity_data["risk_score"] = finding_count * 10 + alert_count * 2
        else:
            entity_data["risk"] = "LOW"
            entity_data["risk_score"] = finding_count * 10 + alert_count * 2
    
    return entities


def create_mttd_chart(rules_mttd, loglm_mttd):
    """Create MTTD comparison bar chart."""
    phases = []
    rules_values = []
    loglm_values = []
    
    for key in sorted([k for k in rules_mttd.keys() if k.startswith("phase_")]):
        phase_name = rules_mttd[key]["phase_name"]
        phases.append(phase_name[:20] + "..." if len(phase_name) > 20 else phase_name)
        
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
        fill='toself',
        name='Rules-Only',
        line_color='#f44336',
        fillcolor='rgba(244, 67, 54, 0.3)'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=loglm_values + [loglm_values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        name='LogLM',
        line_color='#4caf50',
        fillcolor='rgba(76, 175, 80, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True,
        title="Detection Quality Comparison",
        height=400
    )
    
    return fig


def create_evasion_chart(rule_stats):
    """Create a chart showing rule evasion risk."""
    if not rule_stats:
        return None
    
    rules = list(rule_stats.values())
    names = [r.get("name", "Unknown")[:25] for r in rules]
    evasion_risks = [r.get("evasion_risk", "UNKNOWN") for r in rules]
    
    colors = []
    for risk in evasion_risks:
        if risk == "HIGH":
            colors.append("#f44336")
        elif risk == "MEDIUM":
            colors.append("#ff9800")
        else:
            colors.append("#4caf50")
    
    fig = go.Figure(data=[
        go.Bar(
            x=names,
            y=[1] * len(names),
            marker_color=colors,
            text=evasion_risks,
            textposition="inside"
        )
    ])
    
    fig.update_layout(
        title="Rule Evasion Risk Assessment",
        xaxis_title="Rule",
        yaxis_visible=False,
        height=300
    )
    
    return fig


def create_attack_graph_loglm(findings, incidents):
    """Create attack graph from LogLM findings."""
    net = Network(height="500px", width="100%", bgcolor="#1a1a2e", font_color="white")
    net.barnes_hut()
    
    nodes = set()
    edges = []
    
    for finding in findings:
        src = finding.get("hostname") or finding.get("source_ip")
        dst = finding.get("dest_ip")
        
        if src:
            nodes.add(src)
        if dst:
            nodes.add(dst)
        if src and dst:
            is_evasive = finding.get("evasive", False)
            edges.append((src, dst, finding.get("title", ""), is_evasive))
    
    # Add nodes with colors based on role
    for node in nodes:
        if "workstation" in str(node).lower():
            color = "#f44336"  # Red - entry point
            title = "Entry Point / Compromised Host"
        elif "server" in str(node).lower():
            if "db" in str(node).lower():
                color = "#9c27b0"  # Purple - crown jewels
                title = "Crown Jewel - Database Server"
            else:
                color = "#ff9800"  # Orange - lateral movement target
                title = "Server - Lateral Movement Target"
        elif node.startswith("203.") or node.startswith("198."):
            color = "#212121"  # Black - attacker
            title = "External Attacker / C2"
        else:
            color = "#607d8b"  # Gray - other
            title = "Network Entity"
        
        net.add_node(node, label=node, color=color, title=title, size=25)
    
    # Add edges
    for src, dst, label, is_evasive in edges:
        if is_evasive:
            net.add_edge(src, dst, title=f"[EVASIVE] {label}", dashes=True, color="#ff9800")
        else:
            net.add_edge(src, dst, title=label, color="#4caf50")
    
    return net


def create_attack_graph_rules(alerts):
    """Create fragmented attack graph from rules alerts."""
    net = Network(height="500px", width="100%", bgcolor="#1a1a2e", font_color="white")
    net.barnes_hut()
    
    nodes = set()
    edges = []
    
    # Only use a subset of alerts (rules miss many connections)
    true_positive_alerts = [a for a in alerts if not a.get("is_false_positive", False)][:20]
    
    for alert in true_positive_alerts:
        src = alert.get("hostname") or alert.get("source_ip")
        dst = alert.get("dest_ip")
        
        if src:
            nodes.add(src)
        if dst:
            nodes.add(dst)
        if src and dst:
            edges.append((src, dst, alert.get("rule_name", "")))
    
    for node in nodes:
        if "workstation" in str(node).lower():
            color = "#f44336"
        elif "server" in str(node).lower():
            color = "#ff9800"
        else:
            color = "#607d8b"
        
        net.add_node(node, label=node, color=color, size=20)
    
    for src, dst, label in edges:
        net.add_edge(src, dst, title=label, color="#f44336")
    
    return net


def main():
    """Main dashboard application."""
    
    st.title("⚔️ Tale of Two SOCs")
    st.markdown("*Comparing Rules-Only vs LogLM-Enhanced Security Operations*")
    
    # Load data
    data = load_data()
    
    if not data:
        st.error("No scenario data found. Please run the scenario generator first.")
        st.code("python scripts/generate_scenario.py\npython scripts/rules_detection.py\npython scripts/loglm_detection.py\npython scripts/evaluate.py")
        return
    
    # Sidebar
    st.sidebar.header("🎛️ Configuration")
    
    # Mode toggle
    current_mode = get_current_mode()
    st.sidebar.markdown("### Claude Integration Mode")
    mode = st.sidebar.radio(
        "Select SOC Mode for Claude:",
        ["loglm", "rules"],
        index=0 if current_mode == "loglm" else 1,
        format_func=lambda x: "🟢 LogLM-Enhanced" if x == "loglm" else "🔴 Rules-Only",
        help="This controls which tools Claude has access to via MCP"
    )
    
    if mode != current_mode:
        set_mode(mode)
        st.sidebar.success(f"Mode changed to {mode}. Restart Claude to apply.")
    
    st.sidebar.markdown("---")
    
    # Scenario info
    manifest = data.get("manifest", {})
    st.sidebar.markdown("### 📊 Scenario Info")
    st.sidebar.markdown(f"**Name:** {manifest.get('name', 'Unknown')}")
    st.sidebar.markdown(f"**Duration:** {manifest.get('duration_hours', 0)} hours")
    st.sidebar.markdown(f"**Total Events:** {manifest.get('total_events', 0):,}")
    st.sidebar.markdown(f"**Malicious:** {manifest.get('malicious_events', 0)}")
    st.sidebar.markdown(f"**Evasive:** {manifest.get('evasive_events', 0)}")
    st.sidebar.markdown(f"**FP Triggers:** {manifest.get('false_positive_triggers', 0)}")
    
    # Main content - tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Overview",
        "🔍 Findings",
        "🏢 Entities",
        "📋 Workflow",
        "⏱️ MTTD",
        "📜 Rules",
        "🥷 Evasion",
        "🕸️ Attack Graph",
        "▶️ Replay"
    ])
    
    # Get evaluation data
    eval_data = data.get("evaluation", {})
    rules_eval = eval_data.get("rules_only", {})
    loglm_eval = eval_data.get("loglm", {})
    findings = data.get("findings", [])
    alerts = data.get("alerts", [])
    
    # Tab 1: Comparison Overview
    with tab1:
        st.header("Side-by-Side Comparison")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Alert Reduction",
                f"{eval_data.get('comparison', {}).get('alert_reduction', 0)*100:.0f}%",
                help="LogLM reduces alert volume while maintaining coverage"
            )
        
        with col2:
            st.metric(
                "Precision Improvement",
                f"+{eval_data.get('comparison', {}).get('precision_improvement', 0)*100:.1f}%",
                help="LogLM has much higher precision (fewer false positives)"
            )
        
        with col3:
            st.metric(
                "F1 Score Improvement",
                f"+{eval_data.get('comparison', {}).get('f1_improvement', 0):.3f}",
                help="Overall detection quality improvement"
            )
        
        with col4:
            phases_rules = rules_eval.get("mttd", {}).get("phases_detected", 0)
            phases_loglm = loglm_eval.get("mttd", {}).get("phases_detected", 0)
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
            st.markdown("### 🔴 Rules-Only SOC")
            rules_metrics = rules_eval.get("confusion_matrix", {})
            st.markdown(f"**Alerts Generated:** {rules_metrics.get('true_positives', 0) + rules_metrics.get('false_positives', 0)}")
            st.markdown(f"**True Positives:** {rules_metrics.get('true_positives', 0)}")
            st.markdown(f"**False Positives:** {rules_metrics.get('false_positives', 0)}")
            st.markdown(f"**Precision:** {rules_eval.get('metrics', {}).get('precision', 0)*100:.1f}%")
            st.markdown(f"**Recall:** {rules_eval.get('metrics', {}).get('recall', 0)*100:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="loglm-box">', unsafe_allow_html=True)
            st.markdown("### 🟢 LogLM-Enhanced SOC")
            loglm_metrics = loglm_eval.get("confusion_matrix", {})
            st.markdown(f"**Findings Generated:** {loglm_metrics.get('true_positives', 0) + loglm_metrics.get('false_positives', 0)}")
            st.markdown(f"**True Positives:** {loglm_metrics.get('true_positives', 0)}")
            st.markdown(f"**False Positives:** {loglm_metrics.get('false_positives', 0)}")
            st.markdown(f"**Precision:** {loglm_eval.get('metrics', {}).get('precision', 0)*100:.1f}%")
            st.markdown(f"**Recall:** {loglm_eval.get('metrics', {}).get('recall', 0)*100:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Radar chart
        if rules_eval.get("metrics") and loglm_eval.get("metrics"):
            radar_chart = create_metrics_comparison_chart(
                rules_eval["metrics"],
                loglm_eval["metrics"]
            )
            st.plotly_chart(radar_chart, use_container_width=True)
    
    # Tab 2: Findings with AI Explanations
    with tab2:
        st.header("🔍 LogLM Findings with AI Explanations")
        
        st.markdown("""
        Each finding includes an **AI-generated explanation** that describes:
        - What was observed
        - Why it's suspicious/malicious
        - Connection to the broader attack narrative
        """)
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            severity_filter = st.multiselect(
                "Filter by Severity",
                ["critical", "high", "medium", "low"],
                default=["critical", "high", "medium"]
            )
        with col2:
            evasive_filter = st.selectbox(
                "Evasive Attacks",
                ["All", "Evasive Only", "Non-Evasive Only"]
            )
        with col3:
            search_term = st.text_input("Search findings", "")
        
        # Filter findings
        filtered_findings = findings
        if severity_filter:
            filtered_findings = [f for f in filtered_findings if f.get("severity") in severity_filter]
        if evasive_filter == "Evasive Only":
            filtered_findings = [f for f in filtered_findings if f.get("evasive")]
        elif evasive_filter == "Non-Evasive Only":
            filtered_findings = [f for f in filtered_findings if not f.get("evasive")]
        if search_term:
            filtered_findings = [f for f in filtered_findings if search_term.lower() in json.dumps(f).lower()]
        
        st.markdown(f"**Showing {len(filtered_findings)} of {len(findings)} findings**")
        
        # Display findings with explanations
        for finding in filtered_findings[:50]:  # Limit to 50 for performance
            severity = finding.get("severity", "medium")
            severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
            evasive_badge = " 🥷 EVASIVE" if finding.get("evasive") else ""
            
            with st.expander(f"{severity_emoji} {finding.get('title', 'Unknown')}{evasive_badge}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**ID:** {finding.get('id')}")
                    st.markdown(f"**Timestamp:** {finding.get('timestamp')}")
                    st.markdown(f"**Severity:** {severity.upper()}")
                    st.markdown(f"**Confidence:** {finding.get('confidence', 0)*100:.0f}%")
                    
                    # MITRE info
                    mitre = finding.get("mitre_predictions", [{}])[0]
                    st.markdown(f"**MITRE Technique:** {mitre.get('technique_name', 'N/A')} ({mitre.get('technique_id', 'N/A')})")
                    st.markdown(f"**Tactic:** {mitre.get('tactic', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Source:** {finding.get('hostname') or finding.get('source_ip', 'N/A')}")
                    st.markdown(f"**Destination:** {finding.get('dest_ip', 'N/A')}")
                    st.markdown(f"**Port:** {finding.get('dest_port', 'N/A')}")
                    if finding.get("evasive"):
                        st.markdown(f"**Evasion Technique:** {finding.get('evasion_technique', 'N/A')}")
                
                # AI Explanation
                explanation = finding.get("explanation", finding.get("description", "No explanation available."))
                st.markdown("---")
                st.markdown("### 🤖 AI-Generated Explanation")
                st.markdown(f'<div class="explanation-box">{explanation}</div>', unsafe_allow_html=True)
    
    # Tab 3: Entity-Centric Investigation
    with tab3:
        st.header("🏢 Entity-Centric Investigation")
        
        st.markdown("""
        Investigate by entity (IP, hostname, user). Click on any entity to see all related findings and alerts.
        """)
        
        # Extract entities
        entities = extract_entities(findings, alerts)
        
        # Sort by risk score
        sorted_entities = sorted(entities.items(), key=lambda x: x[1].get("risk_score", 0), reverse=True)
        
        # Entity search
        entity_search = st.text_input("Search entities", "")
        if entity_search:
            sorted_entities = [(k, v) for k, v in sorted_entities if entity_search.lower() in k.lower()]
        
        # Entity type filter
        entity_types = list(set(v["type"] for k, v in sorted_entities))
        selected_types = st.multiselect("Filter by type", entity_types, default=entity_types)
        sorted_entities = [(k, v) for k, v in sorted_entities if v["type"] in selected_types]
        
        st.markdown(f"**Found {len(sorted_entities)} entities**")
        
        # Display as table
        entity_data = []
        for entity_name, entity_info in sorted_entities[:100]:
            entity_data.append({
                "Entity": entity_name,
                "Type": entity_info["type"],
                "Risk": entity_info["risk"],
                "Risk Score": entity_info["risk_score"],
                "Findings": len(entity_info["findings"]),
                "Alerts": len(entity_info["alerts"]),
                "First Seen": entity_info.get("first_seen", "N/A"),
                "Last Seen": entity_info.get("last_seen", "N/A")
            })
        
        if entity_data:
            df = pd.DataFrame(entity_data)
            
            # Color code by risk
            def highlight_risk(row):
                if row["Risk"] == "HIGH":
                    return ["background-color: #ffebee"] * len(row)
                elif row["Risk"] == "MEDIUM":
                    return ["background-color: #fff3e0"] * len(row)
                else:
                    return ["background-color: #e8f5e9"] * len(row)
            
            st.dataframe(df.style.apply(highlight_risk, axis=1), hide_index=True, use_container_width=True)
        
        # Entity detail view
        st.markdown("---")
        st.markdown("### Entity Detail View")
        
        selected_entity = st.selectbox(
            "Select an entity to investigate",
            [e[0] for e in sorted_entities[:50]] if sorted_entities else ["No entities found"]
        )
        
        if selected_entity and selected_entity in entities:
            entity_info = entities[selected_entity]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Risk Level", entity_info["risk"])
            with col2:
                st.metric("Related Findings", len(entity_info["findings"]))
            with col3:
                st.metric("Related Alerts", len(entity_info["alerts"]))
            
            # Show related findings
            if entity_info["findings"]:
                st.markdown("#### Related Findings")
                related_findings = [f for f in findings if f["id"] in entity_info["findings"]]
                for f in related_findings[:10]:
                    st.markdown(f"- **{f.get('title')}** ({f.get('severity')}) - {f.get('timestamp')}")
    
    # Tab 4: Investigation Workflow
    with tab4:
        st.header("📋 Investigation Workflow")
        
        st.markdown("""
        Track the status of your investigations. Mark findings as reviewed, true positive, or false positive.
        """)
        
        # Load workflow status
        workflow_status = load_workflow_status()
        
        # Summary metrics
        total = len(findings)
        reviewed = len([f for f in findings if workflow_status.get(f["id"], {}).get("status") == "resolved"])
        in_progress = len([f for f in findings if workflow_status.get(f["id"], {}).get("status") == "in_progress"])
        new_count = total - reviewed - in_progress
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Findings", total)
        with col2:
            st.metric("New", new_count)
        with col3:
            st.metric("In Progress", in_progress)
        with col4:
            st.metric("Resolved", reviewed)
        
        # Progress bar
        progress = reviewed / total if total > 0 else 0
        st.progress(progress, text=f"Triage Progress: {progress*100:.0f}%")
        
        st.markdown("---")
        
        # Filter by status
        status_filter = st.radio(
            "Filter by status",
            ["All", "New", "In Progress", "Resolved"],
            horizontal=True
        )
        
        # Display findings with workflow controls
        for finding in findings[:30]:
            finding_id = finding["id"]
            current_status = workflow_status.get(finding_id, {})
            status = current_status.get("status", "new")
            verdict = current_status.get("verdict", "")
            
            # Apply filter
            if status_filter == "New" and status != "new":
                continue
            elif status_filter == "In Progress" and status != "in_progress":
                continue
            elif status_filter == "Resolved" and status != "resolved":
                continue
            
            severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(finding.get("severity"), "⚪")
            status_emoji = {"new": "🆕", "in_progress": "🔄", "resolved": "✅"}.get(status, "❓")
            
            with st.expander(f"{status_emoji} {severity_emoji} {finding.get('title', 'Unknown')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**ID:** {finding_id}")
                    st.markdown(f"**Severity:** {finding.get('severity', 'unknown').upper()}")
                    st.markdown(f"**Description:** {finding.get('description', 'N/A')[:200]}...")
                
                with col2:
                    # Status selector
                    new_status = st.selectbox(
                        "Status",
                        ["new", "in_progress", "resolved"],
                        index=["new", "in_progress", "resolved"].index(status),
                        key=f"status_{finding_id}"
                    )
                    
                    # Verdict selector
                    new_verdict = st.selectbox(
                        "Verdict",
                        ["", "true_positive", "false_positive", "needs_review"],
                        index=["", "true_positive", "false_positive", "needs_review"].index(verdict) if verdict in ["", "true_positive", "false_positive", "needs_review"] else 0,
                        key=f"verdict_{finding_id}"
                    )
                    
                    # Save button
                    if st.button("Save", key=f"save_{finding_id}"):
                        workflow_status[finding_id] = {
                            "status": new_status,
                            "verdict": new_verdict,
                            "updated_at": datetime.now().isoformat()
                        }
                        save_workflow_status(workflow_status)
                        st.success("Saved!")
                        st.rerun()
    
    # Tab 5: MTTD Analysis
    with tab5:
        st.header("⏱️ Mean Time to Detect (MTTD) Analysis")
        
        rules_mttd = rules_eval.get("mttd", {})
        loglm_mttd = loglm_eval.get("mttd", {})
        
        if rules_mttd and loglm_mttd:
            # Summary metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Rules-Only Overall MTTD",
                    f"{rules_mttd.get('overall_mttd_minutes', 0):.1f} min",
                    help="Average time to detect across all phases"
                )
            with col2:
                st.metric(
                    "LogLM Overall MTTD",
                    f"{loglm_mttd.get('overall_mttd_minutes', 0):.1f} min",
                    help="Average time to detect across all phases"
                )
            
            # MTTD chart
            mttd_chart = create_mttd_chart(rules_mttd, loglm_mttd)
            st.plotly_chart(mttd_chart, use_container_width=True)
            
            # Detailed table
            st.markdown("### Phase-by-Phase Detection")
            
            phase_data = []
            for key in sorted([k for k in rules_mttd.keys() if k.startswith("phase_")]):
                rules_phase = rules_mttd[key]
                loglm_phase = loglm_mttd.get(key, {})
                
                phase_data.append({
                    "Phase": rules_phase["phase_name"],
                    "Rules-Only": f"{rules_phase['mttd_minutes']:.1f} min" if rules_phase["detected"] else "❌ NOT DETECTED",
                    "LogLM": f"{loglm_phase.get('mttd_minutes', 0):.1f} min" if loglm_phase.get("detected") else "❌ NOT DETECTED"
                })
            
            st.dataframe(pd.DataFrame(phase_data), hide_index=True, use_container_width=True)
    
    # Tab 6: Rule Analysis
    with tab6:
        st.header("📜 Detection Rule Analysis")
        
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
    
    # Tab 7: Evasion Analysis
    with tab7:
        st.header("🥷 Signature Evasion Analysis")
        
        st.markdown("""
        This section analyzes how attackers can evade signature-based rules 
        and how LogLM catches these evasive attacks through behavioral analysis.
        """)
        
        manifest = data.get("manifest", {})
        
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
        
        # Evasion techniques
        st.markdown("### Evasion Techniques Used")
        
        evasion_data = [
            {"Technique": "Low-and-Slow DNS C2", "Description": "Short subdomains, A records, spread over hours", "Rules": "❌ Missed", "LogLM": "✅ Detected"},
            {"Technique": "HTTPS C2 via CDN", "Description": "Uses AWS/Cloudflare IPs with timing jitter", "Rules": "❌ Missed", "LogLM": "✅ Detected"},
            {"Technique": "Staged Exfiltration", "Description": "Small chunks (50-200KB) under threshold", "Rules": "❌ Missed", "LogLM": "✅ Detected"},
            {"Technique": "Living-off-the-Land", "Description": "WMI/WinRM instead of RDP/SMB", "Rules": "❌ Missed", "LogLM": "✅ Detected"},
            {"Technique": "Timing Evasion", "Description": "Varied intervals to avoid beaconing detection", "Rules": "❌ Missed", "LogLM": "✅ Detected"},
        ]
        
        st.dataframe(pd.DataFrame(evasion_data), hide_index=True, use_container_width=True)
    
    # Tab 8: Attack Graph
    with tab8:
        st.header("🕸️ Attack Graph Visualization")
        
        st.markdown("""
        This visualization shows how each SOC approach sees the attack.
        **LogLM provides a complete, correlated view** while **Rules-Only shows fragmented alerts**.
        """)
        
        graph_mode = st.radio(
            "Select View:",
            ["LogLM (Complete Attack Graph)", "Rules-Only (Fragmented View)"],
            horizontal=True
        )
        
        if graph_mode == "LogLM (Complete Attack Graph)":
            st.markdown('<div class="loglm-box">', unsafe_allow_html=True)
            st.markdown("### 🟢 LogLM Attack Graph - Complete Visibility")
            st.markdown('</div>', unsafe_allow_html=True)
            
            incidents = data.get("incidents", [])
            net = create_attack_graph_loglm(findings, incidents)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                net.save_graph(f.name)
                with open(f.name, 'r') as html_file:
                    html_content = html_file.read()
                components.html(html_content, height=550)
        else:
            st.markdown('<div class="rules-box">', unsafe_allow_html=True)
            st.markdown("### 🔴 Rules-Only View - Fragmented Alerts")
            st.markdown('</div>', unsafe_allow_html=True)
            
            net = create_attack_graph_rules(alerts)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                net.save_graph(f.name)
                with open(f.name, 'r') as html_file:
                    html_content = html_file.read()
                components.html(html_content, height=550)
    
    # Tab 9: Replay
    with tab9:
        st.header("▶️ Scenario Replay")
        
        st.markdown("""
        Replay the attack scenario to see how events unfold over time.
        This helps understand the attack timeline and detection timing.
        """)
        
        st.markdown("### Replay Controls")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            replay_speed = st.select_slider(
                "Replay Speed",
                options=["0.5x", "1x", "2x", "5x", "10x", "Instant"],
                value="2x"
            )
        with col2:
            replay_mode = st.radio(
                "Show",
                ["All Events", "Malicious Only", "Findings Only"],
                horizontal=True
            )
        with col3:
            st.markdown("**Status**")
            if "replay_running" not in st.session_state:
                st.session_state.replay_running = False
        
        # Replay buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("▶️ Start Replay", use_container_width=True):
                st.session_state.replay_running = True
        with col2:
            if st.button("⏸️ Pause", use_container_width=True):
                st.session_state.replay_running = False
        with col3:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.replay_running = False
                st.session_state.replay_index = 0
        
        st.markdown("---")
        
        # Get events for replay
        conn_logs = data.get("conn_logs", [])
        dns_logs = data.get("dns_logs", [])
        all_logs = sorted(conn_logs + dns_logs, key=lambda x: x.get("ts", ""))
        
        ground_truth = data.get("ground_truth", {})
        events_info = ground_truth.get("events", {})
        
        # Filter based on mode
        if replay_mode == "Malicious Only":
            all_logs = [e for e in all_logs if events_info.get(e.get("id"), {}).get("label") == "malicious"]
        elif replay_mode == "Findings Only":
            finding_event_ids = set()
            for f in findings:
                finding_event_ids.update(f.get("event_ids", []))
            all_logs = [e for e in all_logs if e.get("id") in finding_event_ids]
        
        st.markdown(f"**Total events to replay:** {len(all_logs)}")
        
        # Progress slider
        if "replay_index" not in st.session_state:
            st.session_state.replay_index = 0
        
        replay_index = st.slider(
            "Timeline Position",
            0, max(1, len(all_logs) - 1),
            st.session_state.replay_index,
            key="replay_slider"
        )
        st.session_state.replay_index = replay_index
        
        # Show current event
        if all_logs and replay_index < len(all_logs):
            current_event = all_logs[replay_index]
            event_info = events_info.get(current_event.get("id"), {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Current Event")
                st.json({
                    "id": current_event.get("id"),
                    "timestamp": current_event.get("ts"),
                    "source": current_event.get("id.orig_h") or current_event.get("hostname"),
                    "destination": current_event.get("id.resp_h") or current_event.get("query"),
                    "port": current_event.get("id.resp_p"),
                    "service": current_event.get("service") or current_event.get("qtype_name")
                })
            
            with col2:
                st.markdown("### Event Classification")
                if event_info.get("label") == "malicious":
                    st.error(f"🔴 MALICIOUS - {event_info.get('description', 'Unknown')}")
                    st.markdown(f"**Attack Phase:** {event_info.get('attack_phase', 'N/A')}")
                    st.markdown(f"**Technique:** {event_info.get('technique', 'N/A')}")
                    if event_info.get("evasive"):
                        st.warning(f"🥷 Evasive: {event_info.get('evasion_technique', 'Unknown')}")
                else:
                    st.success("🟢 BENIGN")
        
        st.markdown("---")
        st.markdown("### How to Use Replay")
        st.markdown("""
        1. **Select replay speed** - How fast to advance through events
        2. **Choose what to show** - All events, malicious only, or findings only
        3. **Use the slider** - Manually scrub through the timeline
        4. **Watch the classification** - See how each event is labeled
        
        **To load custom scenarios:**
        1. Place your logs in `data/scenarios/your_scenario/raw_logs/`
        2. Create a `manifest.json` with scenario metadata
        3. Run the detection pipelines
        4. Select your scenario from the sidebar (coming soon)
        """)


if __name__ == "__main__":
    main()
