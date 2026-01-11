"""
DeepTempo AI SOC - Attack Flow Visualization Dashboard

A Streamlit-based visualization for LogLM attack flow analysis.
"""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import networkx as nx
from pyvis.network import Network
import tempfile
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="DeepTempo AI SOC - Attack Flow",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .critical {
        color: #d62728;
        font-weight: bold;
    }
    .high {
        color: #ff7f0e;
        font-weight: bold;
    }
    .medium {
        color: #ffbb78;
    }
    .phase-header {
        background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Sample attack data based on LogLM output
def get_sample_attack_data():
    """Generate sample attack data based on the LogLM output."""
    return {
        "attack_id": "ATK-2026-01-09-001",
        "title": "Multi-Stage Attack: Initial Access to Data Exfiltration",
        "severity": "CRITICAL",
        "start_time": "2026-01-09T02:08:00Z",
        "end_time": "2026-01-09T18:20:00Z",
        "phases": [
            {
                "phase": 1,
                "name": "Initial Compromise",
                "time": "02:08",
                "description": "Credential theft and initial access",
                "techniques": ["T1078 - Valid Accounts", "T1566 - Phishing"],
                "entities": ["workstation-042", "jsmith"]
            },
            {
                "phase": 2,
                "name": "C2 Establishment",
                "time": "02:08 - 02:12",
                "description": "Command and control infrastructure setup",
                "techniques": ["T1071.001 - Web Protocols", "T1573.001 - Encrypted Channel", "T1071.004 - DNS"],
                "entities": ["203.0.113.50", "*.data-sync.org", "*.cdn-update.net"]
            },
            {
                "phase": 3,
                "name": "Lateral Movement",
                "time": "02:12 - 10:41",
                "description": "Privilege escalation and network spread",
                "techniques": ["T1021.001 - RDP", "T1021.002 - SMB", "T1021.006 - WinRM"],
                "entities": ["workstation-055", "laptop-sales-03", "tjohnson", "klee", "mwilson", "agarcia"]
            },
            {
                "phase": 4,
                "name": "Critical Asset Compromise",
                "time": "02:40 - 06:16",
                "description": "Database and web server compromise",
                "techniques": ["T1048.003 - DNS Exfiltration", "T1041 - Exfiltration Over C2"],
                "entities": ["server-db-01", "server-web-02"]
            },
            {
                "phase": 5,
                "name": "Web Exploitation",
                "time": "04:17 - 18:20",
                "description": "Direct API exploitation attempts",
                "techniques": ["T1190 - Exploit Public-Facing Application"],
                "entities": ["198.51.100.10", "198.51.100.25", "10.0.2.10", "10.0.2.33"]
            }
        ],
        "nodes": [
            {"id": "workstation-042", "type": "endpoint", "label": "workstation-042\n(jsmith)", "risk": "high", "role": "entry_point"},
            {"id": "workstation-055", "type": "endpoint", "label": "workstation-055\n(tjohnson)", "risk": "medium", "role": "lateral"},
            {"id": "laptop-sales-03", "type": "endpoint", "label": "laptop-sales-03\n(klee)", "risk": "medium", "role": "lateral"},
            {"id": "server-db-01", "type": "server", "label": "server-db-01\n(DATABASE)", "risk": "critical", "role": "crown_jewel"},
            {"id": "server-web-02", "type": "server", "label": "server-web-02\n(WEB)", "risk": "critical", "role": "crown_jewel"},
            {"id": "203.0.113.50", "type": "external", "label": "203.0.113.50\n(C2 Server)", "risk": "critical", "role": "c2"},
            {"id": "198.51.100.10", "type": "external", "label": "198.51.100.10\n(Attacker)", "risk": "high", "role": "attacker"},
            {"id": "198.51.100.25", "type": "external", "label": "198.51.100.25\n(Attacker)", "risk": "high", "role": "attacker"},
            {"id": "data-sync.org", "type": "domain", "label": "*.data-sync.org\n(DNS Exfil)", "risk": "high", "role": "exfil"},
            {"id": "cdn-update.net", "type": "domain", "label": "*.cdn-update.net\n(DNS Exfil)", "risk": "high", "role": "exfil"},
        ],
        "edges": [
            {"source": "workstation-042", "target": "203.0.113.50", "type": "c2", "label": "HTTPS C2"},
            {"source": "workstation-042", "target": "data-sync.org", "type": "dns", "label": "DNS Tunnel"},
            {"source": "workstation-042", "target": "workstation-055", "type": "lateral", "label": "RDP"},
            {"source": "workstation-042", "target": "laptop-sales-03", "type": "lateral", "label": "SMB"},
            {"source": "workstation-042", "target": "server-db-01", "type": "lateral", "label": "SMB"},
            {"source": "server-db-01", "target": "data-sync.org", "type": "exfil", "label": "DNS Exfil"},
            {"source": "server-web-02", "target": "cdn-update.net", "type": "exfil", "label": "DNS Exfil"},
            {"source": "198.51.100.10", "target": "server-web-02", "type": "attack", "label": "HTTP Exploit"},
            {"source": "198.51.100.25", "target": "server-web-02", "type": "attack", "label": "HTTP Exploit"},
            {"source": "203.0.113.50", "target": "server-web-02", "type": "attack", "label": "Direct Attack"},
        ],
        "timeline_events": [
            {"time": "02:08", "event": "Initial compromise of workstation-042", "severity": "high", "phase": 1},
            {"time": "02:08", "event": "C2 beacon established to 203.0.113.50", "severity": "critical", "phase": 2},
            {"time": "02:10", "event": "DNS tunneling detected to data-sync.org", "severity": "high", "phase": 2},
            {"time": "02:12", "event": "RDP connection to workstation-055", "severity": "medium", "phase": 3},
            {"time": "02:15", "event": "SMB access to laptop-sales-03", "severity": "medium", "phase": 3},
            {"time": "02:40", "event": "Database server compromise (server-db-01)", "severity": "critical", "phase": 4},
            {"time": "03:45", "event": "Web server compromise (server-web-02)", "severity": "critical", "phase": 4},
            {"time": "04:17", "event": "External exploit attempt from 198.51.100.10", "severity": "high", "phase": 5},
            {"time": "06:16", "event": "Data exfiltration via DNS confirmed", "severity": "critical", "phase": 4},
            {"time": "10:41", "event": "Additional lateral movement detected", "severity": "medium", "phase": 3},
            {"time": "18:20", "event": "Continued web exploitation attempts", "severity": "high", "phase": 5},
        ],
        "mitre_techniques": [
            {"technique": "T1078", "name": "Valid Accounts", "tactic": "Initial Access", "confidence": 0.85, "count": 5},
            {"technique": "T1071.001", "name": "Web Protocols", "tactic": "Command and Control", "confidence": 0.89, "count": 15},
            {"technique": "T1071.004", "name": "DNS", "tactic": "Command and Control", "confidence": 0.78, "count": 12},
            {"technique": "T1573.001", "name": "Encrypted Channel", "tactic": "Command and Control", "confidence": 0.65, "count": 15},
            {"technique": "T1021.001", "name": "RDP", "tactic": "Lateral Movement", "confidence": 0.82, "count": 3},
            {"technique": "T1021.002", "name": "SMB/Windows Admin Shares", "tactic": "Lateral Movement", "confidence": 0.79, "count": 8},
            {"technique": "T1048.003", "name": "Exfiltration Over DNS", "tactic": "Exfiltration", "confidence": 0.61, "count": 6},
            {"technique": "T1190", "name": "Exploit Public-Facing App", "tactic": "Initial Access", "confidence": 0.75, "count": 4},
        ]
    }


def create_attack_graph(data):
    """Create an interactive network graph of the attack flow."""
    net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="black")
    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=200)
    
    # Color mapping
    type_colors = {
        "endpoint": "#2ca02c",  # Green
        "server": "#1f77b4",    # Blue
        "external": "#d62728",  # Red
        "domain": "#ff7f0e",    # Orange
    }
    
    role_shapes = {
        "entry_point": "diamond",
        "lateral": "dot",
        "crown_jewel": "star",
        "c2": "triangle",
        "attacker": "triangleDown",
        "exfil": "square",
    }
    
    # Add nodes
    for node in data["nodes"]:
        color = type_colors.get(node["type"], "#999999")
        size = 30 if node["risk"] == "critical" else 25 if node["risk"] == "high" else 20
        net.add_node(
            node["id"],
            label=node["label"],
            color=color,
            size=size,
            title=f"Type: {node['type']}\nRisk: {node['risk']}\nRole: {node['role']}"
        )
    
    # Edge colors
    edge_colors = {
        "c2": "#d62728",
        "dns": "#ff7f0e",
        "lateral": "#2ca02c",
        "exfil": "#9467bd",
        "attack": "#e377c2",
    }
    
    # Add edges
    for edge in data["edges"]:
        color = edge_colors.get(edge["type"], "#999999")
        net.add_edge(
            edge["source"],
            edge["target"],
            title=edge["label"],
            color=color,
            width=2,
            arrows="to"
        )
    
    return net


def create_timeline_chart(data):
    """Create a timeline visualization using Plotly."""
    events = data["timeline_events"]
    
    # Create DataFrame
    df = pd.DataFrame(events)
    
    # Map severity to colors
    severity_colors = {
        "critical": "#d62728",
        "high": "#ff7f0e",
        "medium": "#ffbb78",
        "low": "#2ca02c"
    }
    df["color"] = df["severity"].map(severity_colors)
    
    # Create timeline
    fig = go.Figure()
    
    for i, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[i],
            y=[row["phase"]],
            mode="markers+text",
            marker=dict(size=20, color=row["color"]),
            text=[row["time"]],
            textposition="top center",
            hovertext=row["event"],
            hoverinfo="text",
            name=row["event"][:30] + "..."
        ))
    
    fig.update_layout(
        title="Attack Timeline by Phase",
        xaxis_title="Event Sequence",
        yaxis_title="Attack Phase",
        yaxis=dict(tickmode="array", tickvals=[1, 2, 3, 4, 5], 
                   ticktext=["Initial Compromise", "C2 Establishment", "Lateral Movement", 
                            "Critical Asset Compromise", "Web Exploitation"]),
        showlegend=False,
        height=400
    )
    
    return fig


def create_sankey_diagram(data):
    """Create a Sankey diagram showing data flow."""
    # Define the flow
    labels = [
        "workstation-042",  # 0
        "server-db-01",     # 1
        "server-web-02",    # 2
        "C2 Server",        # 3
        "DNS Tunneling",    # 4
        "Data Exfiltration" # 5
    ]
    
    source = [0, 0, 0, 1, 2, 3, 4]
    target = [1, 2, 3, 4, 4, 5, 5]
    value = [10, 8, 15, 6, 4, 15, 10]
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=["#2ca02c", "#1f77b4", "#1f77b4", "#d62728", "#ff7f0e", "#9467bd"]
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=["rgba(44,160,44,0.4)", "rgba(44,160,44,0.4)", "rgba(214,39,40,0.4)",
                   "rgba(255,127,14,0.4)", "rgba(255,127,14,0.4)", "rgba(214,39,40,0.4)",
                   "rgba(255,127,14,0.4)"]
        )
    )])
    
    fig.update_layout(
        title="Data Exfiltration Flow",
        height=400
    )
    
    return fig


def create_mitre_heatmap(data):
    """Create a MITRE ATT&CK technique heatmap."""
    techniques = data["mitre_techniques"]
    df = pd.DataFrame(techniques)
    
    # Create heatmap
    fig = px.bar(
        df,
        x="name",
        y="count",
        color="confidence",
        color_continuous_scale="RdYlGn",
        title="MITRE ATT&CK Techniques Detected",
        labels={"name": "Technique", "count": "Event Count", "confidence": "Confidence"},
        hover_data=["technique", "tactic"]
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400
    )
    
    return fig


# Main app
def main():
    # Header
    st.markdown('<p class="main-header">🛡️ DeepTempo AI SOC</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Attack Flow Visualization Dashboard</p>', unsafe_allow_html=True)
    
    # Load data
    data = get_sample_attack_data()
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Attack Summary")
        st.markdown(f"**Attack ID:** {data['attack_id']}")
        st.markdown(f"**Severity:** <span class='critical'>{data['severity']}</span>", unsafe_allow_html=True)
        st.markdown(f"**Duration:** {data['start_time'][:10]}")
        
        st.divider()
        
        st.header("🎯 Key Metrics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Phases", len(data["phases"]))
            st.metric("Nodes", len(data["nodes"]))
        with col2:
            st.metric("Connections", len(data["edges"]))
            st.metric("Techniques", len(data["mitre_techniques"]))
        
        st.divider()
        
        st.header("⚙️ Options")
        show_graph = st.checkbox("Show Attack Graph", value=True)
        show_timeline = st.checkbox("Show Timeline", value=True)
        show_sankey = st.checkbox("Show Data Flow", value=True)
        show_mitre = st.checkbox("Show MITRE Techniques", value=True)
    
    # Main content
    # Phase overview
    st.header("📋 Attack Phases")
    
    phase_cols = st.columns(5)
    for i, phase in enumerate(data["phases"]):
        with phase_cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                <h4>Phase {phase['phase']}</h4>
                <p style="font-size: 0.9rem;">{phase['name']}</p>
                <p style="font-size: 0.8rem; opacity: 0.8;">{phase['time']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Attack Graph
    if show_graph:
        st.header("🕸️ Attack Graph")
        st.markdown("Interactive visualization of attack paths and entity relationships.")
        
        net = create_attack_graph(data)
        
        # Save and display
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
            net.save_graph(f.name)
            with open(f.name, "r") as html_file:
                html_content = html_file.read()
            st.components.v1.html(html_content, height=520)
            os.unlink(f.name)
        
        # Legend
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("🟢 **Endpoints**")
        with col2:
            st.markdown("🔵 **Servers**")
        with col3:
            st.markdown("🔴 **External/C2**")
        with col4:
            st.markdown("🟠 **Domains**")
        
        st.divider()
    
    # Timeline
    if show_timeline:
        st.header("⏱️ Attack Timeline")
        fig = create_timeline_chart(data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Event table
        with st.expander("📜 View All Events"):
            events_df = pd.DataFrame(data["timeline_events"])
            st.dataframe(events_df, use_container_width=True)
        
        st.divider()
    
    # Sankey Diagram
    if show_sankey:
        st.header("🔀 Data Exfiltration Flow")
        fig = create_sankey_diagram(data)
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
    
    # MITRE ATT&CK
    if show_mitre:
        st.header("🎯 MITRE ATT&CK Techniques")
        fig = create_mitre_heatmap(data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Technique table
        with st.expander("📊 View Technique Details"):
            tech_df = pd.DataFrame(data["mitre_techniques"])
            st.dataframe(tech_df, use_container_width=True)
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>Powered by <strong>DeepTempo LogLM</strong> | Attack Flow Visualization v0.1</p>
        <p style="font-size: 0.8rem;">Data generated from LogLM embeddings and MITRE ATT&CK predictions</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
