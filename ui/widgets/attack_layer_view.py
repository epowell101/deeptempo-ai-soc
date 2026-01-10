"""ATT&CK Navigator layer view widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
import json
import webbrowser
from pathlib import Path

from services.data_service import DataService


class AttackLayerViewWidget(QWidget):
    """Widget for viewing and managing ATT&CK Navigator layers."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_service = DataService()
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(
            "MITRE ATT&CK Technique Rollup\n\n"
            "This view shows detected ATT&CK techniques across all findings."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        generate_btn = QPushButton("Generate ATT&CK Layer")
        generate_btn.clicked.connect(self._generate_layer)
        toolbar.addWidget(generate_btn)
        
        export_btn = QPushButton("Export Layer")
        export_btn.clicked.connect(self._export_layer)
        toolbar.addWidget(export_btn)
        
        open_btn = QPushButton("Open in Navigator")
        open_btn.clicked.connect(self._open_navigator)
        toolbar.addWidget(open_btn)
        
        toolbar.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # Technique table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Technique", "Finding Count", "Avg Confidence", "Score"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def refresh(self):
        """Refresh technique rollup."""
        findings = self.data_service.get_findings()
        
        # Aggregate techniques
        technique_stats = {}
        for finding in findings:
            predictions = finding.get('mitre_predictions', {})
            for technique, confidence in predictions.items():
                if confidence < 0.5:  # Minimum confidence threshold
                    continue
                
                if technique not in technique_stats:
                    technique_stats[technique] = {
                        'count': 0,
                        'total_confidence': 0.0
                    }
                
                technique_stats[technique]['count'] += 1
                technique_stats[technique]['total_confidence'] += confidence
        
        # Build results
        results = []
        for technique, stats in technique_stats.items():
            avg_confidence = stats['total_confidence'] / stats['count']
            # Calculate score (combination of count and confidence)
            volume_factor = min(1.0, stats['count'] / 10)
            confidence_factor = avg_confidence
            score = int((volume_factor * 0.4 + confidence_factor * 0.6) * 100)
            
            results.append({
                'technique': technique,
                'count': stats['count'],
                'avg_confidence': avg_confidence,
                'score': score
            })
        
        # Sort by count
        results.sort(key=lambda x: x['count'], reverse=True)
        
        # Populate table
        self.table.setRowCount(len(results))
        for row, result in enumerate(results):
            self.table.setItem(row, 0, QTableWidgetItem(result['technique']))
            self.table.setItem(row, 1, QTableWidgetItem(str(result['count'])))
            self.table.setItem(row, 2, QTableWidgetItem(f"{result['avg_confidence']:.3f}"))
            self.table.setItem(row, 3, QTableWidgetItem(str(result['score'])))
        
        self.table.resizeColumnsToContents()
        self.technique_results = results
    
    def _generate_layer(self):
        """Generate ATT&CK Navigator layer."""
        if not hasattr(self, 'technique_results') or not self.technique_results:
            QMessageBox.warning(self, "No Data", "No technique data available. Please refresh first.")
            return
        
        techniques = []
        for result in self.technique_results:
            techniques.append({
                "techniqueID": result['technique'],
                "score": result['score'],
                "comment": f"{result['count']} findings, avg conf {result['avg_confidence']:.2f}",
                "enabled": True,
                "showSubtechniques": True
            })
        
        layer = {
            "name": "DeepTempo AI SOC Layer",
            "versions": {
                "attack": "14",
                "navigator": "4.9.1",
                "layer": "4.5"
            },
            "domain": "enterprise-attack",
            "description": "ATT&CK layer generated from DeepTempo findings",
            "techniques": techniques,
            "gradient": {
                "colors": ["#ffffff", "#66b3ff", "#ff6666"],
                "minValue": 0,
                "maxValue": 100
            }
        }
        
        # Save to data service
        if self.data_service.save_demo_layer(layer):
            QMessageBox.information(
                self,
                "Success",
                f"ATT&CK layer generated with {len(techniques)} techniques.\n\n"
                f"Saved to: {self.data_service.demo_layer_file}"
            )
        else:
            QMessageBox.critical(self, "Error", "Failed to save ATT&CK layer.")
    
    def _export_layer(self):
        """Export ATT&CK layer to file."""
        layer = self.data_service.get_demo_layer()
        if not layer:
            QMessageBox.warning(self, "No Layer", "No layer available. Please generate one first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export ATT&CK Layer",
            "attack_layer.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(layer, f, indent=2)
                QMessageBox.information(self, "Success", f"Layer exported to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export layer: {e}")
    
    def _open_navigator(self):
        """Open ATT&CK Navigator in browser."""
        layer = self.data_service.get_demo_layer()
        if not layer:
            reply = QMessageBox.question(
                self,
                "No Layer",
                "No layer available. Generate one now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._generate_layer()
                layer = self.data_service.get_demo_layer()
            
            if not layer:
                return
        
        # Open Navigator
        navigator_url = "https://mitre-attack.github.io/attack-navigator/"
        webbrowser.open(navigator_url)
        
        QMessageBox.information(
            self,
            "Navigator Opened",
            "ATT&CK Navigator opened in your browser.\n\n"
            "To load the layer:\n"
            "1. Click 'Open Existing Layer'\n"
            "2. Select 'Upload from local'\n"
            f"3. Select: {self.data_service.demo_layer_file}"
        )

