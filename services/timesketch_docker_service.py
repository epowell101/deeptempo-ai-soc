"""Docker management service for Timesketch server."""

import subprocess
import logging
import time
import platform
import os
from typing import Optional, Dict, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class TimesketchDockerService:
    """Service for managing Timesketch Docker container."""
    
    CONTAINER_NAME = "timesketch"
    # Note: timesketch/timesketch doesn't exist as a single image
    # Timesketch requires docker-compose with multiple services
    # This is a placeholder - users should use docker-compose or configure their own image
    DEFAULT_IMAGE = "timesketch/timesketch"
    DEFAULT_PORT = 5000
    
    def __init__(self, container_name: Optional[str] = None, image: Optional[str] = None,
                 docker_compose_path: Optional[str] = None):
        """
        Initialize Docker service.
        
        Args:
            container_name: Docker container name (default: "timesketch")
            image: Docker image name (None means not configured, will require docker-compose or custom image)
            docker_compose_path: Path to docker-compose.yml file (if using docker-compose)
        """
        self.container_name = container_name or self.CONTAINER_NAME
        # Store the provided image, or None if not provided
        # We don't use DEFAULT_IMAGE automatically to prevent trying non-existent images
        self.image = image
        self.docker_compose_path = docker_compose_path
        self._docker_available = self._check_docker_available()
    
    def _check_docker_available(self) -> bool:
        """Check if Docker CLI is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def is_docker_available(self) -> bool:
        """Check if Docker CLI is available."""
        return self._docker_available
    
    def is_docker_daemon_running(self) -> bool:
        """
        Check if Docker daemon is running.
        
        Returns:
            True if Docker daemon is running, False otherwise.
        """
        if not self._docker_available:
            return False
        
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"Docker daemon check failed: {e}")
            return False
    
    def get_docker_daemon_status(self) -> Dict:
        """
        Get Docker daemon status information.
        
        Returns:
            Dictionary with daemon status information.
        """
        if not self._docker_available:
            return {
                "cli_available": False,
                "daemon_running": False,
                "error": "Docker CLI is not installed"
            }
        
        daemon_running = self.is_docker_daemon_running()
        
        return {
            "cli_available": True,
            "daemon_running": daemon_running,
            "error": None if daemon_running else "Docker daemon is not running"
        }
    
    def start_docker_daemon(self) -> Tuple[bool, str]:
        """
        Start Docker daemon (platform-specific).
        
        Returns:
            Tuple of (success, message)
        """
        if not self._docker_available:
            return False, "Docker CLI is not installed. Please install Docker Desktop."
        
        if self.is_docker_daemon_running():
            return True, "Docker daemon is already running"
        
        system = platform.system().lower()
        
        try:
            if system == "darwin":  # macOS
                # Try to open Docker Desktop
                result = subprocess.run(
                    ["open", "-a", "Docker"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    # Wait a bit for Docker to start
                    logger.info("Docker Desktop launch command executed. Waiting for daemon to start...")
                    
                    # Poll for up to 30 seconds to see if daemon starts
                    for _ in range(30):
                        time.sleep(1)
                        if self.is_docker_daemon_running():
                            return True, "Docker daemon started successfully"
                    
                    return False, "Docker Desktop was launched, but daemon did not start within 30 seconds. Please check Docker Desktop."
                else:
                    return False, "Failed to launch Docker Desktop. Please start Docker Desktop manually."
            
            elif system == "linux":
                # Try to start Docker service
                result = subprocess.run(
                    ["sudo", "systemctl", "start", "docker"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    # Wait a bit for Docker to start
                    time.sleep(2)
                    if self.is_docker_daemon_running():
                        return True, "Docker daemon started successfully"
                    else:
                        return False, "Docker service started but daemon is not responding"
                else:
                    # Try without sudo (might be in docker group)
                    result = subprocess.run(
                        ["systemctl", "--user", "start", "docker"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        time.sleep(2)
                        if self.is_docker_daemon_running():
                            return True, "Docker daemon started successfully"
                    
                    return False, f"Failed to start Docker service. Error: {result.stderr}. Please start Docker manually."
            
            elif system == "windows":
                # On Windows, try to start Docker Desktop
                result = subprocess.run(
                    ["cmd", "/c", "start", "docker"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    # Wait for Docker to start
                    for _ in range(30):
                        time.sleep(1)
                        if self.is_docker_daemon_running():
                            return True, "Docker daemon started successfully"
                    
                    return False, "Docker Desktop was launched, but daemon did not start within 30 seconds. Please check Docker Desktop."
                else:
                    return False, "Failed to launch Docker Desktop. Please start Docker Desktop manually."
            
            else:
                return False, f"Unsupported platform: {system}. Please start Docker manually."
        
        except subprocess.TimeoutExpired:
            return False, "Command timed out while trying to start Docker"
        except Exception as e:
            logger.error(f"Error starting Docker daemon: {e}")
            return False, f"Error starting Docker daemon: {str(e)}"
    
    def is_container_running(self) -> bool:
        """Check if Timesketch container(s) are running."""
        if not self._docker_available:
            return False
        
        # If using docker-compose, check for timesketch-web (main container from deploy script)
        if self.docker_compose_path:
            try:
                compose_file = Path(self.docker_compose_path)
                compose_dir = compose_file.parent
                # Check if timesketch-web container is running (main container from deploy script)
                result = subprocess.run(
                    ["docker", "ps", "--filter", "name=timesketch-web", "--format", "{{.Names}}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return "timesketch-web" in result.stdout
            except (subprocess.TimeoutExpired, Exception) as e:
                logger.error(f"Error checking docker-compose container status: {e}")
                return False
        
        # For single container setup
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return self.container_name in result.stdout
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.error(f"Error checking container status: {e}")
            return False
    
    def get_container_status(self) -> Dict:
        """
        Get detailed container status.
        
        Returns:
            Dictionary with status information.
        """
        if not self._docker_available:
            return {
                "available": False,
                "running": False,
                "error": "Docker is not available"
            }
        
        # If using docker-compose, check for timesketch-web (main container)
        if self.docker_compose_path:
            try:
                compose_file = Path(self.docker_compose_path)
                compose_dir = compose_file.parent
                
                # Check if timesketch-web exists
                result = subprocess.run(
                    ["docker", "ps", "-a", "--filter", "name=timesketch-web", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if "timesketch-web" not in result.stdout:
                    return {
                        "available": True,
                        "running": False,
                        "exists": False,
                        "status": "not_found",
                        "note": "docker-compose setup - containers not created yet"
                    }
                
                # Parse status
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if "timesketch-web" in line:
                        parts = line.split('|')
                        status_text = parts[1] if len(parts) > 1 else ""
                        ports = parts[2] if len(parts) > 2 else ""
                        
                        is_running = "Up" in status_text
                        
                        return {
                            "available": True,
                            "running": is_running,
                            "exists": True,
                            "status": "running" if is_running else "stopped",
                            "status_text": status_text,
                            "ports": ports,
                            "note": "docker-compose setup"
                        }
                
                return {
                    "available": True,
                    "running": False,
                    "exists": False,
                    "status": "not_found"
                }
            except Exception as e:
                logger.error(f"Error getting docker-compose container status: {e}")
                return {
                    "available": True,
                    "running": False,
                    "error": str(e)
                }
        
        # For single container setup
        try:
            # Check if container exists
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if self.container_name not in result.stdout:
                return {
                    "available": True,
                    "running": False,
                    "exists": False,
                    "status": "not_found"
                }
            
            # Parse status
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if self.container_name in line:
                    parts = line.split('|')
                    status_text = parts[1] if len(parts) > 1 else ""
                    ports = parts[2] if len(parts) > 2 else ""
                    
                    is_running = "Up" in status_text
                    
                    return {
                        "available": True,
                        "running": is_running,
                        "exists": True,
                        "status": "running" if is_running else "stopped",
                        "status_text": status_text,
                        "ports": ports
                    }
            
            return {
                "available": True,
                "running": False,
                "exists": False,
                "status": "not_found"
            }
        
        except Exception as e:
            logger.error(f"Error getting container status: {e}")
            return {
                "available": True,
                "running": False,
                "error": str(e)
            }
    
    def start_container(self, port: int = None) -> Tuple[bool, str]:
        """
        Start Timesketch container.
        
        Args:
            port: Port to map (default: 5000)
        
        Returns:
            Tuple of (success, message)
        """
        if not self._docker_available:
            return False, "Docker CLI is not available. Please install Docker."
        
        # Check if Docker daemon is running
        if not self.is_docker_daemon_running():
            return False, "Docker daemon is not running. Please start Docker first."
        
        port = port or self.DEFAULT_PORT
        
        # Check if already running
        if self.is_container_running():
            return True, f"Container '{self.container_name}' is already running"
        
        try:
            # Check if using docker-compose FIRST (preferred method for Timesketch)
            if self.docker_compose_path:
                compose_file = Path(self.docker_compose_path)
                if compose_file.exists():
                    return self._start_with_docker_compose()
                else:
                    return False, (
                        f"Docker compose file not found: {self.docker_compose_path}\n\n"
                        "Please check the path in Settings → Timesketch → Docker Compose File"
                    )
            
            # For single container setup (only if docker-compose is not configured)
            # Check if container exists but is stopped
            # Use exact name matching by checking each line
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Check for exact match (not substring match)
            container_names = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            if self.container_name in container_names:
                # Container exists but is stopped - start it
                logger.info(f"Starting existing container: {self.container_name}")
                result = subprocess.run(
                    ["docker", "start", self.container_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Wait a bit for container to be ready
                    time.sleep(2)
                    if self.is_container_running():
                        return True, f"Container '{self.container_name}' started successfully"
                    else:
                        return False, "Container started but is not running"
                else:
                    return False, f"Failed to start container: {result.stderr}"
            else:
                # Container doesn't exist - create and run it
                
                # Check if image is configured (must be provided, not None or default)
                if not self.image:
                    return False, (
                        "Timesketch Docker configuration required.\n\n"
                        "Timesketch requires a multi-service setup and doesn't have a single-container image.\n\n"
                        "Please configure one of the following:\n"
                        "1. Docker Compose File: Set the path to docker-compose.yml in Settings\n"
                        "2. Custom Docker Image: Enter a custom image name in Settings\n"
                        "3. Existing Server: Configure an existing Timesketch server URL instead\n\n"
                        "Click 'View Timesketch Docker Setup Instructions' for detailed setup steps.\n\n"
                        "For official documentation, see: https://timesketch.org/guides/admin/install-docker/"
                    )
                
                # Use custom image if configured
                logger.info(f"Creating and starting new container with image: {self.image}")
                cmd = [
                    "docker", "run", "-d",
                    "-p", f"{port}:5000",
                    "--name", self.container_name,
                    self.image
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    # Wait a bit for container to be ready
                    time.sleep(3)
                    if self.is_container_running():
                        return True, f"Container '{self.container_name}' created and started successfully"
                    else:
                        return False, "Container created but is not running"
                else:
                    error_msg = result.stderr.strip() or result.stdout.strip()
                    
                    # Provide helpful error message for image pull failures
                    if "pull access denied" in error_msg or "repository does not exist" in error_msg:
                        return False, (
                            f"Failed to pull Docker image '{self.image}':\n\n"
                            f"{error_msg}\n\n"
                            "The specified Docker image could not be found or requires authentication.\n\n"
                            "Please:\n"
                            "1. Verify the image name is correct\n"
                            "2. Ensure you're logged in to the registry (docker login)\n"
                            "3. Or configure docker-compose instead (recommended for Timesketch)\n\n"
                            "For setup instructions, see: https://timesketch.org/guides/admin/install-docker/"
                        )
                    
                    return False, f"Failed to create container: {error_msg}"
        
        except subprocess.TimeoutExpired:
            return False, "Docker command timed out"
        except Exception as e:
            logger.error(f"Error starting container: {e}")
            return False, f"Error: {str(e)}"
    
    def stop_container(self) -> Tuple[bool, str]:
        """
        Stop Timesketch container(s).
        
        Returns:
            Tuple of (success, message)
        """
        if not self._docker_available:
            return False, "Docker is not available"
        
        if not self.is_container_running():
            return True, "Timesketch containers are not running"
        
        # If using docker-compose, stop all services
        if self.docker_compose_path:
            try:
                compose_file = Path(self.docker_compose_path)
                compose_dir = compose_file.parent
                compose_filename = compose_file.name
                
                # Check which docker compose command to use
                result = subprocess.run(
                    ["docker", "compose", "version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    compose_cmd = ["docker", "compose"]
                else:
                    compose_cmd = ["docker-compose"]
                
                # Stop services: docker compose stop (or down to remove)
                cmd = compose_cmd + ["-f", compose_filename, "stop"]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=compose_dir
                )
                
                if result.returncode == 0:
                    return True, "Timesketch services stopped successfully"
                else:
                    error_msg = result.stderr.strip() or result.stdout.strip()
                    return False, f"Failed to stop docker-compose services: {error_msg}"
            
            except Exception as e:
                logger.error(f"Error stopping docker-compose services: {e}")
                return False, f"Error stopping services: {str(e)}"
        
        # For single container setup
        try:
            result = subprocess.run(
                ["docker", "stop", self.container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, f"Container '{self.container_name}' stopped successfully"
            else:
                return False, f"Failed to stop container: {result.stderr}"
        
        except subprocess.TimeoutExpired:
            return False, "Docker command timed out"
        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            return False, f"Error: {str(e)}"
    
    def remove_container(self) -> Tuple[bool, str]:
        """
        Remove Timesketch container (must be stopped first).
        
        Returns:
            Tuple of (success, message)
        """
        if not self._docker_available:
            return False, "Docker is not available"
        
        # Stop first if running
        if self.is_container_running():
            self.stop_container()
            time.sleep(1)
        
        try:
            result = subprocess.run(
                ["docker", "rm", self.container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, f"Container '{self.container_name}' removed successfully"
            else:
                if "No such container" in result.stderr:
                    return True, f"Container '{self.container_name}' does not exist"
                return False, f"Failed to remove container: {result.stderr}"
        
        except subprocess.TimeoutExpired:
            return False, "Docker command timed out"
        except Exception as e:
            logger.error(f"Error removing container: {e}")
            return False, f"Error: {str(e)}"
    
    def _start_with_docker_compose(self) -> Tuple[bool, str]:
        """
        Start Timesketch using docker-compose.
        Matches the behavior of deploy_timesketch.sh script.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.docker_compose_path:
            return False, "Docker compose path not configured"
        
        compose_file = Path(self.docker_compose_path)
        if not compose_file.exists():
            return False, f"Docker compose file not found: {self.docker_compose_path}"
        
        # Use the directory containing docker-compose file as working directory
        # This matches deploy_timesketch.sh which runs from the timesketch directory
        compose_dir = compose_file.parent
        
        try:
            # Check if docker compose (v2) is available - match deploy_timesketch.sh check
            # The script uses: if ! docker compose &>/dev/null
            result = subprocess.run(
                ["docker", "compose", "version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                compose_cmd = ["docker", "compose"]
            else:
                # Try legacy docker-compose command (v1)
                result = subprocess.run(
                    ["docker-compose", "--version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    compose_cmd = ["docker-compose"]
                else:
                    return False, (
                        "Docker Compose is not available.\n\n"
                        "The deploy_timesketch.sh script requires 'docker compose' (v2 plugin).\n\n"
                        "Please install Docker Compose:\n"
                        "- Docker Compose v2 is included with Docker Desktop\n"
                        "- For Ubuntu: sudo apt-get install docker-compose-plugin\n"
                        "- See: https://docs.docker.com/compose/install/"
                    )
            
            # Check if .env file exists (created by deploy_timesketch.sh)
            env_file = compose_dir / ".env"
            config_env = compose_dir / "config.env"
            if not env_file.exists() and config_env.exists():
                # The script creates a symlink: ln -s ./config.env ./timesketch/.env
                # If .env doesn't exist but config.env does, create it
                try:
                    if platform.system() == "Windows":
                        # Windows doesn't support symlinks easily, so copy
                        import shutil
                        shutil.copy(config_env, env_file)
                    else:
                        # Create symlink
                        env_file.symlink_to("config.env")
                except Exception as e:
                    logger.warning(f"Could not create .env symlink: {e}")
                    # Fallback to copy
                    try:
                        import shutil
                        shutil.copy(config_env, env_file)
                    except Exception:
                        pass
            
            # Ensure required directories exist (for volume mounts)
            # These paths match what's in config.env
            # IMPORTANT: Create parent directories first (data, etc) before subdirectories
            # Use absolute paths to avoid any path resolution issues
            compose_dir_abs = compose_dir.resolve()
            
            parent_dirs = [
                compose_dir_abs / "data",
                compose_dir_abs / "etc",
                compose_dir_abs / "logs",
                compose_dir_abs / "upload",
            ]
            for parent_dir in parent_dirs:
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                    if platform.system() != "Windows":
                        os.chmod(parent_dir, 0o755)
                    # Verify it exists
                    if not parent_dir.exists():
                        raise OSError(f"Failed to create {parent_dir}")
                    logger.info(f"Verified directory exists: {parent_dir}")
                except Exception as e:
                    logger.error(f"Could not create parent directory {parent_dir}: {e}")
                    return False, (
                        f"Failed to create required directory: {parent_dir}\n\n"
                        f"Error: {str(e)}\n\n"
                        f"Please ensure you have write permissions to: {compose_dir_abs}\n\n"
                        f"Try creating the directory manually:\n"
                        f"  mkdir -p {parent_dir}\n"
                        f"  chmod 755 {parent_dir}"
                    )
            
            required_dirs = [
                compose_dir_abs / "data" / "postgresql",
                compose_dir_abs / "data" / "opensearch",
                compose_dir_abs / "logs",
                compose_dir_abs / "upload",
                compose_dir_abs / "etc" / "timesketch",  # For TIMESKETCH_CONFIG_PATH
            ]
            for dir_path in required_dirs:
                try:
                    # Create with parents=True to ensure all parent directories exist
                    dir_path.mkdir(parents=True, exist_ok=True)
                    # Ensure directories have proper permissions (readable/writable)
                    if platform.system() != "Windows":
                        # Set permissions: owner read/write/execute, group/others read/execute
                        os.chmod(dir_path, 0o755)
                        # Also ensure parent directories have correct permissions
                        parent = dir_path.parent
                        while parent != compose_dir.parent:
                            try:
                                os.chmod(parent, 0o755)
                            except (OSError, PermissionError):
                                pass  # May not have permission to change parent
                            parent = parent.parent
                    
                    # Verify directory was created and is accessible
                    if not dir_path.exists():
                        raise OSError(f"Directory {dir_path} was not created")
                    
                    # Log successful creation
                    logger.info(f"Verified directory exists: {dir_path}")
                    
                    # On macOS, verify Docker can access the directory
                    # Docker Desktop on macOS uses /host_mnt prefix
                    if platform.system() == "Darwin":
                        # Try to verify the directory is readable/writable
                        try:
                            test_file = dir_path / ".docker_test"
                            test_file.touch()
                            if not test_file.exists():
                                raise OSError(f"Cannot write to {dir_path}")
                            test_file.unlink()
                            logger.info(f"Verified Docker can access: {dir_path}")
                        except Exception as e:
                            logger.warning(f"Could not verify Docker access to {dir_path}: {e}")
                            # Don't fail - Docker might still be able to access it
                            # But log a warning about potential Docker Desktop file sharing issues
                            
                except Exception as e:
                    logger.error(f"Could not create directory {dir_path}: {e}")
                    # This is critical - return error if we can't create required directories
                    return False, (
                        f"Failed to create required directory: {dir_path}\n\n"
                        f"Error: {str(e)}\n\n"
                        f"Please ensure you have write permissions to: {compose_dir}\n\n"
                        f"Try creating the directory manually:\n"
                        f"  mkdir -p {dir_path}\n"
                        f"  chmod 755 {dir_path}\n\n"
                        f"On macOS, also ensure Docker Desktop has file sharing enabled for /Users"
                    )
            
            # Final verification: ensure all directories exist before starting docker-compose
            # This is especially important on macOS where Docker Desktop uses /host_mnt
            logger.info(f"Final verification of directories before starting docker-compose...")
            for dir_path in required_dirs:
                if not dir_path.exists():
                    return False, (
                        f"Directory verification failed: {dir_path} does not exist\n\n"
                        f"This may be a Docker Desktop file sharing issue on macOS.\n\n"
                        f"Please:\n"
                        f"1. Check Docker Desktop → Settings → Resources → File Sharing\n"
                        f"2. Ensure /Users is in the shared folders list\n"
                        f"3. Restart Docker Desktop if needed\n"
                        f"4. Try creating the directory manually:\n"
                        f"   mkdir -p {dir_path}"
                    )
            
            # On macOS, add a small delay to ensure Docker Desktop has processed the directory changes
            if platform.system() == "Darwin":
                time.sleep(0.5)
                logger.info("Added delay for macOS Docker Desktop file system sync")
            
            # Start services - match deploy_timesketch.sh: docker compose up -d
            # When in the correct directory, we can use just the filename with -f
            # Or use the full path - both should work, but filename is cleaner
            compose_filename = compose_file.name
            cmd = compose_cmd + ["-f", compose_filename, "up", "-d"]
            
            logger.info(f"Running docker-compose command: {' '.join(cmd)} in {compose_dir}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout (matching script's health check timeout)
                cwd=compose_dir
            )
            
            if result.returncode == 0:
                # Wait a moment for services to start
                time.sleep(2)
                
                return True, (
                    f"Timesketch services started successfully using docker-compose.\n\n"
                    f"Services are starting in the background. This may take a few minutes.\n\n"
                    f"Next steps:\n"
                    f"1. Wait for services to become healthy (check with: docker compose ps)\n"
                    f"2. Create a user: docker compose exec timesketch-web tsctl create-user <USERNAME>\n"
                    f"3. Access Timesketch at: http://localhost (or your server IP)\n\n"
                    f"Check status: docker compose -f {compose_file.name} ps\n"
                    f"View logs: docker compose -f {compose_file.name} logs"
                )
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                
                # Provide helpful error messages based on common issues
                if "permission denied" in error_msg.lower():
                    return False, (
                        f"Permission denied when starting docker-compose:\n\n{error_msg}\n\n"
                        f"The deploy_timesketch.sh script requires root/sudo access.\n"
                        f"If you're running this from the GUI, you may need to:\n"
                        f"1. Run the application with appropriate permissions, or\n"
                        f"2. Add your user to the docker group: sudo usermod -aG docker $USER\n"
                        f"   (then log out and back in)\n\n"
                        f"Alternatively, start Timesketch manually:\n"
                        f"  cd {compose_dir}\n"
                        f"  sudo docker compose up -d"
                    )
                
                return False, (
                    f"Failed to start docker-compose services:\n\n{error_msg}\n\n"
                    f"Troubleshooting:\n"
                    f"1. Check if Docker daemon is running\n"
                    f"2. Verify docker-compose.yml is valid\n"
                    f"3. Check logs: docker compose -f {compose_file.name} logs\n"
                    f"4. Try running manually: cd {compose_dir} && docker compose up -d"
                )
        
        except subprocess.TimeoutExpired:
            return False, (
                "Docker compose command timed out after 5 minutes.\n\n"
                "Services may still be starting. Check status with:\n"
                f"  cd {compose_dir}\n"
                f"  docker compose ps"
            )
        except Exception as e:
            logger.error(f"Error starting docker-compose: {e}")
            return False, (
                f"Error starting docker-compose: {str(e)}\n\n"
                f"Make sure:\n"
                f"1. Docker is installed and running\n"
                f"2. Docker Compose plugin is installed\n"
                f"3. You have permission to run docker commands\n"
                f"4. The docker-compose.yml file is valid"
            )
    
    def get_container_logs(self, lines: int = 50) -> str:
        """
        Get container logs.
        
        Args:
            lines: Number of log lines to retrieve
        
        Returns:
            Log output as string
        """
        if not self._docker_available:
            return "Docker is not available"
        
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines), self.container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error getting logs: {result.stderr}"
        
        except Exception as e:
            return f"Error: {str(e)}"

