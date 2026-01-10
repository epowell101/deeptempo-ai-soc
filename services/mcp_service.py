"""MCP service for managing MCP servers."""

import subprocess
import platform
import logging
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class MCPServer:
    """Represents an MCP server process."""
    
    def __init__(self, name: str, command: str, args: List[str], cwd: str, env: Dict[str, str]):
        self.name = name
        self.command = command
        self.args = args
        self.cwd = cwd
        self.env = env
        self.process: Optional[subprocess.Popen] = None
        self.status = "stopped"
        self.start_time: Optional[datetime] = None
    
    def start(self) -> bool:
        """Start the MCP server."""
        if self.process is not None:
            logger.warning(f"Server {self.name} is already running")
            return False
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(self.env)
            
            # Start process
            self.process = subprocess.Popen(
                [self.command] + self.args,
                cwd=self.cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.status = "running"
            self.start_time = datetime.now()
            logger.info(f"Started MCP server: {self.name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start MCP server {self.name}: {e}")
            self.status = "error"
            return False
    
    def stop(self) -> bool:
        """Stop the MCP server."""
        if self.process is None:
            return True
        
        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            
            self.process = None
            self.status = "stopped"
            self.start_time = None
            logger.info(f"Stopped MCP server: {self.name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to stop MCP server {self.name}: {e}")
            return False
    
    def is_running(self) -> bool:
        """Check if the server is running."""
        if self.process is None:
            return False
        
        # Check if process is still alive
        if self.process.poll() is not None:
            self.status = "stopped"
            self.process = None
            return False
        
        return True
    
    def get_status(self) -> str:
        """Get server status."""
        if self.is_running():
            return "running"
        return self.status
    
    def get_log_path(self) -> Path:
        """Get the log file path for this server."""
        log_name = self.name.replace("-", "_")
        return Path(f"/tmp/{log_name}.log")


class MCPService:
    """Service for managing MCP servers."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the MCP service.
        
        Args:
            project_root: Optional project root path. Defaults to parent of services directory.
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root)
        self.venv_path = self.project_root / "venv"
        
        # Determine Python executable
        if platform.system() == "Windows":
            self.python_exe = self.venv_path / "Scripts" / "python.exe"
        else:
            self.python_exe = self.venv_path / "bin" / "python"
        
        # Initialize servers
        self.servers: Dict[str, MCPServer] = {}
        self._initialize_servers()
    
    def _initialize_servers(self):
        """Initialize MCP server configurations."""
        python_exe_str = str(self.python_exe)
        project_path_str = str(self.project_root)
        
        server_configs = [
            {
                "name": "deeptempo-findings",
                "command": python_exe_str,
                "args": ["-m", "mcp_servers.deeptempo_findings_server.server"],
                "cwd": project_path_str,
                "env": {"PYTHONPATH": project_path_str}
            },
            {
                "name": "evidence-snippets",
                "command": python_exe_str,
                "args": ["-m", "mcp_servers.evidence_snippets_server.server"],
                "cwd": project_path_str,
                "env": {"PYTHONPATH": project_path_str}
            },
            {
                "name": "case-store",
                "command": python_exe_str,
                "args": ["-m", "mcp_servers.case_store_server.server"],
                "cwd": project_path_str,
                "env": {"PYTHONPATH": project_path_str}
            }
        ]
        
        for config in server_configs:
            server = MCPServer(**config)
            self.servers[config["name"]] = server
    
    def start_server(self, server_name: str) -> bool:
        """
        Start an MCP server.
        
        Args:
            server_name: Name of the server to start.
        
        Returns:
            True if successful, False otherwise.
        """
        if server_name not in self.servers:
            logger.error(f"Unknown server: {server_name}")
            return False
        
        return self.servers[server_name].start()
    
    def stop_server(self, server_name: str) -> bool:
        """
        Stop an MCP server.
        
        Args:
            server_name: Name of the server to stop.
        
        Returns:
            True if successful, False otherwise.
        """
        if server_name not in self.servers:
            logger.error(f"Unknown server: {server_name}")
            return False
        
        return self.servers[server_name].stop()
    
    def start_all(self) -> Dict[str, bool]:
        """
        Start all MCP servers.
        
        Returns:
            Dictionary mapping server names to success status.
        """
        results = {}
        for name in self.servers:
            results[name] = self.start_server(name)
        return results
    
    def stop_all(self) -> Dict[str, bool]:
        """
        Stop all MCP servers.
        
        Returns:
            Dictionary mapping server names to success status.
        """
        results = {}
        for name in self.servers:
            results[name] = self.stop_server(name)
        return results
    
    def get_server_status(self, server_name: str) -> Optional[str]:
        """
        Get the status of an MCP server.
        
        Args:
            server_name: Name of the server.
        
        Returns:
            Status string or None if server not found.
        """
        if server_name not in self.servers:
            return None
        
        return self.servers[server_name].get_status()
    
    def get_all_statuses(self) -> Dict[str, str]:
        """
        Get status of all servers.
        
        Returns:
            Dictionary mapping server names to status strings.
        """
        statuses = {}
        for name, server in self.servers.items():
            statuses[name] = server.get_status()
        return statuses
    
    def get_server_log(self, server_name: str, lines: int = 100) -> str:
        """
        Get log content for a server.
        
        Args:
            server_name: Name of the server.
            lines: Number of lines to retrieve (from end).
        
        Returns:
            Log content as string.
        """
        if server_name not in self.servers:
            return ""
        
        log_path = self.servers[server_name].get_log_path()
        
        if not log_path.exists():
            return f"Log file not found: {log_path}"
        
        try:
            with open(log_path, 'r') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception as e:
            return f"Error reading log: {e}"
    
    def test_server(self, server_name: str) -> bool:
        """
        Test if a server is responding.
        
        Args:
            server_name: Name of the server to test.
        
        Returns:
            True if server appears to be running, False otherwise.
        """
        if server_name not in self.servers:
            return False
        
        server = self.servers[server_name]
        return server.is_running()
    
    def list_servers(self) -> List[str]:
        """
        List all available servers.
        
        Returns:
            List of server names.
        """
        return list(self.servers.keys())

