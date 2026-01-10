"""Configuration manager for Claude Desktop MCP integration."""

import json
import platform
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QMessageBox, QFileDialog, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt


class ConfigManager(QDialog):
    """Configuration manager dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Claude Desktop Configuration Manager")
        self.setMinimumSize(700, 600)
        
        self.project_root = Path(__file__).parent.parent
        self.claude_config_path = self._get_claude_config_path()
        
        self._setup_ui()
        self._load_config()
    
    def _get_claude_config_path(self) -> Path:
        """Get the Claude Desktop config file path."""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "Claude"
        elif system == "Windows":
            config_dir = Path.home() / "AppData" / "Roaming" / "Claude"
        else:  # Linux
            config_dir = Path.home() / ".config" / "claude"
        
        return config_dir / "claude_desktop_config.json"
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Info section
        info_group = QGroupBox("Configuration Information")
        info_layout = QVBoxLayout()
        
        info_label = QLabel(
            "This tool will configure Claude Desktop to use the DeepTempo AI SOC MCP servers.\n\n"
            "The configuration will be written to your Claude Desktop config file."
        )
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        self.config_path_label = QLabel(f"Config file: {self.claude_config_path}")
        self.config_path_label.setWordWrap(True)
        info_layout.addWidget(self.config_path_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Paths section
        paths_group = QGroupBox("Paths")
        paths_layout = QFormLayout()
        
        self.project_path_edit = QLineEdit()
        self.project_path_edit.setText(str(self.project_root))
        browse_project_btn = QPushButton("Browse...")
        browse_project_btn.clicked.connect(self._browse_project_path)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.project_path_edit)
        path_layout.addWidget(browse_project_btn)
        paths_layout.addRow("Project Path:", path_layout)
        
        self.venv_path_edit = QLineEdit()
        self.venv_path_edit.setText(str(self.project_root / "venv"))
        browse_venv_btn = QPushButton("Browse...")
        browse_venv_btn.clicked.connect(self._browse_venv_path)
        venv_layout = QHBoxLayout()
        venv_layout.addWidget(self.venv_path_edit)
        venv_layout.addWidget(browse_venv_btn)
        paths_layout.addRow("Virtual Environment Path:", venv_layout)
        
        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)
        
        # Preview section
        preview_group = QGroupBox("Configuration Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Preview Configuration")
        self.preview_btn.clicked.connect(self._preview_config)
        button_layout.addWidget(self.preview_btn)
        
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.clicked.connect(self._save_config)
        button_layout.addWidget(self.save_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Auto-preview on path change
        self.project_path_edit.textChanged.connect(self._update_preview)
        self.venv_path_edit.textChanged.connect(self._update_preview)
    
    def _browse_project_path(self):
        """Browse for project path."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Project Directory",
            str(self.project_root)
        )
        if path:
            self.project_path_edit.setText(path)
            # Update venv path
            self.venv_path_edit.setText(str(Path(path) / "venv"))
    
    def _browse_venv_path(self):
        """Browse for virtual environment path."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Virtual Environment Directory",
            str(self.project_root / "venv")
        )
        if path:
            self.venv_path_edit.setText(path)
    
    def _load_config(self):
        """Load existing Claude Desktop config."""
        if self.claude_config_path.exists():
            try:
                with open(self.claude_config_path, 'r') as f:
                    self.existing_config = json.load(f)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"Could not load existing config: {e}\n\nWill create new config."
                )
                self.existing_config = {}
        else:
            self.existing_config = {}
        
        self._update_preview()
    
    def _generate_mcp_config(self) -> dict:
        """Generate MCP server configuration."""
        project_path = Path(self.project_path_edit.text())
        venv_path = Path(self.venv_path_edit.text())
        
        # Determine Python executable
        if platform.system() == "Windows":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
        
        python_exe_str = str(python_exe)
        
        mcp_servers = {
            "deeptempo-findings": {
                "command": python_exe_str,
                "args": ["-m", "mcp_servers.deeptempo_findings_server.server"],
                "cwd": str(project_path),
                "env": {
                    "PYTHONPATH": str(project_path)
                }
            },
            "evidence-snippets": {
                "command": python_exe_str,
                "args": ["-m", "mcp_servers.evidence_snippets_server.server"],
                "cwd": str(project_path),
                "env": {
                    "PYTHONPATH": str(project_path)
                }
            },
            "case-store": {
                "command": python_exe_str,
                "args": ["-m", "mcp_servers.case_store_server.server"],
                "cwd": str(project_path),
                "env": {
                    "PYTHONPATH": str(project_path)
                }
            }
        }
        
        return mcp_servers
    
    def _update_preview(self):
        """Update configuration preview."""
        mcp_servers = self._generate_mcp_config()
        
        # Merge with existing config
        config = self.existing_config.copy()
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # Merge MCP servers (new ones will override existing)
        config["mcpServers"].update(mcp_servers)
        
        self.preview_text.setPlainText(json.dumps(config, indent=2))
    
    def _preview_config(self):
        """Show configuration preview."""
        self._update_preview()
        QMessageBox.information(
            self,
            "Configuration Preview",
            "Configuration preview updated in the preview area above."
        )
    
    def _save_config(self):
        """Save configuration to Claude Desktop config file."""
        # Validate paths
        project_path = Path(self.project_path_edit.text())
        venv_path = Path(self.venv_path_edit.text())
        
        if not project_path.exists():
            QMessageBox.critical(
                self,
                "Error",
                f"Project path does not exist: {project_path}"
            )
            return
        
        if not venv_path.exists():
            reply = QMessageBox.question(
                self,
                "Virtual Environment Not Found",
                f"Virtual environment not found at: {venv_path}\n\n"
                "Would you like to continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Check Python executable
        if platform.system() == "Windows":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
        
        if not python_exe.exists():
            QMessageBox.warning(
                self,
                "Warning",
                f"Python executable not found at: {python_exe}\n\n"
                "The configuration may not work correctly."
            )
        
        # Generate config
        mcp_servers = self._generate_mcp_config()
        
        # Merge with existing config
        config = self.existing_config.copy()
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # Backup existing config if it exists
        if self.claude_config_path.exists():
            backup_path = self.claude_config_path.with_suffix('.json.backup')
            try:
                shutil.copy2(self.claude_config_path, backup_path)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Backup Warning",
                    f"Could not create backup: {e}\n\nProceeding anyway..."
                )
        
        # Merge MCP servers
        config["mcpServers"].update(mcp_servers)
        
        # Ensure config directory exists
        self.claude_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save config
        try:
            with open(self.claude_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            QMessageBox.information(
                self,
                "Success",
                f"Configuration saved successfully!\n\n"
                f"File: {self.claude_config_path}\n\n"
                "Please restart Claude Desktop for changes to take effect."
            )
            
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save configuration:\n\n{e}"
            )

