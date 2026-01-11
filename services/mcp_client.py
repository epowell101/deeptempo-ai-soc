"""MCP client service for connecting to MCP servers and using their tools."""

import asyncio
import json
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path
import platform
import threading

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import path
        from mcp.client import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
        MCP_AVAILABLE = True
    except ImportError:
        MCP_AVAILABLE = False

from services.mcp_service import MCPService

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for connecting to MCP servers and using their tools."""
    
    def __init__(self, mcp_service: MCPService):
        """
        Initialize MCP client.
        
        Args:
            mcp_service: MCPService instance for managing server processes
        """
        self.mcp_service = mcp_service
        self.sessions: Dict[str, ClientSession] = {}
        self.tools_cache: Dict[str, List[Dict]] = {}
        self._connection_locks: Dict[str, threading.Lock] = {}  # Locks per server to prevent concurrent connections
    
    async def connect_to_server(self, server_name: str) -> bool:
        """
        Connect to an MCP server and cache its tools.
        Note: This connects temporarily to get tools, then disconnects.
        For actual tool calls, we'll reconnect as needed.
        
        Args:
            server_name: Name of the server to connect to
            
        Returns:
            True if successful, False otherwise
        """
        if not MCP_AVAILABLE:
            logger.error("MCP SDK not available")
            return False
        
        if server_name not in self.mcp_service.servers:
            logger.error(f"Unknown server: {server_name}")
            return False
        
        # Get or create lock for this server to prevent concurrent connections
        if server_name not in self._connection_locks:
            self._connection_locks[server_name] = threading.Lock()
        
        # Use lock to prevent concurrent connections to the same server
        with self._connection_locks[server_name]:
            # Check cache inside lock (double-check pattern to prevent race conditions)
            if server_name in self.tools_cache and self.tools_cache[server_name]:
                logger.debug(f"Tools already cached for {server_name}")
                return True
        
        # If we get here, we need to connect (lock is released, but we'll re-check inside)
        server = self.mcp_service.servers[server_name]
        
        # Re-acquire lock for the actual connection
        with self._connection_locks[server_name]:
            # Double-check: another thread might have populated the cache while we were waiting
            if server_name in self.tools_cache and self.tools_cache[server_name]:
                logger.debug(f"Tools were cached by another thread for {server_name}")
                return True
            
            try:
                # Create stdio server parameters
                server_params = StdioServerParameters(
                    command=server.command,
                    args=server.args,
                    env=server.env
                )
                
                # Connect via stdio (temporary connection to get tools)
                async with stdio_client(server_params) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        # Initialize session
                        await session.initialize()
                        
                        # Cache available tools (clear first to prevent duplicates)
                        tools_result = await session.list_tools()
                        # Clear cache before populating to prevent duplicates
                        self.tools_cache[server_name] = []
                        for tool in tools_result.tools:
                            # Get input schema - handle both dict and object formats
                            input_schema = tool.inputSchema
                            if hasattr(input_schema, 'model_dump'):
                                input_schema = input_schema.model_dump()
                            elif hasattr(input_schema, 'dict'):
                                input_schema = input_schema.dict()
                            elif not isinstance(input_schema, dict):
                                input_schema = dict(input_schema) if input_schema else {}
                            
                            # Ensure it's a valid JSON schema
                            if not isinstance(input_schema, dict):
                                input_schema = {}
                            
                            self.tools_cache[server_name].append({
                                "name": tool.name,
                                "description": tool.description or "",
                                "inputSchema": input_schema
                            })
                        
                        logger.info(f"Connected to {server_name}, found {len(self.tools_cache[server_name])} tools")
                        return True
            
            except Exception as e:
                logger.error(f"Failed to connect to {server_name}: {e}")
                return False
    
    async def list_tools(self, server_name: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        List available tools from MCP servers.
        
        Args:
            server_name: Optional server name to list tools from. If None, lists from all servers.
            
        Returns:
            Dictionary mapping server names to lists of tool definitions
        """
        if not MCP_AVAILABLE:
            return {}
        
        tools = {}
        
        if server_name:
            if server_name in self.tools_cache:
                tools[server_name] = self.tools_cache[server_name]
            else:
                # Try to connect and get tools
                if await self.connect_to_server(server_name):
                    tools[server_name] = self.tools_cache.get(server_name, [])
        else:
            # List tools from all servers
            for name in self.mcp_service.list_servers():
                if name in self.tools_cache:
                    tools[name] = self.tools_cache[name]
                else:
                    # Try to connect
                    if await self.connect_to_server(name):
                        tools[name] = self.tools_cache.get(name, [])
        
        return tools
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        """
        Call a tool on an MCP server with timeout.
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            timeout: Timeout in seconds (default: 30)
            
        Returns:
            Tool result dictionary
        """
        if not MCP_AVAILABLE:
            return {"error": "MCP SDK not available", "content": [{"type": "text", "text": "MCP SDK not available"}]}
        
        if server_name not in self.mcp_service.servers:
            return {"error": f"Unknown server: {server_name}", "content": [{"type": "text", "text": f"Unknown server: {server_name}"}]}
        
        server = self.mcp_service.servers[server_name]
        
        async def _call_tool_with_session():
            try:
                # Create connection for this tool call
                server_params = StdioServerParameters(
                    command=server.command,
                    args=server.args,
                    env=server.env
                )
                
                async with stdio_client(server_params) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        # Initialize session
                        await session.initialize()
                        
                        # Call the tool
                        result = await session.call_tool(tool_name, arguments)
                        
                        # Convert result to dictionary
                        content_list = []
                        for content_item in result.content:
                            if hasattr(content_item, 'text'):
                                content_list.append({"type": "text", "text": content_item.text})
                            elif hasattr(content_item, 'type'):
                                content_list.append({"type": str(content_item.type), "text": str(content_item)})
                            else:
                                content_list.append({"type": "text", "text": str(content_item)})
                        
                        return {
                            "error": result.isError if hasattr(result, 'isError') else False,
                            "content": content_list
                        }
            except Exception as e:
                logger.error(f"Error in tool call {tool_name} on {server_name}: {e}")
                raise
        
        try:
            # Apply timeout
            return await asyncio.wait_for(_call_tool_with_session(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Tool call {tool_name} on {server_name} timed out after {timeout}s")
            return {
                "error": True,
                "content": [{"type": "text", "text": f"Tool call timed out after {timeout} seconds. The MCP server may not be responding."}]
            }
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on {server_name}: {e}")
            return {"error": True, "content": [{"type": "text", "text": f"Error: {str(e)}"}]}
    
    def get_tools_for_claude(self) -> List[Dict]:
        """
        Get all available tools formatted for Claude's tool use API.
        
        Returns:
            List of tool definitions in Claude's format
        """
        all_tools = []
        
        for server_name, tools in self.tools_cache.items():
            for tool in tools:
                # Format tool for Claude API
                claude_tool = {
                    "name": f"{server_name}_{tool['name']}",
                    "description": f"[{server_name}] {tool['description']}",
                    "input_schema": tool.get("inputSchema", {})
                }
                all_tools.append(claude_tool)
        
        return all_tools
    
    async def close_all(self):
        """Close all MCP server connections and clear cache."""
        self.sessions.clear()
        self.tools_cache.clear()


# Global MCP client instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> Optional[MCPClient]:
    """Get or create the global MCP client instance."""
    global _mcp_client
    
    if not MCP_AVAILABLE:
        logger.warning("MCP SDK not available. Install with: pip install mcp")
        return None
    
    if _mcp_client is None:
        mcp_service = MCPService()
        _mcp_client = MCPClient(mcp_service)
    
    return _mcp_client

