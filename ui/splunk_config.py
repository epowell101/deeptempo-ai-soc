"""Splunk configuration dialog."""

import logging
from pathlib import Path
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QCheckBox, QSpinBox, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt

from services.splunk_service import SplunkService

logger = logging.getLogger(__name__)


class SplunkConfigDialog(QDialog):
    """Dialog for configuring Splunk connection."""
    
    CONFIG_FILE = Path("data/splunk_config.json")
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Splunk Configuration")
        self.setMinimumSize(500, 300)
        
        self.splunk_service = None
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(
            "Configure connection to your Splunk server for data enrichment.\n"
            "Credentials are stored locally."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Connection settings
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QFormLayout()
        
        self.server_url_edit = QLineEdit()
        self.server_url_edit.setPlaceholderText("https://splunk.example.com:8089")
        self.server_url_edit.setToolTip("Splunk server URL including port (default: 8089)")
        conn_layout.addRow("Server URL:", self.server_url_edit)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("admin")
        self.username_edit.setToolTip("Splunk username")
        conn_layout.addRow("Username:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password...")
        self.password_edit.setToolTip("Splunk password")
        conn_layout.addRow("Password:", self.password_edit)
        
        self.verify_ssl_checkbox = QCheckBox("Verify SSL Certificate")
        self.verify_ssl_checkbox.setChecked(False)
        self.verify_ssl_checkbox.setToolTip("Enable SSL certificate verification (disable for self-signed certificates)")
        conn_layout.addRow("", self.verify_ssl_checkbox)
        
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Query settings
        query_group = QGroupBox("Query Settings")
        query_layout = QFormLayout()
        
        self.lookback_hours_spin = QSpinBox()
        self.lookback_hours_spin.setMinimum(1)
        self.lookback_hours_spin.setMaximum(720)  # 30 days max
        self.lookback_hours_spin.setValue(168)  # 7 days default
        self.lookback_hours_spin.setSuffix(" hours")
        self.lookback_hours_spin.setToolTip("Default lookback period for Splunk queries")
        query_layout.addRow("Default Lookback:", self.lookback_hours_spin)
        
        query_group.setLayout(query_layout)
        layout.addWidget(query_group)
        
        # Test connection button
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_connection)
        layout.addWidget(test_btn)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_config)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                
                self.server_url_edit.setText(config.get('server_url', ''))
                self.username_edit.setText(config.get('username', ''))
                self.password_edit.setText(config.get('password', ''))
                self.verify_ssl_checkbox.setChecked(config.get('verify_ssl', False))
                self.lookback_hours_spin.setValue(config.get('lookback_hours', 168))
                
                self.status_label.setText("✓ Configuration loaded")
                self.status_label.setStyleSheet("color: green;")
        
        except Exception as e:
            logger.error(f"Error loading Splunk config: {e}")
            self.status_label.setText(f"Error loading config: {e}")
            self.status_label.setStyleSheet("color: red;")
    
    def _save_config(self):
        """Save configuration to file."""
        server_url = self.server_url_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not server_url or not username or not password:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Server URL, username, and password are required."
            )
            return
        
        config = {
            'server_url': server_url,
            'username': username,
            'password': password,
            'verify_ssl': self.verify_ssl_checkbox.isChecked(),
            'lookback_hours': self.lookback_hours_spin.value()
        }
        
        try:
            # Ensure data directory exists
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            
            QMessageBox.information(
                self,
                "Success",
                "Splunk configuration saved successfully!"
            )
            
            self.accept()
        
        except Exception as e:
            logger.error(f"Error saving Splunk config: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save configuration: {e}"
            )
    
    def _test_connection(self):
        """Test connection to Splunk server."""
        server_url = self.server_url_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        verify_ssl = self.verify_ssl_checkbox.isChecked()
        
        if not server_url or not username or not password:
            self.status_label.setText("⚠ Please fill in all connection fields")
            self.status_label.setStyleSheet("color: orange;")
            return
        
        self.status_label.setText("Testing connection...")
        self.status_label.setStyleSheet("color: blue;")
        
        try:
            test_service = SplunkService(
                server_url=server_url,
                username=username,
                password=password,
                verify_ssl=verify_ssl
            )
            
            success, message = test_service.test_connection()
            
            if success:
                self.status_label.setText(f"✓ {message}")
                self.status_label.setStyleSheet("color: green;")
                QMessageBox.information(
                    self,
                    "Connection Successful",
                    "Successfully connected to Splunk server!"
                )
            else:
                self.status_label.setText(f"✗ {message}")
                self.status_label.setStyleSheet("color: red;")
                QMessageBox.warning(
                    self,
                    "Connection Failed",
                    f"Failed to connect to Splunk:\n\n{message}"
                )
        
        except Exception as e:
            logger.error(f"Error testing Splunk connection: {e}")
            self.status_label.setText(f"✗ Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.critical(
                self,
                "Error",
                f"Error testing connection:\n\n{str(e)}"
            )
    
    @staticmethod
    def load_service() -> SplunkService:
        """
        Load Splunk service from saved configuration.
        
        Returns:
            SplunkService instance if configured, None otherwise
        """
        try:
            config_file = Path("data/splunk_config.json")
            if not config_file.exists():
                return None
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if not all(k in config for k in ['server_url', 'username', 'password']):
                return None
            
            service = SplunkService(
                server_url=config['server_url'],
                username=config['username'],
                password=config['password'],
                verify_ssl=config.get('verify_ssl', False)
            )
            
            return service
        
        except Exception as e:
            logger.error(f"Error loading Splunk service: {e}")
            return None
    
    @staticmethod
    def get_lookback_hours() -> int:
        """
        Get default lookback hours from configuration.
        
        Returns:
            Lookback hours (default: 168)
        """
        try:
            config_file = Path("data/splunk_config.json")
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                return config.get('lookback_hours', 168)
        except:
            pass
        
        return 168  # Default to 7 days

