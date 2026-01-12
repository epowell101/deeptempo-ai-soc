"""MCP service for managing MCP servers."""

import subprocess
import platform
import logging
import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class MCPServer:
    """Represents an MCP server process."""
    
    def __init__(self, name: str, command: str, args: List[str], cwd: str, env: Dict[str, str], server_type: str = "unknown"):
        self.name = name
        self.command = command
        self.args = args
        self.cwd = cwd
        self.env = env
        self.process: Optional[subprocess.Popen] = None
        self.status = "stopped"
        self.start_time: Optional[datetime] = None
        self.server_type = server_type  # "fastmcp" or "stdio"
    
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
        # First check if we have a process object and it's still alive
        if self.process is not None:
            if self.process.poll() is None:
                # Process is still running
                return True
            else:
                # Process has terminated
                self.status = "stopped"
                self.process = None
                return False
        
        # If no process object, check if the process is running externally
        # by checking for the process by command line arguments
        try:
            # Extract module name from args (e.g., "mcp_servers.deeptempo_findings_server.server" -> "deeptempo_findings_server")
            module_name = None
            for arg in self.args:
                if arg.startswith("mcp_servers."):
                    parts = arg.split(".")
                    if len(parts) >= 2:
                        module_name = parts[1]  # Get the module name (e.g., deeptempo_findings_server)
                    break
            
            if module_name:
                # On Unix systems (macOS, Linux), use pgrep
                if platform.system() != "Windows":
                    try:
                        result = subprocess.run(
                            ["pgrep", "-f", f"mcp_servers.*{module_name}"],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            self.status = "running"
                            return True
                    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                        pass
                else:
                    # On Windows, use tasklist with findstr
                    try:
                        result = subprocess.run(
                            ["tasklist", "/FI", f"IMAGENAME eq python.exe", "/FO", "CSV"],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        if result.returncode == 0 and module_name in result.stdout:
                            self.status = "running"
                            return True
                    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                        pass
        except Exception as e:
            logger.debug(f"Error checking external process status: {e}")
        
        return False
    
    def get_status(self) -> str:
        """Get server status."""
        if self.server_type == "stdio":
            return "stdio (Claude Desktop)"
        if self.is_running():
            return "running"
        return self.status
    
    def get_log_path(self) -> Path:
        """Get the log file path for this server."""
        # Keep hyphens as servers log to files with hyphens (e.g., deeptempo-findings.log)
        return Path(f"/tmp/{self.name}.log")


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
    
    def _detect_server_type(self, args: List[str]) -> str:
        """
        Detect if a server is FastMCP or stdio-based by checking the module path.
        
        FastMCP servers: deeptempo_findings_server, evidence_snippets_server, case_store_server
        Stdio servers: All others (designed for Claude Desktop integration)
        """
        # Extract module name from args
        for arg in args:
            if "." in arg and arg.startswith("mcp_servers"):
                # Check if it's one of the known FastMCP servers
                fastmcp_servers = [
                    "deeptempo_findings_server",
                    "evidence_snippets_server",
                    "case_store_server"
                ]
                
                for fastmcp in fastmcp_servers:
                    if fastmcp in arg:
                        return "fastmcp"
                
                # All others are stdio-based
                return "stdio"
        
        return "unknown"
    
    def _initialize_servers(self):
        """
        Initialize MCP server configurations from mcp-config.json.
        
        Loads server configurations dynamically from the mcp-config.json file
        to ensure consistency with Claude Desktop integration.
        """
        python_exe_str = str(self.python_exe)
        project_path_str = str(self.project_root)
        
        # Load servers from mcp-config.json
        mcp_config_path = self.project_root / "mcp-config.json"
        server_configs = []
        
        if mcp_config_path.exists():
            try:
                with open(mcp_config_path, 'r') as f:
                    mcp_config = json.load(f)
                    
                for server_name, server_config in mcp_config.get("mcpServers", {}).items():
                    # Convert config format from mcp-config.json to our internal format
                    command = server_config.get("command", "python")
                    
                    # Use venv python if command is just "python"
                    if command == "python":
                        command = python_exe_str
                    
                    # Get cwd, replace ${workspaceFolder} with actual path
                    cwd = server_config.get("cwd", project_path_str)
                    if "${workspaceFolder}" in cwd:
                        cwd = cwd.replace("${workspaceFolder}", project_path_str)
                    
                    # Get environment variables
                    env = server_config.get("env", {}).copy()
                    env["PYTHONPATH"] = project_path_str
                    
                    args = server_config.get("args", [])
                    
                    server_configs.append({
                        "name": server_name,
                        "command": command,
                        "args": args,
                        "cwd": cwd,
                        "env": env,
                        "server_type": self._detect_server_type(args)
                    })
                    
                logger.info(f"Loaded {len(server_configs)} servers from mcp-config.json")
            except Exception as e:
                logger.error(f"Error loading mcp-config.json: {e}")
                # Fall back to default servers if config loading fails
                server_configs = self._get_default_servers(python_exe_str, project_path_str)
        else:
            logger.warning("mcp-config.json not found, using default servers")
            server_configs = self._get_default_servers(python_exe_str, project_path_str)
        
        for config in server_configs:
            server = MCPServer(**config)
            self.servers[config["name"]] = server
    
    def _get_default_servers(self, python_exe_str: str, project_path_str: str) -> List[Dict]:
        """Get default server configurations if mcp-config.json is not available."""
        return [
            {
                "name": "deeptempo-findings",
                "command": python_exe_str,
                "args": ["-m", "mcp_servers.deeptempo_findings_server.server"],
                "cwd": project_path_str,
                "env": {"PYTHONPATH": project_path_str},
                "server_type": "fastmcp"
            },
            {
                "name": "evidence-snippets",
                "command": python_exe_str,
                "args": ["-m", "mcp_servers.evidence_snippets_server.server"],
                "cwd": project_path_str,
                "env": {"PYTHONPATH": project_path_str},
                "server_type": "fastmcp"
            },
            {
                "name": "case-store",
                "command": python_exe_str,
                "args": ["-m", "mcp_servers.case_store_server.server"],
                "cwd": project_path_str,
                "env": {"PYTHONPATH": project_path_str},
                "server_type": "fastmcp"
            }
        ]
    
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
        
        server = self.servers[server_name]
        
        # Check if it's a stdio-based server
        if server.server_type == "stdio":
            logger.warning(f"Server {server_name} is stdio-based and designed for Claude Desktop integration, not standalone monitoring")
            return False
        
        return server.start()
    
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
            return f"Log file not yet created. Start the server to generate logs.\n\nExpected log path: {log_path}"
        
        try:
            with open(log_path, 'r') as f:
                all_lines = f.readlines()
                if not all_lines:
                    return f"Log file is empty. Server may not have started yet.\n\nLog path: {log_path}"
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

