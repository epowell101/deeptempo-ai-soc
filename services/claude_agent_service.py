"""Claude Agent SDK service - alternative implementation using Agent SDK."""

import logging
import json
import asyncio
from typing import Optional, List, Dict, AsyncIterator, Union
from pathlib import Path
import keyring

try:
    from claude_agent_sdk import query, ClaudeAgentOptions
    from claude_agent_sdk.tools import Tool
    AGENT_SDK_AVAILABLE = True
except ImportError:
    AGENT_SDK_AVAILABLE = False
    print("Claude Agent SDK not installed. Install with: pip install claude-agent-sdk")

logger = logging.getLogger(__name__)


class ClaudeAgentService:
    """Service for interacting with Claude using the Agent SDK."""
    
    SERVICE_NAME = "deeptempo-ai-soc"
    API_KEY_NAME = "claude_api_key"
    
    def __init__(self, use_mcp_tools: bool = True, enable_thinking: bool = False, thinking_budget: int = 10000):
        """
        Initialize Claude Agent service.
        
        Args:
            use_mcp_tools: Whether to enable MCP tool integration
            enable_thinking: Whether to enable extended thinking
            thinking_budget: Token budget for extended thinking
        """
        if not AGENT_SDK_AVAILABLE:
            raise ImportError("claude-agent-sdk not installed. Run: pip install claude-agent-sdk")
        
        self.api_key: Optional[str] = None
        self.use_mcp_tools = use_mcp_tools
        self.mcp_tools: List[Dict] = []
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget
        
        # Default system prompt
        self.default_system_prompt = self._get_default_system_prompt()
        
        # Try to load API key
        self._load_api_key()
        
        # Load MCP tools if enabled
        if self.use_mcp_tools:
            self._load_mcp_tools()
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt."""
        return """You are Claude, an AI assistant for security operations and analysis.

When working with security findings and cases:
- Provide clear, actionable analysis
- Use available tools to gather information
- Correlate findings when patterns emerge
- Be thorough but efficient in your analysis"""
    
    def _load_api_key(self) -> bool:
        """Load API key from secure storage."""
        try:
            # Try keyring first
            try:
                self.api_key = keyring.get_password(self.SERVICE_NAME, self.API_KEY_NAME)
                if not self.api_key:
                    self.api_key = keyring.get_password(self.SERVICE_NAME, "anthropic_api_key")
            except Exception:
                pass
            
            # Fallback to config file
            if not self.api_key:
                config_file = Path.home() / ".deeptempo" / "config.json"
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        self.api_key = config.get('anthropic_api_key') or config.get('claude_api_key')
            
            # Check environment variable
            if not self.api_key:
                import os
                self.api_key = os.environ.get('ANTHROPIC_API_KEY')
            
            return self.api_key is not None
        
        except Exception as e:
            logger.error(f"Error loading API key: {e}")
            return False
    
    def _load_mcp_tools(self):
        """Load MCP tools for Claude to use."""
        self.mcp_tools = []
        
        try:
            from services.mcp_client import get_mcp_client
            
            mcp_client = get_mcp_client()
            if mcp_client:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    tools_dict = loop.run_until_complete(mcp_client.list_tools())
                    seen_tool_names = set()
                    
                    for server_name, server_tools in tools_dict.items():
                        for tool in server_tools:
                            tool_name = f"{server_name}_{tool['name']}"
                            
                            if tool_name in seen_tool_names:
                                continue
                            seen_tool_names.add(tool_name)
                            
                            input_schema = tool.get("inputSchema", {})
                            if hasattr(input_schema, 'model_dump'):
                                input_schema = input_schema.model_dump()
                            elif not isinstance(input_schema, dict):
                                input_schema = dict(input_schema) if input_schema else {}
                            
                            if not input_schema or "type" not in input_schema:
                                input_schema = {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            
                            # Store tool metadata for Agent SDK tool conversion
                            self.mcp_tools.append({
                                "name": tool_name,
                                "server_name": server_name,
                                "actual_name": tool['name'],
                                "description": f"[{server_name}] {tool.get('description', '')}",
                                "input_schema": input_schema
                            })
                    
                    logger.info(f"Loaded {len(self.mcp_tools)} MCP tools from {len(tools_dict)} servers")
                finally:
                    loop.close()
        except Exception as e:
            logger.warning(f"Could not load MCP tools: {e}")
            self.mcp_tools = []
    
    def _convert_mcp_tools_to_agent_sdk(self) -> List[Tool]:
        """Convert MCP tools to Agent SDK Tool format."""
        agent_tools = []
        
        for mcp_tool in self.mcp_tools:
            # Create a tool execution function
            async def execute_tool(tool_data=mcp_tool, **kwargs):
                from services.mcp_client import get_mcp_client
                mcp_client = get_mcp_client()
                if mcp_client:
                    result = await mcp_client.call_tool(
                        tool_data["server_name"],
                        tool_data["actual_name"],
                        kwargs,
                        timeout=30.0
                    )
                    return result
                return {"error": "MCP client not available"}
            
            # Create Agent SDK tool
            agent_tool = Tool(
                name=mcp_tool["name"],
                description=mcp_tool["description"],
                parameters=mcp_tool["input_schema"],
                function=execute_tool
            )
            agent_tools.append(agent_tool)
        
        return agent_tools
    
    def set_api_key(self, api_key: str, save: bool = True) -> bool:
        """Set the API key."""
        if not api_key or not api_key.strip():
            return False
        
        self.api_key = api_key.strip()
        
        if save:
            try:
                keyring.set_password(self.SERVICE_NAME, self.API_KEY_NAME, self.api_key)
            except Exception:
                config_file = Path.home() / ".deeptempo" / "config.json"
                config_file.parent.mkdir(parents=True, exist_ok=True)
                
                config = {}
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                
                config['anthropic_api_key'] = self.api_key
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
        
        return True
    
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return self.api_key is not None
    
    async def chat_stream(self, message: str, system_prompt: Optional[str] = None,
                         context: Optional[List[Dict]] = None, model: str = "claude-sonnet-4-5-20250929",
                         images: Optional[List[Dict]] = None, max_tokens: int = 4096,
                         enable_thinking: Optional[bool] = None,
                         thinking_budget: Optional[int] = None) -> AsyncIterator[str]:
        """
        Send a chat message to Claude with streaming response using Agent SDK.
        
        Args:
            message: User message
            system_prompt: Optional system prompt
            context: Optional context messages (for conversation history)
            model: Claude model to use
            images: Optional list of image content blocks
            max_tokens: Maximum tokens for response
            enable_thinking: Override thinking setting
            thinking_budget: Override thinking budget
        
        Yields:
            Text chunks as they arrive
        """
        if not self.has_api_key():
            raise ValueError("API key not configured. Please set your Anthropic API key.")
        
        # Set environment variable for Agent SDK
        import os
        os.environ['ANTHROPIC_API_KEY'] = self.api_key
        
        # Build prompt with context
        full_prompt = message
        if context:
            # Format context as conversation
            context_text = "\n\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in context if isinstance(msg.get('content'), str)
            ])
            full_prompt = f"{context_text}\n\nUser: {message}"
        
        # Prepare options
        options = ClaudeAgentOptions(
            model=model,
            max_tokens=max_tokens
        )
        
        # Add system prompt if provided
        if system_prompt:
            options.system = system_prompt
        elif self.default_system_prompt:
            options.system = self.default_system_prompt
        
        # Add tools if available
        if self.use_mcp_tools and self.mcp_tools:
            try:
                agent_tools = self._convert_mcp_tools_to_agent_sdk()
                options.tools = agent_tools
            except Exception as e:
                logger.warning(f"Could not convert MCP tools: {e}")
        
        # Stream response using Agent SDK
        try:
            async for message_chunk in query(prompt=full_prompt, options=options):
                if message_chunk.type == "assistant":
                    # Extract text content from assistant message
                    content = message_chunk.data.message.get('content', [])
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get('type') == 'text':
                                yield block.get('text', '')
                            elif hasattr(block, 'text'):
                                yield block.text
                    elif isinstance(content, str):
                        yield content
                elif message_chunk.type == "tool_use":
                    # Tool is being used
                    tool_name = message_chunk.data.get('name', 'unknown')
                    yield f"\n\n[Using tool: {tool_name}...]\n"
                elif message_chunk.type == "result":
                    # Final result metadata (optional logging)
                    logger.info(f"Query completed - Cost: ${message_chunk.data.total_cost_usd}, Turns: {message_chunk.data.num_turns}")
        
        except Exception as e:
            logger.error(f"Error in Claude Agent SDK stream: {e}")
            raise
    
    def chat(self, message: str, system_prompt: Optional[str] = None,
             context: Optional[List[Dict]] = None, model: str = "claude-sonnet-4-5-20250929",
             images: Optional[List[Dict]] = None, max_tokens: int = 4096,
             enable_thinking: Optional[bool] = None,
             thinking_budget: Optional[int] = None) -> Optional[str]:
        """
        Send a chat message to Claude (non-streaming).
        
        Args:
            message: User message
            system_prompt: Optional system prompt
            context: Optional context messages
            model: Claude model to use
            images: Optional list of image content blocks
            max_tokens: Maximum tokens for response
            enable_thinking: Override thinking setting
            thinking_budget: Override thinking budget
        
        Returns:
            Claude's response text or None if error
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            full_response = ""
            async def collect_response():
                nonlocal full_response
                async for chunk in self.chat_stream(
                    message, system_prompt, context, model, images,
                    max_tokens, enable_thinking, thinking_budget
                ):
                    full_response += chunk
            
            loop.run_until_complete(collect_response())
            return full_response
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise
        finally:
            loop.close()
    
    def analyze_finding(self, finding: Dict) -> str:
        """Analyze a security finding using Claude."""
        system_prompt = (
            "You are a security analyst helping to analyze security findings. "
            "Provide clear, actionable analysis including threat assessment and recommended actions."
        )
        
        finding_text = json.dumps(finding, indent=2)
        finding_text = finding_text.replace('"embedding": [', '"embedding": [vector data...')
        
        message = f"Analyze this security finding:\n\n{finding_text}\n\nProvide a detailed analysis."
        
        return self.chat(message, system_prompt=system_prompt)
    
    def correlate_findings(self, findings: List[Dict]) -> str:
        """Correlate multiple findings using Claude."""
        system_prompt = (
            "You are a security analyst correlating multiple security findings. "
            "Identify patterns, relationships, and potential attack campaigns."
        )
        
        findings_text = json.dumps(findings, indent=2)
        findings_text = findings_text.replace('"embedding": [', '"embedding": [vector data...')
        
        message = f"Correlate these security findings:\n\n{findings_text}\n\nProvide correlation analysis."
        
        return self.chat(message, system_prompt=system_prompt)
    
    def generate_case_summary(self, case: Dict, findings: List[Dict]) -> str:
        """Generate a case summary using Claude."""
        system_prompt = (
            "You are a security analyst creating case summaries. "
            "Provide clear summaries including key findings, threat assessment, and next steps."
        )
        
        case_text = json.dumps(case, indent=2)
        findings_text = json.dumps(findings, indent=2)
        findings_text = findings_text.replace('"embedding": [', '"embedding": [vector data...')
        
        message = (
            f"Generate a summary for this investigation case:\n\n"
            f"Case:\n{case_text}\n\n"
            f"Related Findings:\n{findings_text}\n\n"
            f"Provide a comprehensive case summary."
        )
        
        return self.chat(message, system_prompt=system_prompt)
    
    # For compatibility with existing code - these methods can stay the same
    def create_image_block(self, image_source, source_type: str = "auto", media_type: str = "image/jpeg") -> Dict:
        """Create image block (Agent SDK may handle this differently)."""
        # Agent SDK might have its own image handling
        # For now, return standard format
        import base64
        from pathlib import Path
        
        if source_type == "base64" or (source_type == "auto" and not str(image_source).startswith("http")):
            image_path = Path(image_source)
            if image_path.exists():
                with open(image_path, "rb") as f:
                    data = base64.b64encode(f.read()).decode('utf-8')
                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": data
                    }
                }
        
        return {
            "type": "image",
            "source": {
                "type": "url",
                "url": str(image_source)
            }
        }

