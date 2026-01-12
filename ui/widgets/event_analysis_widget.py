"""Event analysis widget with Claude integration."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QTextEdit, QTabWidget,
    QWidget, QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from typing import Dict, List, Optional
import json
import numpy as np

from services.claude_service import ClaudeService
from services.data_service import DataService
from services.timeline_service import TimelineService
from ui.utils.auto_resize import TableAutoResize, ButtonSizePolicy


def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot_product / (norm1 * norm2))


class AnalysisWorker(QThread):
    """Worker thread for Claude analysis."""
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, event: Dict, finding: Optional[Dict], all_events: List[Dict]):
        super().__init__()
        self.event = event
        self.finding = finding
        self.all_events = all_events
    
    def run(self):
        """Run Claude analysis."""
        try:
            claude_service = ClaudeService()
            if not claude_service.has_api_key():
                self.error.emit("Claude API key not configured. Please set it in Settings.")
                return
            
            # Build analysis prompt
            event_text = json.dumps(self.event, indent=2)
            finding_text = ""
            if self.finding:
                finding_copy = self.finding.copy()
                # Remove embedding (too large)
                if 'embedding' in finding_copy:
                    finding_copy['embedding'] = f"[{len(finding_copy['embedding'])}-dimensional vector]"
                finding_text = json.dumps(finding_copy, indent=2)
            
            system_prompt = (
                "You are a security analyst examining a timeline event. "
                "Provide a comprehensive analysis including:\n"
                "- Threat assessment and severity evaluation\n"
                "- Behavioral patterns and indicators\n"
                "- MITRE ATT&CK technique analysis\n"
                "- Potential attack context\n"
                "- Recommended investigation steps\n"
                "- Affected entities and their risk level"
            )
            
            message = (
                f"Analyze this security event in detail:\n\n"
                f"Event Data:\n{event_text}\n\n"
            )
            
            if finding_text:
                message += f"Related Finding:\n{finding_text}\n\n"
            
            message += (
                "Provide a comprehensive analysis including threat assessment, "
                "behavioral patterns, MITRE technique analysis, potential attack context, "
                "recommended investigation steps, and affected entities."
            )
            
            analysis = claude_service.chat(
                message,
                system_prompt=system_prompt,
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096
            )
            
            self.finished.emit(analysis)
        except Exception as e:
            self.error.emit(f"Error during analysis: {str(e)}")


class EventAnalysisWidget(QDialog):
    """Widget for analyzing events with Claude integration."""
    
    # Material Design severity colors
    SEVERITY_COLORS = {
        'critical': QColor('#D32F2F'),  # Red
        'high': QColor('#F57C00'),      # Orange
        'medium': QColor('#FBC02D'),    # Yellow
        'low': QColor('#388E3C')        # Green
    }
    
    def __init__(self, event: Dict, all_events: List[Dict], parent=None):
        super().__init__(parent)
        self.event = event
        self.all_events = all_events
        self.data_service = DataService()
        self.timeline_service = TimelineService()
        
        # Get finding if available
        self.finding = None
        finding_id = event.get('finding_id')
        if finding_id:
            self.finding = self.data_service.get_finding(finding_id)
        
        self.setWindowTitle(f"Event Analysis: {event.get('message', 'Unknown Event')[:50]}")
        self.setMinimumSize(1200, 800)
        
        self._setup_ui()
        self._analyze_event()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        event_info = QLabel(
            f"<b>Event:</b> {self.event.get('message', 'Unknown')}<br>"
            f"<b>Timestamp:</b> {self.event.get('timestamp', 'N/A')}<br>"
            f"<b>Severity:</b> {self.event.get('severity', 'N/A')}"
        )
        header_layout.addWidget(event_info)
        header_layout.addStretch()
        
        close_btn = QPushButton("Close")
        ButtonSizePolicy.make_compact(close_btn, min_width=70)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Claude Analysis tab
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout()
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setPlaceholderText("Claude analysis will appear here...")
        analysis_layout.addWidget(self.analysis_text)
        
        refresh_btn = QPushButton("Refresh Analysis")
        ButtonSizePolicy.make_flexible(refresh_btn, min_width=130)
        refresh_btn.clicked.connect(self._analyze_event)
        analysis_layout.addWidget(refresh_btn)
        
        analysis_tab.setLayout(analysis_layout)
        self.tabs.addTab(analysis_tab, "Claude Analysis")
        
        # Similar Events tab
        similar_tab = QWidget()
        similar_layout = QVBoxLayout()
        
        self.similar_table = QTableWidget()
        self.similar_table.setColumnCount(6)
        self.similar_table.setHorizontalHeaderLabels([
            "Timestamp", "Message", "Similarity", "Severity", "Source IP", "Destination IP"
        ])
        # Configure intelligent auto-resizing
        from PyQt6.QtWidgets import QHeaderView
        TableAutoResize.configure(
            self.similar_table,
            content_fit_columns=[2, 3],  # Similarity, Severity (auto-fit)
            stretch_columns=[1],  # Message (stretches to fill)
            interactive_columns=[0, 4, 5]  # Timestamp, Source IP, Destination IP (user can resize)
        )
        self.similar_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.similar_table.verticalHeader().setVisible(True)
        self.similar_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        similar_layout.addWidget(self.similar_table)
        
        similar_tab.setLayout(similar_layout)
        self.tabs.addTab(similar_tab, "Similar Events")
        
        # Correlated Events tab
        correlated_tab = QWidget()
        correlated_layout = QVBoxLayout()
        
        self.correlated_table = QTableWidget()
        self.correlated_table.setColumnCount(6)
        self.correlated_table.setHorizontalHeaderLabels([
            "Timestamp", "Message", "Correlation Type", "Severity", "Source IP", "Destination IP"
        ])
        # Configure intelligent auto-resizing
        TableAutoResize.configure(
            self.correlated_table,
            content_fit_columns=[2, 3],  # Correlation Type, Severity (auto-fit)
            stretch_columns=[1],  # Message (stretches to fill)
            interactive_columns=[0, 4, 5]  # Timestamp, Source IP, Destination IP (user can resize)
        )
        self.correlated_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.correlated_table.verticalHeader().setVisible(True)
        self.correlated_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        correlated_layout.addWidget(self.correlated_table)
        
        correlated_tab.setLayout(correlated_layout)
        self.tabs.addTab(correlated_tab, "Correlated Events")
        
        # Affected Entities tab
        entities_tab = QWidget()
        entities_layout = QVBoxLayout()
        
        # IPs section
        ips_group = QGroupBox("Affected IP Addresses")
        ips_layout = QVBoxLayout()
        
        self.ips_table = QTableWidget()
        self.ips_table.setColumnCount(4)
        self.ips_table.setHorizontalHeaderLabels([
            "IP Address", "Type", "Event Count", "First Seen"
        ])
        # Configure intelligent auto-resizing
        TableAutoResize.configure(
            self.ips_table,
            content_fit_columns=[1, 2],  # Type, Event Count (auto-fit)
            stretch_columns=[0, 3]  # IP Address, First Seen (stretch to fill)
        )
        self.ips_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.ips_table.verticalHeader().setVisible(True)
        ips_layout.addWidget(self.ips_table)
        
        ips_group.setLayout(ips_layout)
        entities_layout.addWidget(ips_group)
        
        # Devices section
        devices_group = QGroupBox("Affected Devices")
        devices_layout = QVBoxLayout()
        
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(4)
        self.devices_table.setHorizontalHeaderLabels([
            "Hostname", "IP Address", "Event Count", "Severity"
        ])
        # Configure intelligent auto-resizing
        TableAutoResize.configure(
            self.devices_table,
            content_fit_columns=[2, 3],  # Event Count, Severity (auto-fit)
            stretch_columns=[0, 1]  # Hostname, IP Address (stretch to fill)
        )
        self.devices_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.devices_table.verticalHeader().setVisible(True)
        devices_layout.addWidget(self.devices_table)
        
        devices_group.setLayout(devices_layout)
        entities_layout.addWidget(devices_group)
        
        entities_tab.setLayout(entities_layout)
        self.tabs.addTab(entities_tab, "Affected Entities")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
    
    def _analyze_event(self):
        """Start Claude analysis of the event."""
        self.analysis_text.setPlainText("Analyzing event with Claude... Please wait.")
        
        # Create worker thread
        self.worker = AnalysisWorker(self.event, self.finding, self.all_events)
        self.worker.finished.connect(self._on_analysis_complete)
        self.worker.error.connect(self._on_analysis_error)
        self.worker.start()
    
    def _on_analysis_complete(self, analysis: str):
        """Handle analysis completion."""
        self.analysis_text.setPlainText(analysis)
        # Also populate other tabs
        self._populate_similar_events()
        self._populate_correlated_events()
        self._populate_affected_entities()
    
    def _on_analysis_error(self, error: str):
        """Handle analysis error."""
        self.analysis_text.setPlainText(f"Error: {error}")
        QMessageBox.warning(self, "Analysis Error", error)
        # Still populate other tabs even if Claude fails
        self._populate_similar_events()
        self._populate_correlated_events()
        self._populate_affected_entities()
    
    def _populate_similar_events(self):
        """Find and display similar events."""
        similar_events = []
        
        # Method 1: Find by embedding similarity (if finding has embedding)
        if self.finding and 'embedding' in self.finding:
            finding_embedding = np.array(self.finding['embedding'])
            current_event_id = self.event.get('finding_id') or self.event.get('timestamp', '')
            
            for other_event in self.all_events:
                other_event_id = other_event.get('finding_id') or other_event.get('timestamp', '')
                if other_event_id == current_event_id:
                    continue
                
                other_finding_id = other_event.get('finding_id')
                if other_finding_id:
                    other_finding = self.data_service.get_finding(other_finding_id)
                    if other_finding and 'embedding' in other_finding:
                        other_embedding = np.array(other_finding['embedding'])
                        similarity = cosine_similarity(finding_embedding, other_embedding)
                        
                        if similarity > 0.7:  # Threshold for similarity
                            similar_events.append((other_event, similarity, 'embedding'))
        
        # Method 2: Find by cluster ID
        cluster_id = self.event.get('cluster_id')
        if cluster_id:
            current_event_id = self.event.get('finding_id') or self.event.get('timestamp', '')
            for other_event in self.all_events:
                other_event_id = other_event.get('finding_id') or other_event.get('timestamp', '')
                if (other_event.get('cluster_id') == cluster_id and 
                    other_event_id != current_event_id):
                    # Check if already added
                    if not any(e[0].get('finding_id') == other_event.get('finding_id') 
                              for e in similar_events if other_event.get('finding_id')):
                        similar_events.append((other_event, 1.0, 'cluster'))
        
        # Method 3: Find by MITRE techniques
        mitre_techniques = self.event.get('mitre_techniques', [])
        if mitre_techniques:
            current_event_id = self.event.get('finding_id') or self.event.get('timestamp', '')
            for other_event in self.all_events:
                other_event_id = other_event.get('finding_id') or other_event.get('timestamp', '')
                if other_event_id == current_event_id:
                    continue
                
                other_mitre = other_event.get('mitre_techniques', [])
                if other_mitre:
                    # Calculate overlap
                    overlap = len(set(mitre_techniques) & set(other_mitre))
                    if overlap > 0:
                        similarity = overlap / max(len(mitre_techniques), len(other_mitre))
                        if similarity > 0.5:
                            # Check if already added
                            if not any(e[0].get('finding_id') == other_event.get('finding_id') 
                                      for e in similar_events if other_event.get('finding_id')):
                                similar_events.append((other_event, similarity, 'mitre'))
        
        # Method 4: Find by IP addresses
        src_ip = self.event.get('entity_src_ip')
        dst_ip = self.event.get('entity_dst_ip')
        
        if src_ip or dst_ip:
            current_event_id = self.event.get('finding_id') or self.event.get('timestamp', '')
            for other_event in self.all_events:
                other_event_id = other_event.get('finding_id') or other_event.get('timestamp', '')
                if other_event_id == current_event_id:
                    continue
                
                other_src = other_event.get('entity_src_ip')
                other_dst = other_event.get('entity_dst_ip')
                
                ip_match = False
                if src_ip and (src_ip == other_src or src_ip == other_dst):
                    ip_match = True
                if dst_ip and (dst_ip == other_src or dst_ip == other_dst):
                    ip_match = True
                
                if ip_match:
                    # Check if already added
                    if not any(e[0].get('finding_id') == other_event.get('finding_id') 
                              for e in similar_events if other_event.get('finding_id')):
                        similar_events.append((other_event, 0.8, 'ip'))
        
        # Sort by similarity (descending)
        similar_events.sort(key=lambda x: x[1], reverse=True)
        
        # Limit to top 20
        similar_events = similar_events[:20]
        
        # Populate table
        self.similar_table.setRowCount(len(similar_events))
        
        for row, (event, similarity, match_type) in enumerate(similar_events):
            timestamp = event.get('timestamp', '')
            if 'T' in timestamp:
                timestamp = timestamp.split('T')[0] + ' ' + timestamp.split('T')[1].split('.')[0]
            
            self.similar_table.setItem(row, 0, QTableWidgetItem(timestamp))
            self.similar_table.setItem(row, 1, QTableWidgetItem(event.get('message', '')[:100]))
            self.similar_table.setItem(row, 2, QTableWidgetItem(f"{similarity:.3f} ({match_type})"))
            
            # Severity with Material Design colors
            severity = event.get('severity', '').lower()
            severity_item = QTableWidgetItem(severity.capitalize() if severity else '')
            if severity in self.SEVERITY_COLORS:
                severity_item.setForeground(self.SEVERITY_COLORS[severity])
            self.similar_table.setItem(row, 3, severity_item)
            
            self.similar_table.setItem(row, 4, QTableWidgetItem(event.get('entity_src_ip', '')))
            self.similar_table.setItem(row, 5, QTableWidgetItem(event.get('entity_dst_ip', '')))
        
        self.similar_table.resizeColumnsToContents()
    
    def _populate_correlated_events(self):
        """Find and display correlated events."""
        # Use timeline service correlation
        correlations = self.timeline_service.correlate_events(self.all_events)
        
        correlated_events = []
        event_id = self.event.get('finding_id') or self.event.get('timestamp', '')
        
        # Find correlations involving this event
        for correlation in correlations:
            events = correlation.get('events', [])
            for corr_event in events:
                corr_id = corr_event.get('finding_id') or corr_event.get('timestamp', '')
                if corr_id == event_id:
                    # Add all other events in this correlation
                    for other_event in events:
                        other_id = other_event.get('finding_id') or other_event.get('timestamp', '')
                        if other_id != event_id:
                            corr_type = correlation.get('type', 'unknown')
                            correlated_events.append((other_event, corr_type))
                    break
        
        # Also check advanced correlation
        advanced_corr = self.timeline_service.advanced_correlation(self.all_events)
        
        # Check IP networks
        src_ip = self.event.get('entity_src_ip')
        dst_ip = self.event.get('entity_dst_ip')
        
        if src_ip or dst_ip:
            ip_networks = advanced_corr.get('ip_networks', {})
            for network, network_data in ip_networks.items():
                network_events = network_data.get('events', [])
                for network_event in network_events:
                    net_id = network_event.get('finding_id') or network_event.get('timestamp', '')
                    if net_id == event_id:
                        # Add all other events in this network
                        for other_event in network_events:
                            other_id = other_event.get('finding_id') or other_event.get('timestamp', '')
                            if other_id != event_id:
                                if not any(e[0].get('finding_id') == other_event.get('finding_id') 
                                          for e in correlated_events):
                                    correlated_events.append((other_event, 'ip_network'))
                        break
        
        # Check temporal clusters
        temporal_clusters = advanced_corr.get('temporal_clusters', [])
        for cluster in temporal_clusters:
            cluster_events = cluster.get('events', [])
            for cluster_event in cluster_events:
                cluster_id = cluster_event.get('finding_id') or cluster_event.get('timestamp', '')
                if cluster_id == event_id:
                    # Add all other events in this temporal cluster
                    for other_event in cluster_events:
                        other_id = other_event.get('finding_id') or other_event.get('timestamp', '')
                        if other_id != event_id:
                            if not any(e[0].get('finding_id') == other_event.get('finding_id') 
                                      for e in correlated_events):
                                correlated_events.append((other_event, 'temporal'))
                    break
        
        # Populate table
        self.correlated_table.setRowCount(len(correlated_events))
        
        for row, (event, corr_type) in enumerate(correlated_events):
            timestamp = event.get('timestamp', '')
            if 'T' in timestamp:
                timestamp = timestamp.split('T')[0] + ' ' + timestamp.split('T')[1].split('.')[0]
            
            self.correlated_table.setItem(row, 0, QTableWidgetItem(timestamp))
            self.correlated_table.setItem(row, 1, QTableWidgetItem(event.get('message', '')[:100]))
            self.correlated_table.setItem(row, 2, QTableWidgetItem(corr_type))
            
            # Severity with Material Design colors
            severity = event.get('severity', '').lower()
            severity_item = QTableWidgetItem(severity.capitalize() if severity else '')
            if severity in self.SEVERITY_COLORS:
                severity_item.setForeground(self.SEVERITY_COLORS[severity])
            self.correlated_table.setItem(row, 3, severity_item)
            
            self.correlated_table.setItem(row, 4, QTableWidgetItem(event.get('entity_src_ip', '')))
            self.correlated_table.setItem(row, 5, QTableWidgetItem(event.get('entity_dst_ip', '')))
        
        self.correlated_table.resizeColumnsToContents()
    
    def _populate_affected_entities(self):
        """Populate affected IPs and devices."""
        # Collect all IPs and devices from all events
        ip_data = {}  # ip -> {type: 'src'|'dst'|'both', count: int, first_seen: str}
        device_data = {}  # hostname -> {ip: str, count: int, max_severity: str}
        
        for event in self.all_events:
            src_ip = event.get('entity_src_ip')
            dst_ip = event.get('entity_dst_ip')
            hostname = event.get('entity_hostname')
            severity = event.get('severity', 'unknown')
            timestamp = event.get('timestamp', '')
            
            # Track IPs
            if src_ip:
                if src_ip not in ip_data:
                    ip_data[src_ip] = {'type': 'src', 'count': 0, 'first_seen': timestamp}
                ip_data[src_ip]['count'] += 1
                if ip_data[src_ip]['type'] == 'dst':
                    ip_data[src_ip]['type'] = 'both'
                if timestamp < ip_data[src_ip]['first_seen']:
                    ip_data[src_ip]['first_seen'] = timestamp
            
            if dst_ip:
                if dst_ip not in ip_data:
                    ip_data[dst_ip] = {'type': 'dst', 'count': 0, 'first_seen': timestamp}
                ip_data[dst_ip]['count'] += 1
                if ip_data[dst_ip]['type'] == 'src':
                    ip_data[dst_ip]['type'] = 'both'
                if timestamp < ip_data[dst_ip]['first_seen']:
                    ip_data[dst_ip]['first_seen'] = timestamp
            
            # Track devices
            if hostname:
                device_ip = src_ip or dst_ip or ''
                if hostname not in device_data:
                    device_data[hostname] = {
                        'ip': device_ip,
                        'count': 0,
                        'max_severity': severity
                    }
                device_data[hostname]['count'] += 1
                # Update max severity
                severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'unknown': 0}
                if severity_order.get(severity, 0) > severity_order.get(device_data[hostname]['max_severity'], 0):
                    device_data[hostname]['max_severity'] = severity
        
        # Populate IPs table
        self.ips_table.setRowCount(len(ip_data))
        for row, (ip_addr, data) in enumerate(sorted(ip_data.items())):
            self.ips_table.setItem(row, 0, QTableWidgetItem(ip_addr))
            self.ips_table.setItem(row, 1, QTableWidgetItem(data['type']))
            self.ips_table.setItem(row, 2, QTableWidgetItem(str(data['count'])))
            first_seen = data['first_seen']
            if 'T' in first_seen:
                first_seen = first_seen.split('T')[0] + ' ' + first_seen.split('T')[1].split('.')[0]
            self.ips_table.setItem(row, 3, QTableWidgetItem(first_seen))
        
        self.ips_table.resizeColumnsToContents()
        
        # Populate devices table
        self.devices_table.setRowCount(len(device_data))
        for row, (hostname, data) in enumerate(sorted(device_data.items())):
            self.devices_table.setItem(row, 0, QTableWidgetItem(hostname))
            self.devices_table.setItem(row, 1, QTableWidgetItem(data['ip']))
            self.devices_table.setItem(row, 2, QTableWidgetItem(str(data['count'])))
            
            # Severity with Material Design colors
            severity = data['max_severity'].lower()
            severity_item = QTableWidgetItem(severity.capitalize())
            if severity in self.SEVERITY_COLORS:
                severity_item.setForeground(self.SEVERITY_COLORS[severity])
            self.devices_table.setItem(row, 3, severity_item)
        
        self.devices_table.resizeColumnsToContents()

