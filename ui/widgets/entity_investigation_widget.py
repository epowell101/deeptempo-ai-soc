"""Entity-Centric Investigation Widget - Investigate by entity (IP, hostname, user)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QLineEdit, QComboBox, QGroupBox, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from datetime import datetime
from typing import Dict, List, Set

from services.data_service import DataService


class EntityInvestigationWidget(QWidget):
    """Widget for entity-centric investigation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_service = DataService()
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("<h2>Entity-Centric Investigation</h2>")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Search and filter controls
        controls = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search entities...")
        self.search_input.textChanged.connect(self._filter_entities)
        controls.addWidget(QLabel("Search:"))
        controls.addWidget(self.search_input)
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "IP", "Host", "User", "Domain"])
        self.type_filter.currentTextChanged.connect(self._filter_entities)
        controls.addWidget(QLabel("Type:"))
        controls.addWidget(self.type_filter)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        controls.addWidget(refresh_btn)
        
        controls.addStretch()
        
        layout.addLayout(controls)
        
        # Entity table
        self.entity_table = QTableWidget()
        self.entity_table.setColumnCount(7)
        self.entity_table.setHorizontalHeaderLabels([
            "Entity", "Type", "Risk", "Risk Score", "Findings", "Alerts", "First Seen"
        ])
        self.entity_table.horizontalHeader().setStretchLastSection(True)
        self.entity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.entity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.entity_table.itemSelectionChanged.connect(self._on_entity_selected)
        # Make table expand to fill available space (relative sizing)
        layout.addWidget(self.entity_table, 2)  # Stretch factor of 2 (takes more space than detail)
        
        # Entity detail view
        detail_group = QGroupBox("Entity Details")
        detail_layout = QVBoxLayout()
        
        self.detail_label = QLabel("Select an entity to view details")
        self.detail_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_label)
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        # Use relative sizing instead of fixed height
        detail_layout.addWidget(self.detail_text, 1)  # Stretch factor
        
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        self.setLayout(layout)
        
        self.entities_data = {}
        self.filtered_entities = []
    
    def _extract_entities(self, findings: List[Dict], alerts: List[Dict] = None) -> Dict:
        """Extract all unique entities from findings and alerts."""
        if alerts is None:
            alerts = []
        
        entities = {}
        
        # Extract from findings
        for finding in findings:
            entity = finding.get("entity_context", {})
            
            # Source IP
            src_ip = entity.get("src_ip")
            if src_ip:
                if src_ip not in entities:
                    entities[src_ip] = {
                        "type": "IP",
                        "findings": [],
                        "alerts": [],
                        "first_seen": None,
                        "last_seen": None
                    }
                entities[src_ip]["findings"].append(finding.get("finding_id", ""))
                ts = finding.get("timestamp")
                if ts:
                    if not entities[src_ip]["first_seen"] or ts < entities[src_ip]["first_seen"]:
                        entities[src_ip]["first_seen"] = ts
                    if not entities[src_ip]["last_seen"] or ts > entities[src_ip]["last_seen"]:
                        entities[src_ip]["last_seen"] = ts
            
            # Dest IP
            dest_ip = entity.get("dst_ip")
            if dest_ip:
                if dest_ip not in entities:
                    entities[dest_ip] = {
                        "type": "IP",
                        "findings": [],
                        "alerts": [],
                        "first_seen": None,
                        "last_seen": None
                    }
                entities[dest_ip]["findings"].append(finding.get("finding_id", ""))
                ts = finding.get("timestamp")
                if ts:
                    if not entities[dest_ip]["first_seen"] or ts < entities[dest_ip]["first_seen"]:
                        entities[dest_ip]["first_seen"] = ts
                    if not entities[dest_ip]["last_seen"] or ts > entities[dest_ip]["last_seen"]:
                        entities[dest_ip]["last_seen"] = ts
            
            # Hostname
            hostname = entity.get("hostname")
            if hostname:
                if hostname not in entities:
                    entities[hostname] = {
                        "type": "Host",
                        "findings": [],
                        "alerts": [],
                        "first_seen": None,
                        "last_seen": None
                    }
                entities[hostname]["findings"].append(finding.get("finding_id", ""))
                ts = finding.get("timestamp")
                if ts:
                    if not entities[hostname]["first_seen"] or ts < entities[hostname]["first_seen"]:
                        entities[hostname]["first_seen"] = ts
                    if not entities[hostname]["last_seen"] or ts > entities[hostname]["last_seen"]:
                        entities[hostname]["last_seen"] = ts
            
            # User
            user = entity.get("user")
            if user:
                if user not in entities:
                    entities[user] = {
                        "type": "User",
                        "findings": [],
                        "alerts": [],
                        "first_seen": None,
                        "last_seen": None
                    }
                entities[user]["findings"].append(finding.get("finding_id", ""))
            
            # Domain
            query_name = entity.get("query_name")
            if query_name:
                # Extract domain
                parts = query_name.split(".")
                if len(parts) >= 2:
                    domain = ".".join(parts[-2:])
                    if domain not in entities:
                        entities[domain] = {
                            "type": "Domain",
                            "findings": [],
                            "alerts": [],
                            "first_seen": None,
                            "last_seen": None
                        }
                    entities[domain]["findings"].append(finding.get("finding_id", ""))
        
        # Extract from alerts (if available)
        for alert in alerts:
            src_ip = alert.get("source_ip")
            if src_ip:
                if src_ip not in entities:
                    entities[src_ip] = {
                        "type": "IP",
                        "findings": [],
                        "alerts": [],
                        "first_seen": None,
                        "last_seen": None
                    }
                entities[src_ip]["alerts"].append(alert.get("id", ""))
        
        # Calculate risk scores
        for entity_name, entity_data in entities.items():
            finding_count = len(entity_data["findings"])
            alert_count = len(entity_data["alerts"])
            
            # Risk based on finding involvement
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
    
    def _filter_entities(self):
        """Filter entities based on search and type."""
        search_term = self.search_input.text().lower()
        type_filter = self.type_filter.currentText()
        
        self.filtered_entities = []
        
        for entity_name, entity_info in self.entities_data.items():
            # Search filter
            if search_term and search_term not in entity_name.lower():
                continue
            
            # Type filter
            if type_filter != "All Types" and entity_info["type"] != type_filter:
                continue
            
            self.filtered_entities.append((entity_name, entity_info))
        
        # Sort by risk score
        self.filtered_entities.sort(key=lambda x: x[1].get("risk_score", 0), reverse=True)
        
        self._populate_table()
    
    def _populate_table(self):
        """Populate the entity table."""
        self.entity_table.setRowCount(len(self.filtered_entities))
        
        for row, (entity_name, entity_info) in enumerate(self.filtered_entities):
            self.entity_table.setItem(row, 0, QTableWidgetItem(entity_name))
            self.entity_table.setItem(row, 1, QTableWidgetItem(entity_info["type"]))
            
            risk_item = QTableWidgetItem(entity_info["risk"])
            if entity_info["risk"] == "HIGH":
                risk_item.setForeground(Qt.GlobalColor.red)
            elif entity_info["risk"] == "MEDIUM":
                risk_item.setForeground(Qt.GlobalColor.darkYellow)
            else:
                risk_item.setForeground(Qt.GlobalColor.green)
            self.entity_table.setItem(row, 2, risk_item)
            
            self.entity_table.setItem(row, 3, QTableWidgetItem(str(entity_info["risk_score"])))
            self.entity_table.setItem(row, 4, QTableWidgetItem(str(len(entity_info["findings"]))))
            self.entity_table.setItem(row, 5, QTableWidgetItem(str(len(entity_info["alerts"]))))
            
            first_seen = entity_info.get("first_seen", "N/A")
            if first_seen and first_seen != "N/A":
                first_seen = first_seen[:16] if len(first_seen) > 16 else first_seen
            self.entity_table.setItem(row, 6, QTableWidgetItem(first_seen))
        
        self.entity_table.resizeColumnsToContents()
    
    def _on_entity_selected(self):
        """Handle entity selection."""
        selected_rows = self.entity_table.selectedIndexes()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row >= len(self.filtered_entities):
            return
        
        entity_name, entity_info = self.filtered_entities[row]
        
        # Update detail view
        self.detail_label.setText(f"<b>Entity:</b> {entity_name}")
        
        detail_text = f"""
<b>Type:</b> {entity_info['type']}<br>
<b>Risk Level:</b> {entity_info['risk']}<br>
<b>Risk Score:</b> {entity_info['risk_score']}<br>
<b>Related Findings:</b> {len(entity_info['findings'])}<br>
<b>Related Alerts:</b> {len(entity_info['alerts'])}<br>
<b>First Seen:</b> {entity_info.get('first_seen', 'N/A')}<br>
<b>Last Seen:</b> {entity_info.get('last_seen', 'N/A')}<br>
<br>
<b>Finding IDs:</b><br>
{', '.join(entity_info['findings'][:10])}
{('...' if len(entity_info['findings']) > 10 else '')}
        """
        
        self.detail_text.setHtml(detail_text)
    
    def refresh(self):
        """Refresh entity data."""
        findings = self.data_service.get_findings()
        
        # Extract entities
        self.entities_data = self._extract_entities(findings)
        
        # Apply filters
        self._filter_entities()

