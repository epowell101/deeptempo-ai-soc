"""Setup wizard for initial environment configuration."""

import sys
import subprocess
import platform
from pathlib import Path
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel, QProgressBar,
    QTextEdit, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from services.data_service import DataService


class SetupWorker(QThread):
    """Worker thread for setup operations."""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, project_root: Path, generate_sample_data: bool = False):
        super().__init__()
        self.project_root = project_root
        self.generate_sample_data = generate_sample_data
    
    def run(self):
        """Run the setup process."""
        try:
            # Check Python version
            self.progress.emit("Checking Python version...")
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 10):
                self.finished.emit(False, "Python 3.10+ is required")
                return
            
            # Create virtual environment
            self.progress.emit("Creating virtual environment...")
            venv_path = self.project_root / "venv"
            
            if not venv_path.exists():
                result = subprocess.run(
                    [sys.executable, "-m", "venv", str(venv_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    self.finished.emit(False, f"Failed to create venv: {result.stderr}")
                    return
            
            # Determine Python executable in venv
            if platform.system() == "Windows":
                python_exe = venv_path / "Scripts" / "python.exe"
                pip_exe = venv_path / "Scripts" / "pip.exe"
            else:
                python_exe = venv_path / "bin" / "python"
                pip_exe = venv_path / "bin" / "pip"
            
            # Upgrade pip
            self.progress.emit("Upgrading pip...")
            subprocess.run(
                [str(pip_exe), "install", "--upgrade", "pip"],
                capture_output=True,
                check=False
            )
            
            # Install requirements
            self.progress.emit("Installing dependencies...")
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                result = subprocess.run(
                    [str(pip_exe), "install", "-r", str(requirements_file)],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    self.finished.emit(False, f"Failed to install requirements: {result.stderr}")
                    return
            
            # Install MCP SDK
            self.progress.emit("Installing MCP SDK...")
            result = subprocess.run(
                [str(pip_exe), "install", "mcp[cli]"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                self.finished.emit(False, f"Failed to install MCP SDK: {result.stderr}")
                return
            
            # Generate sample data if requested
            if self.generate_sample_data:
                self.progress.emit("Generating sample data...")
                result = subprocess.run(
                    [str(python_exe), "-m", "scripts.demo"],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    # Non-fatal, just warn
                    self.progress.emit(f"Warning: Sample data generation had issues: {result.stderr}")
            
            self.finished.emit(True, "Setup completed successfully!")
        
        except Exception as e:
            self.finished.emit(False, f"Setup failed: {str(e)}")


class SetupWizard(QWizard):
    """Setup wizard dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DeepTempo AI SOC - Setup Wizard")
        self.setMinimumSize(600, 500)
        
        self.project_root = Path(__file__).parent.parent
        self.worker = None
        
        self._setup_pages()
    
    def _setup_pages(self):
        """Set up wizard pages."""
        # Page 1: Welcome
        welcome_page = QWizardPage()
        welcome_page.setTitle("Welcome")
        layout = QVBoxLayout()
        welcome_label = QLabel(
            "Welcome to the DeepTempo AI SOC Setup Wizard!\n\n"
            "This wizard will help you:\n"
            "• Check Python version (3.10+ required)\n"
            "• Create a virtual environment\n"
            "• Install dependencies\n"
            "• Install MCP SDK\n"
            "• Optionally generate sample data\n\n"
            "Click Next to continue."
        )
        welcome_label.setWordWrap(True)
        layout.addWidget(welcome_label)
        welcome_page.setLayout(layout)
        self.addPage(welcome_page)
        
        # Page 2: Options
        options_page = QWizardPage()
        options_page.setTitle("Setup Options")
        layout = QVBoxLayout()
        
        info_label = QLabel("Select setup options:")
        layout.addWidget(info_label)
        
        self.generate_data_checkbox = QCheckBox("Generate sample data after setup")
        self.generate_data_checkbox.setChecked(True)
        layout.addWidget(self.generate_data_checkbox)
        
        layout.addStretch()
        options_page.setLayout(layout)
        self.addPage(options_page)
        
        # Page 3: Progress
        progress_page = QWizardPage()
        progress_page.setTitle("Setup Progress")
        layout = QVBoxLayout()
        
        self.progress_label = QLabel("Ready to start setup...")
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        progress_page.setLayout(layout)
        self.addPage(progress_page)
        
        # Page 4: Completion
        completion_page = QWizardPage()
        completion_page.setTitle("Setup Complete")
        layout = QVBoxLayout()
        
        self.completion_label = QLabel("Setup completed successfully!")
        layout.addWidget(self.completion_label)
        
        layout.addStretch()
        completion_page.setLayout(layout)
        self.addPage(completion_page)
    
    def initializePage(self, page_id: int):
        """Handle page initialization."""
        if page_id == 2:  # Progress page
            self._start_setup()
        elif page_id == 3:  # Completion page
            self._show_completion()
    
    def _start_setup(self):
        """Start the setup process."""
        generate_data = self.generate_data_checkbox.isChecked()
        
        self.progress_label.setText("Starting setup...")
        self.progress_bar.setRange(0, 0)
        self.log_text.clear()
        
        self.worker = SetupWorker(self.project_root, generate_data)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._setup_finished)
        self.worker.start()
    
    def _update_progress(self, message: str):
        """Update progress display."""
        self.progress_label.setText(message)
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def _setup_finished(self, success: bool, message: str):
        """Handle setup completion."""
        if success:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.progress_label.setText("Setup completed successfully!")
            self.log_text.append("\n" + message)
            # Move to next page
            self.next()
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_label.setText("Setup failed!")
            self.log_text.append("\nERROR: " + message)
            QMessageBox.critical(
                self,
                "Setup Failed",
                f"Setup failed:\n\n{message}\n\nPlease check the logs and try again."
            )
    
    def _show_completion(self):
        """Show completion message."""
        venv_path = self.project_root / "venv"
        if venv_path.exists():
            self.completion_label.setText(
                "Setup completed successfully!\n\n"
                f"Virtual environment created at: {venv_path}\n\n"
                "You can now configure Claude Desktop to use the MCP servers."
            )
        else:
            self.completion_label.setText(
                "Setup completed, but virtual environment was not created.\n\n"
                "Please check the logs for details."
            )

