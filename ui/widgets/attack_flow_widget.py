"""Attack Flow Visualization Widget - Network graph visualization of attack flows."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QComboBox, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, QUrl
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    QWebEngineView = None
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from services.data_service import DataService


class AttackFlowWidget(QWidget):
    """Widget for visualizing attack flows as network graphs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_service = DataService()
        self.temp_html_file = None
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("<h2>Attack Flow Visualization</h2>")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Controls
        controls = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        controls.addWidget(refresh_btn)
        
        controls.addStretch()
        
        # View options
        self.show_graph_check = QCheckBox("Show Attack Graph")
        self.show_graph_check.setChecked(True)
        self.show_graph_check.stateChanged.connect(self._update_view)
        controls.addWidget(self.show_graph_check)
        
        self.show_timeline_check = QCheckBox("Show Timeline")
        self.show_timeline_check.setChecked(True)
        self.show_timeline_check.stateChanged.connect(self._update_view)
        controls.addWidget(self.show_timeline_check)
        
        layout.addLayout(controls)
        
        # Web view for graph
        if WEBENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
            self.web_view.setMinimumHeight(500)
            layout.addWidget(self.web_view)
        else:
            self.web_view = None
            web_label = QLabel("QWebEngineView not available. Please install PyQt6-WebEngine.")
            web_label.setWordWrap(True)
            layout.addWidget(web_label)
        
        # Info label
        self.info_label = QLabel("Loading attack flow data...")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        self.setLayout(layout)
    
    def _findings_to_attack_data(self, findings: List[Dict]) -> Dict:
        """Convert findings to attack visualization data structure."""
        # Extract unique entities
        hosts = set()
        external_ips = set()
        users = set()
        domains = set()
        
        # Track connections
        connections = []
        timeline_events = []
        technique_counts = {}
        
        for finding in findings:
            entity = finding.get("entity_context", {})
            
            # Extract entities
            if entity.get("hostname"):
                hosts.add(entity["hostname"])
            if entity.get("src_ip", ""):
                if not (entity["src_ip"].startswith("10.") or 
                       entity["src_ip"].startswith("192.168.") or
                       entity["src_ip"].startswith("172.")):
                    external_ips.add(entity["src_ip"])
            if entity.get("dst_ip"):
                if not (entity["dst_ip"].startswith("10.") or 
                       entity["dst_ip"].startswith("192.168.") or
                       entity["dst_ip"].startswith("172.")):
                    external_ips.add(entity["dst_ip"])
            if entity.get("user"):
                users.add(entity["user"])
            if entity.get("query_name"):
                # Extract domain from DNS query
                parts = entity["query_name"].split(".")
                if len(parts) >= 2:
                    domain = ".".join(parts[-2:])
                    domains.add(domain)
            
            # Track MITRE techniques
            for technique, confidence in finding.get("mitre_predictions", {}).items():
                if technique not in technique_counts:
                    technique_counts[technique] = {"count": 0, "total_confidence": 0}
                technique_counts[technique]["count"] += 1
                technique_counts[technique]["total_confidence"] += confidence
            
            # Create timeline event
            timestamp = finding.get("timestamp", datetime.now().isoformat())
            timeline_events.append({
                "time": timestamp[11:16] if len(timestamp) > 16 else "00:00",
                "event": f"{finding.get('data_source', 'unknown').upper()}: {entity.get('hostname', 'unknown')}",
                "severity": finding.get("severity", "medium"),
                "finding_id": finding.get("finding_id", ""),
                "anomaly_score": finding.get("anomaly_score", 0)
            })
        
        # Build nodes
        nodes = []
        
        for host in hosts:
            risk = "high" if "server" in host.lower() else "medium"
            role = "crown_jewel" if "server" in host.lower() else "endpoint"
            nodes.append({
                "id": host,
                "type": "server" if "server" in host.lower() else "endpoint",
                "label": host,
                "risk": risk,
                "role": role
            })
        
        for ip in list(external_ips)[:10]:  # Limit external IPs
            nodes.append({
                "id": ip,
                "type": "external",
                "label": f"{ip}\n(External)",
                "risk": "high",
                "role": "c2"
            })
        
        for domain in list(domains)[:5]:  # Limit domains
            nodes.append({
                "id": domain,
                "type": "domain",
                "label": f"*.{domain}",
                "risk": "medium",
                "role": "exfil"
            })
        
        # Build edges based on findings
        edges = []
        host_list = list(hosts)
        external_list = list(external_ips)
        domain_list = list(domains)
        
        # Connect hosts to external IPs (C2)
        if host_list and external_list:
            for host in host_list[:3]:
                for ext in external_list[:2]:
                    edges.append({
                        "source": host,
                        "target": ext,
                        "type": "c2",
                        "label": "C2 Beacon"
                    })
        
        # Connect hosts to domains (DNS)
        if host_list and domain_list:
            for host in host_list[:2]:
                for domain in domain_list[:2]:
                    edges.append({
                        "source": host,
                        "target": domain,
                        "type": "dns",
                        "label": "DNS Query"
                    })
        
        # Lateral movement between hosts
        if len(host_list) > 1:
            for i in range(min(len(host_list) - 1, 5)):
                edges.append({
                    "source": host_list[i],
                    "target": host_list[i + 1],
                    "type": "lateral",
                    "label": "Lateral Movement"
                })
        
        # Build MITRE techniques list
        mitre_techniques = []
        technique_names = {
            "T1071.001": ("Web Protocols", "Command and Control"),
            "T1071.004": ("DNS", "Command and Control"),
            "T1573.001": ("Encrypted Channel", "Command and Control"),
            "T1021.001": ("RDP", "Lateral Movement"),
            "T1021.002": ("SMB/Windows Admin Shares", "Lateral Movement"),
            "T1048.003": ("Exfiltration Over DNS", "Exfiltration"),
            "T1190": ("Exploit Public-Facing Application", "Initial Access"),
            "T1078": ("Valid Accounts", "Initial Access"),
            "T1059.001": ("PowerShell", "Execution"),
            "T1018": ("Remote System Discovery", "Discovery"),
        }
        
        for technique, stats in technique_counts.items():
            name, tactic = technique_names.get(technique, (technique, "Unknown"))
            mitre_techniques.append({
                "technique": technique,
                "name": name,
                "tactic": tactic,
                "confidence": round(stats["total_confidence"] / stats["count"], 3) if stats["count"] > 0 else 0,
                "count": stats["count"]
            })
        
        # Sort by count
        mitre_techniques.sort(key=lambda x: x["count"], reverse=True)
        
        # Determine phases based on techniques
        phases = []
        if any(t["tactic"] == "Initial Access" for t in mitre_techniques):
            phases.append({
                "phase": 1,
                "name": "Initial Access",
                "time": timeline_events[0]["time"] if timeline_events else "00:00",
                "description": "Initial compromise detected",
                "techniques": [t["technique"] for t in mitre_techniques if t["tactic"] == "Initial Access"],
                "entities": list(hosts)[:2]
            })
        
        if any(t["tactic"] == "Command and Control" for t in mitre_techniques):
            phases.append({
                "phase": 2,
                "name": "Command and Control",
                "time": "Ongoing",
                "description": "C2 infrastructure established",
                "techniques": [t["technique"] for t in mitre_techniques if t["tactic"] == "Command and Control"],
                "entities": list(external_ips)[:3]
            })
        
        if any(t["tactic"] == "Lateral Movement" for t in mitre_techniques):
            phases.append({
                "phase": 3,
                "name": "Lateral Movement",
                "time": "Ongoing",
                "description": "Network spread detected",
                "techniques": [t["technique"] for t in mitre_techniques if t["tactic"] == "Lateral Movement"],
                "entities": list(hosts)
            })
        
        if any(t["tactic"] == "Exfiltration" for t in mitre_techniques):
            phases.append({
                "phase": 4,
                "name": "Exfiltration",
                "time": "Ongoing",
                "description": "Data exfiltration detected",
                "techniques": [t["technique"] for t in mitre_techniques if t["tactic"] == "Exfiltration"],
                "entities": list(domains)[:3]
            })
        
        # Ensure at least some phases
        if not phases:
            phases = [
                {"phase": 1, "name": "Detection", "time": "00:00", "description": "Anomalies detected", 
                 "techniques": [], "entities": list(hosts)[:3]}
            ]
        
        return {
            "attack_id": f"ATK-{datetime.now().strftime('%Y-%m-%d')}-001",
            "title": "LogLM Attack Flow Analysis",
            "severity": "HIGH" if any(f.get("severity") == "high" for f in findings) else "MEDIUM",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "phases": phases,
            "nodes": nodes,
            "edges": edges,
            "timeline_events": timeline_events[:20],  # Limit to 20 events
            "mitre_techniques": mitre_techniques[:10]  # Limit to top 10
        }
    
    def _create_attack_graph_html(self, data: Dict) -> str:
        """Create HTML for attack graph visualization."""
        try:
            from pyvis.network import Network
            import tempfile
            
            net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="black")
            net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=200)
            
            # Color mapping
            type_colors = {
                "endpoint": "#2ca02c",  # Green
                "server": "#1f77b4",    # Blue
                "external": "#d62728",   # Red
                "domain": "#ff7f0e",     # Orange
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
            
            # Generate HTML
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                net.save_graph(f.name)
                with open(f.name, 'r') as html_file:
                    html_content = html_file.read()
                os.unlink(f.name)
                return html_content
        except ImportError:
            # Fallback to simple HTML if pyvis not available
            return self._create_simple_graph_html(data)
    
    def _create_simple_graph_html(self, data: Dict) -> str:
        """Create a simple HTML graph visualization without pyvis."""
        nodes_html = []
        for node in data["nodes"]:
            nodes_html.append(f'{{id: "{node["id"]}", label: "{node["label"]}", group: "{node["type"]}"}}')
        
        edges_html = []
        for edge in data["edges"]:
            edges_html.append(f'{{from: "{edge["source"]}", to: "{edge["target"]}", label: "{edge["label"]}"}}')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Attack Flow Graph</title>
            <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <style>
                body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
                #network {{ width: 100%; height: 500px; border: 1px solid #ccc; }}
            </style>
        </head>
        <body>
            <h3>Attack Flow Graph</h3>
            <div id="network"></div>
            <script type="text/javascript">
                var nodes = new vis.DataSet([{','.join(nodes_html)}]);
                var edges = new vis.DataSet([{','.join(edges_html)}]);
                var container = document.getElementById('network');
                var data = {{ nodes: nodes, edges: edges }};
                var options = {{
                    nodes: {{
                        shape: 'dot',
                        size: 20,
                        font: {{ size: 12 }}
                    }},
                    edges: {{
                        arrows: {{ to: {{ enabled: true }} }},
                        smooth: {{ type: 'continuous' }}
                    }},
                    physics: {{
                        enabled: true,
                        stabilization: {{ iterations: 200 }}
                    }}
                }};
                var network = new vis.Network(container, data, options);
            </script>
        </body>
        </html>
        """
        return html
    
    def refresh(self):
        """Refresh the attack flow visualization."""
        findings = self.data_service.get_findings()
        
        if not findings:
            self.info_label.setText("No findings available. Load findings data to visualize attack flows.")
            self.web_view.setHtml("<html><body><h3>No Data Available</h3><p>Please load findings data first.</p></body></html>")
            return
        
        # Convert findings to attack data
        try:
            from services.attack_data_loader import findings_to_attack_data
            attack_data = findings_to_attack_data(findings)
        except ImportError:
            # Fallback to local method
            attack_data = self._findings_to_attack_data(findings)
        
        # Update info
        info_text = (
            f"<b>Attack ID:</b> {attack_data['attack_id']}<br>"
            f"<b>Severity:</b> {attack_data['severity']}<br>"
            f"<b>Phases:</b> {len(attack_data['phases'])} | "
            f"<b>Nodes:</b> {len(attack_data['nodes'])} | "
            f"<b>Connections:</b> {len(attack_data['edges'])} | "
            f"<b>Techniques:</b> {len(attack_data['mitre_techniques'])}"
        )
        self.info_label.setText(info_text)
        
        # Create and display graph
        if self.web_view:
            if self.show_graph_check.isChecked():
                html_content = self._create_attack_graph_html(attack_data)
                self.web_view.setHtml(html_content)
            else:
                self.web_view.setHtml("<html><body><h3>Graph view disabled</h3></body></html>")
    
    def _update_view(self):
        """Update view based on checkboxes."""
        self.refresh()
    
    def __del__(self):
        """Cleanup temp files."""
        if self.temp_html_file and os.path.exists(self.temp_html_file):
            try:
                os.unlink(self.temp_html_file)
            except:
                pass

