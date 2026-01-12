"""Advanced correlation analysis widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QGroupBox, QTextEdit,
    QTabWidget, QMessageBox
)
from PyQt6.QtCore import Qt
import logging

from services.timeline_service import TimelineService
from services.data_service import DataService
from services.sketch_manager import SketchManager

logger = logging.getLogger(__name__)


class CorrelationWidget(QWidget):
    """Widget for advanced timeline correlation analysis."""
    
    def __init__(self, case_id: str, parent=None):
        super().__init__(parent)
        self.case_id = case_id
        self.data_service = DataService()
        self.timeline_service = TimelineService()
        self.sketch_manager = SketchManager()
        
        self.events = []
        self.correlation_results = None
        
        self._setup_ui()
        self._load_events()
        self._run_correlation()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Header
        case = self.data_service.get_case(self.case_id)
        header_label = QLabel(
            f"<h3>Advanced Correlation Analysis</h3>"
            f"<p><b>Case:</b> {case.get('title', self.case_id) if case else self.case_id}</p>"
        )
        layout.addWidget(header_label)
        
        # Tabs for different correlation views
        self.tabs = QTabWidget()
        
        # Temporal Clusters
        temporal_tab = QWidget()
        temporal_layout = QVBoxLayout()
        self.temporal_table = QTableWidget()
        self.temporal_table.setColumnCount(4)
        self.temporal_table.setHorizontalHeaderLabels([
            "Start Time", "End Time", "Event Count", "Events"
        ])
        # Make resizable
        from PyQt6.QtWidgets import QHeaderView
        self.temporal_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.temporal_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.temporal_table.verticalHeader().setVisible(True)
        temporal_layout.addWidget(self.temporal_table)
        temporal_tab.setLayout(temporal_layout)
        self.tabs.addTab(temporal_tab, "Temporal Clusters")
        
        # IP Networks
        ip_tab = QWidget()
        ip_layout = QVBoxLayout()
        self.ip_table = QTableWidget()
        self.ip_table.setColumnCount(3)
        self.ip_table.setHorizontalHeaderLabels([
            "Network", "Event Count", "Details"
        ])
        # Make resizable
        self.ip_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.ip_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.ip_table.verticalHeader().setVisible(True)
        ip_layout.addWidget(self.ip_table)
        ip_tab.setLayout(ip_layout)
        self.tabs.addTab(ip_tab, "IP Networks")
        
        # Attack Chains
        attack_tab = QWidget()
        attack_layout = QVBoxLayout()
        self.attack_table = QTableWidget()
        self.attack_table.setColumnCount(4)
        self.attack_table.setHorizontalHeaderLabels([
            "Techniques", "Occurrences", "First Seen", "Last Seen"
        ])
        # Make resizable
        self.attack_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.attack_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.attack_table.verticalHeader().setVisible(True)
        attack_layout.addWidget(self.attack_table)
        attack_tab.setLayout(attack_layout)
        self.tabs.addTab(attack_tab, "Attack Chains")
        
        # Entity Relationships
        entity_tab = QWidget()
        entity_layout = QVBoxLayout()
        self.entity_table = QTableWidget()
        self.entity_table.setColumnCount(3)
        self.entity_table.setHorizontalHeaderLabels([
            "Relationship", "Event Count", "Details"
        ])
        # Make resizable
        self.entity_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.entity_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.entity_table.verticalHeader().setVisible(True)
        entity_layout.addWidget(self.entity_table)
        entity_tab.setLayout(entity_layout)
        self.tabs.addTab(entity_tab, "Entity Relationships")
        
        # Attack Patterns
        pattern_tab = QWidget()
        pattern_layout = QVBoxLayout()
        self.pattern_table = QTableWidget()
        self.pattern_table.setColumnCount(4)
        self.pattern_table.setHorizontalHeaderLabels([
            "Pattern", "Description", "Confidence", "Event Count"
        ])
        # Make resizable
        self.pattern_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.pattern_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.pattern_table.verticalHeader().setVisible(True)
        pattern_layout.addWidget(self.pattern_table)
        pattern_tab.setLayout(pattern_layout)
        self.tabs.addTab(pattern_tab, "Attack Patterns")
        
        # MITRE Patterns
        mitre_tab = QWidget()
        mitre_layout = QVBoxLayout()
        self.mitre_table = QTableWidget()
        self.mitre_table.setColumnCount(3)
        self.mitre_table.setHorizontalHeaderLabels([
            "Technique", "Occurrences", "Events"
        ])
        # Make resizable
        self.mitre_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.mitre_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.mitre_table.verticalHeader().setVisible(True)
        mitre_layout.addWidget(self.mitre_table)
        mitre_tab.setLayout(mitre_layout)
        self.tabs.addTab(mitre_tab, "MITRE Patterns")
        
        layout.addWidget(self.tabs)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Analysis")
        refresh_btn.clicked.connect(self._run_correlation)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
    
    def _load_events(self):
        """Load events for the case."""
        case = self.data_service.get_case(self.case_id)
        if not case:
            return
        
        finding_ids = case.get('finding_ids', [])
        findings = []
        for finding_id in finding_ids:
            finding = self.data_service.get_finding(finding_id)
            if finding:
                findings.append(finding)
        
        self.events = self.timeline_service.case_to_timeline_events(case, findings)
    
    def _run_correlation(self):
        """Run correlation analysis."""
        if not self.events:
            QMessageBox.warning(self, "No Events", "No events found for correlation analysis.")
            return
        
        # Run advanced correlation
        self.correlation_results = self.timeline_service.advanced_correlation(self.events)
        
        # Run attack pattern detection
        attack_patterns = self.timeline_service.detect_attack_patterns(self.events)
        
        # Populate tables
        self._populate_temporal_clusters()
        self._populate_ip_networks()
        self._populate_attack_chains()
        self._populate_entity_relationships()
        self._populate_attack_patterns(attack_patterns)
        self._populate_mitre_patterns()
    
    def _populate_temporal_clusters(self):
        """Populate temporal clusters table."""
        clusters = self.correlation_results.get('temporal_clusters', [])
        self.temporal_table.setRowCount(len(clusters))
        
        for row, cluster in enumerate(clusters):
            start_time = cluster.get('start_time', '')
            if 'T' in start_time:
                start_time = start_time.split('T')[0] + ' ' + start_time.split('T')[1].split('.')[0]
            
            end_time = cluster.get('end_time', '')
            if 'T' in end_time:
                end_time = end_time.split('T')[0] + ' ' + end_time.split('T')[1].split('.')[0]
            
            self.temporal_table.setItem(row, 0, QTableWidgetItem(start_time))
            self.temporal_table.setItem(row, 1, QTableWidgetItem(end_time))
            self.temporal_table.setItem(row, 2, QTableWidgetItem(str(cluster.get('count', 0))))
            
            events_text = '\n'.join([e.get('message', '')[:50] for e in cluster.get('events', [])[:3]])
            self.temporal_table.setItem(row, 3, QTableWidgetItem(events_text))
        
        self.temporal_table.resizeColumnsToContents()
    
    def _populate_ip_networks(self):
        """Populate IP networks table."""
        networks = self.correlation_results.get('ip_networks', {})
        rows = list(networks.items())
        self.ip_table.setRowCount(len(rows))
        
        for row, (network, data) in enumerate(rows):
            self.ip_table.setItem(row, 0, QTableWidgetItem(network))
            self.ip_table.setItem(row, 1, QTableWidgetItem(str(data.get('count', 0))))
            
            events = data.get('events', [])
            details = f"{len(events)} events"
            if events:
                src_ips = set([e.get('entity_src_ip') for e in events if e.get('entity_src_ip')])
                if src_ips:
                    details += f"\nSource IPs: {', '.join(list(src_ips)[:3])}"
            
            self.ip_table.setItem(row, 2, QTableWidgetItem(details))
        
        self.ip_table.resizeColumnsToContents()
    
    def _populate_attack_chains(self):
        """Populate attack chains table."""
        chains = self.correlation_results.get('attack_chains', [])
        self.attack_table.setRowCount(len(chains))
        
        for row, chain in enumerate(chains):
            techniques = ', '.join(chain.get('techniques', []))
            self.attack_table.setItem(row, 0, QTableWidgetItem(techniques))
            self.attack_table.setItem(row, 1, QTableWidgetItem(str(chain.get('count', 0))))
            
            occurrences = chain.get('occurrences', [])
            if occurrences:
                first = occurrences[0].get('timestamp', '')
                last = occurrences[-1].get('timestamp', '')
                if 'T' in first:
                    first = first.split('T')[0]
                if 'T' in last:
                    last = last.split('T')[0]
                
                self.attack_table.setItem(row, 2, QTableWidgetItem(first))
                self.attack_table.setItem(row, 3, QTableWidgetItem(last))
        
        self.attack_table.resizeColumnsToContents()
    
    def _populate_entity_relationships(self):
        """Populate entity relationships table."""
        relationships = self.correlation_results.get('entity_relationships', [])
        self.entity_table.setRowCount(len(relationships))
        
        for row, rel in enumerate(relationships):
            self.entity_table.setItem(row, 0, QTableWidgetItem(rel.get('relationship', '')))
            self.entity_table.setItem(row, 1, QTableWidgetItem(str(rel.get('count', 0))))
            
            events = rel.get('events', [])
            details = f"{len(events)} events"
            if events:
                messages = [e.get('message', '')[:40] for e in events[:2]]
                details += f"\n{chr(10).join(messages)}"
            
            self.entity_table.setItem(row, 2, QTableWidgetItem(details))
        
        self.entity_table.resizeColumnsToContents()
    
    def _populate_attack_patterns(self, patterns: list):
        """Populate attack patterns table."""
        self.pattern_table.setRowCount(len(patterns))
        
        for row, pattern in enumerate(patterns):
            self.pattern_table.setItem(row, 0, QTableWidgetItem(pattern.get('pattern', '')))
            self.pattern_table.setItem(row, 1, QTableWidgetItem(pattern.get('description', '')))
            
            confidence = pattern.get('confidence', 'unknown')
            confidence_item = QTableWidgetItem(confidence)
            if confidence == 'high':
                confidence_item.setForeground(Qt.GlobalColor.red)
            elif confidence == 'medium':
                confidence_item.setForeground(Qt.GlobalColor.darkYellow)
            self.pattern_table.setItem(row, 2, confidence_item)
            
            events = pattern.get('events', [])
            if not events:
                events = []
                if pattern.get('recon_events'):
                    events.extend(pattern.get('recon_events', []))
                if pattern.get('access_events'):
                    events.extend(pattern.get('access_events', []))
                if pattern.get('exec_events'):
                    events.extend(pattern.get('exec_events', []))
            
            self.pattern_table.setItem(row, 3, QTableWidgetItem(str(len(events))))
        
        self.pattern_table.resizeColumnsToContents()
    
    def _populate_mitre_patterns(self):
        """Populate MITRE patterns table."""
        patterns = self.correlation_results.get('mitre_patterns', {})
        rows = list(patterns.items())
        self.mitre_table.setRowCount(len(rows))
        
        for row, (technique, events) in enumerate(rows):
            self.mitre_table.setItem(row, 0, QTableWidgetItem(technique))
            self.mitre_table.setItem(row, 1, QTableWidgetItem(str(len(events))))
            
            events_text = '\n'.join([e.get('message', '')[:40] for e in events[:3]])
            self.mitre_table.setItem(row, 2, QTableWidgetItem(events_text))
        
        self.mitre_table.resizeColumnsToContents()

