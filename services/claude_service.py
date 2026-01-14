"""Claude API service for Anthropic integration."""

import logging
import json
import base64
from typing import Optional, List, Dict, AsyncIterator, Union
from pathlib import Path
import platform
import asyncio
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from secrets_manager import get_secret, set_secret

try:
    from anthropic import Anthropic, AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for interacting with Claude API."""
    
    SERVICE_NAME = "deeptempo-ai-soc"
    API_KEY_NAME = "claude_api_key"  # Changed to match settings console
    
    def __init__(self, use_mcp_tools: bool = True, enable_thinking: bool = False, thinking_budget: int = 10000):
        """
        Initialize Claude service.
        
        Args:
            use_mcp_tools: Whether to enable MCP tool integration
            enable_thinking: Whether to enable extended thinking (default: False)
            thinking_budget: Token budget for extended thinking (default: 10000)
        """
        self.client: Optional[Anthropic] = None
        self.async_client: Optional[AsyncAnthropic] = None
        self.api_key: Optional[str] = None
        self.use_mcp_tools = use_mcp_tools
        self.mcp_tools: List[Dict] = []
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget
        
        # Default system prompt with Claude 4.5 best practices
        self.default_system_prompt = self._get_default_system_prompt()
        
        # Try to load API key
        self._load_api_key()
        
        # Load MCP tools if enabled
        if self.use_mcp_tools:
            self._load_mcp_tools()
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt with Claude 4.5 best practices."""
        return """You are Claude, an AI assistant for security operations and analysis in the DeepTempo AI SOC platform.

<default_to_action>
By default, implement changes rather than only suggesting them. If the user's intent is unclear, infer the most useful likely action and proceed, using tools to discover any missing details instead of guessing. Try to infer the user's intent about whether a tool call (e.g., file edit or read) is intended or not, and act accordingly.
</default_to_action>

<use_parallel_tool_calls>
If you intend to call multiple tools and there are no dependencies between the tool calls, make all of the independent tool calls in parallel. Prioritize calling tools simultaneously whenever the actions can be done in parallel rather than sequentially. For example, when reading 3 files, run 3 tool calls in parallel to read all 3 files into context at the same time. Maximize use of parallel tool calls where possible to increase speed and efficiency. However, if some tool calls depend on previous calls to inform dependent values like the parameters, do NOT call these tools in parallel and instead call them sequentially. Never use placeholders or guess missing parameters in tool calls.
</use_parallel_tool_calls>

<investigate_before_answering>
Never speculate about data you have not retrieved. If the user references a specific finding, case, or other security entity, you MUST use the appropriate MCP tool to fetch it before answering. Make sure to investigate and retrieve relevant data BEFORE answering questions. Never make any claims about security data before investigating - give grounded and hallucination-free answers.
</investigate_before_answering>

<available_mcp_tools>
You have access to MCP (Model Context Protocol) tools that connect to various security platforms and data sources. The tools are prefixed with the server name (e.g., "deeptempo-findings_get_finding"). Use these tools to:

1. **Findings & Cases**: Retrieve and analyze security findings from DeepTempo LogLM
   - Finding IDs start with "f-" (e.g., "f-20260109-40d9379b")
   - Case IDs start with "case-" (e.g., "case-12345")
   - Use tools like: list_findings, get_finding, list_cases, get_case

2. **Security Integrations**: Query data from various security platforms
   - The available integrations are dynamically loaded based on what's configured
   - Tools are named with the pattern: {integration-name}_{tool-name}
   - Check your available tools to see which integrations are active

3. **Threat Intelligence**: Analyze indicators, URLs, files, etc.
   - Use tools for VirusTotal, Shodan, AnyRun, Hybrid Analysis, etc. (if available)
   - These help enrich findings with external context

4. **Investigation Workflows**: Execute predefined investigation workflows
   - Automate common SOC investigation patterns
   - Use tempo_flow_server tools for workflows

When a user mentions an ID or entity (finding, case, IP, hash, domain), ALWAYS use the appropriate MCP tool to retrieve it first. Never try to access these as files - they are stored in databases and accessed via MCP tools.
</available_mcp_tools>

<recognizing_security_entities>
Common patterns you should recognize and how to handle them:

- Finding IDs: "f-YYYYMMDD-XXXXXXXX" → Use deeptempo-findings_get_finding tool
- Case IDs: "case-" prefix → Use case-store_get_case tool  
- IP addresses: X.X.X.X → Consider using IP geolocation or threat intel tools
- Domain names: example.com → Consider using URL analysis or threat intel tools
- File hashes: MD5/SHA1/SHA256 → Consider using malware analysis tools
- URLs: http(s)://... → Consider using URL analysis tools

IMPORTANT: When a user says "analyze [ID]", "check [ID]", "investigate [ID]", etc., your FIRST action should ALWAYS be to use the appropriate MCP tool to fetch that entity's data.
</recognizing_security_entities>

<security_analysis_workflow>
When analyzing security findings and cases:
1. **Retrieve**: Use MCP tools to fetch the finding/case data first
2. **Understand**: Parse the severity, data source, MITRE techniques, and context
3. **Correlate**: Look for related findings or patterns using similarity/correlation tools
4. **Enrich**: Use threat intelligence tools to add external context
5. **Analyze**: Provide clear assessment of the threat, impact, and recommended actions
6. **Act**: Be thorough but efficient - prioritize actionable insights
</security_analysis_workflow>

Your goal is to help SOC analysts work more efficiently by leveraging all available tools and integrations to provide comprehensive, accurate, and actionable security analysis."""
    
    def _load_api_key(self) -> bool:
        """Load API key from secure storage."""
        try:
            # Use secrets manager with fallback to legacy names
            self.api_key = (get_secret("CLAUDE_API_KEY") or 
                           get_secret("ANTHROPIC_API_KEY") or
                           get_secret("claude_api_key") or
                           get_secret("anthropic_api_key"))
            
            if self.api_key and ANTHROPIC_AVAILABLE:
                self.client = Anthropic(api_key=self.api_key)
                self.async_client = AsyncAnthropic(api_key=self.api_key)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error loading API key: {e}")
            return False
    
    def _load_mcp_tools(self):
        """Load MCP tools for Claude to use."""
        # Clear existing tools to prevent duplicates
        self.mcp_tools = []
        
        try:
            from services.mcp_client import get_mcp_client
            import asyncio
            
            mcp_client = get_mcp_client()
            if mcp_client:
                # Try to use existing event loop or create a new one
                try:
                    # Check if there's already a running loop
                    loop = asyncio.get_running_loop()
                    # If we're in an async context, we can't use run_until_complete
                    # Instead, just use cached tools or skip loading
                    logger.info("Running in async context - using cached MCP tools")
                    tools_dict = mcp_client.tools_cache
                    if not tools_dict:
                        logger.warning("No cached MCP tools available yet. Tools will be loaded on first use.")
                        return
                except RuntimeError:
                    # No running loop, safe to create one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # First, try to get cached tools
                        tools_dict = loop.run_until_complete(mcp_client.list_tools())
                        
                        # If no tools are cached, try to connect to servers
                        if not tools_dict or all(len(tools) == 0 for tools in tools_dict.values()):
                            logger.info("No cached MCP tools found, attempting to connect to servers...")
                            servers = mcp_client.mcp_service.list_servers()
                            for server_name in servers:
                                try:
                                    loop.run_until_complete(mcp_client.connect_to_server(server_name))
                                except Exception as e:
                                    logger.warning(f"Could not connect to {server_name}: {e}")
                            
                            # Try to get tools again after connecting
                            tools_dict = loop.run_until_complete(mcp_client.list_tools())
                    finally:
                        loop.close()
                
                # Track tool names to prevent duplicates
                seen_tool_names = set()
                
                # Flatten tools from all servers with server prefix
                for server_name, server_tools in tools_dict.items():
                    for tool in server_tools:
                        # Format for Claude API with server prefix
                        tool_name = f"{server_name}_{tool['name']}"
                        
                        # Skip if we've already seen this tool name
                        if tool_name in seen_tool_names:
                            logger.warning(f"Skipping duplicate tool: {tool_name}")
                            continue
                        seen_tool_names.add(tool_name)
                        
                        # Get input schema - handle both dict and object formats
                        input_schema = tool.get("inputSchema", {})
                        if hasattr(input_schema, 'model_dump'):
                            input_schema = input_schema.model_dump()
                        elif not isinstance(input_schema, dict):
                            input_schema = dict(input_schema) if input_schema else {}
                        
                        # Ensure input_schema has required structure
                        if not input_schema or "type" not in input_schema:
                            input_schema = {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        
                        claude_tool = {
                            "name": tool_name,
                            "description": f"[{server_name}] {tool.get('description', '')}",
                            "input_schema": input_schema
                        }
                        self.mcp_tools.append(claude_tool)
                
                if self.mcp_tools:
                    tool_names = [t['name'] for t in self.mcp_tools]
                    logger.info(f"✓ Loaded {len(self.mcp_tools)} MCP tools from {len(tools_dict)} servers")
                    logger.debug(f"Available tools: {', '.join(tool_names)}")
                else:
                    logger.warning("No MCP tools were loaded. Check that MCP servers are configured and running.")
            else:
                logger.warning("MCP client not available")
        except Exception as e:
            logger.warning(f"Could not load MCP tools: {e}")
            self.mcp_tools = []
    
    def set_api_key(self, api_key: str, save: bool = True) -> bool:
        """
        Set the API key.
        
        Args:
            api_key: The Anthropic API key.
            save: Whether to save the key securely.
        
        Returns:
            True if successful, False otherwise.
        """
        if not api_key or not api_key.strip():
            return False
        
        self.api_key = api_key.strip()
        
        if not ANTHROPIC_AVAILABLE:
            logger.warning("Anthropic package not available. Install with: pip install anthropic")
            return False
        
        try:
            self.client = Anthropic(api_key=self.api_key)
            self.async_client = AsyncAnthropic(api_key=self.api_key)
            
            if save:
                # Save using secrets manager
                set_secret("CLAUDE_API_KEY", self.api_key)
            
            return True
        
        except Exception as e:
            logger.error(f"Error setting API key: {e}")
            return False
    
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return self.api_key is not None and self.client is not None
    
    async def _process_tool_use(self, content: List) -> List[Dict]:
        """Process tool use requests and call MCP tools."""
        tool_results = []
        
        for item in content:
            # Handle both dict and object formats
            if isinstance(item, dict):
                item_type = item.get('type')
                tool_name = item.get('name')
                tool_id = item.get('id')
                arguments = item.get('input', {})
            else:
                item_type = getattr(item, 'type', None)
                tool_name = getattr(item, 'name', None)
                tool_id = getattr(item, 'id', None)
                arguments = getattr(item, 'input', {})
            
            if item_type == 'tool_use' and tool_name:
                # Extract server name from tool name (format: server_toolname)
                parts = tool_name.split('_', 1)
                if len(parts) == 2:
                    server_name, actual_tool_name = parts
                else:
                    # Try to find tool in any server by checking tool cache
                    server_name = None
                    actual_tool_name = tool_name
                    from services.mcp_client import get_mcp_client
                    mcp_client = get_mcp_client()
                    if mcp_client:
                        # Check which server has this tool
                        for srv_name, tools in mcp_client.tools_cache.items():
                            if any(t['name'] == tool_name for t in tools):
                                server_name = srv_name
                                break
                
                if server_name:
                    try:
                        from services.mcp_client import get_mcp_client
                        
                        mcp_client = get_mcp_client()
                        if mcp_client:
                            # Call tool with 30 second timeout
                            result = await mcp_client.call_tool(server_name, actual_tool_name, arguments, timeout=30.0)
                            
                            # Format result for Claude API
                            if isinstance(result, dict):
                                content = result.get("content", [{"type": "text", "text": str(result)}])
                            else:
                                content = [{"type": "text", "text": str(result)}]
                            
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": content
                            })
                    except Exception as e:
                        logger.error(f"Error calling tool {tool_name}: {e}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": [{"type": "text", "text": f"Error: {str(e)}"}]
                        })
                else:
                    logger.warning(f"Could not determine server for tool {tool_name}")
        
        return tool_results
    
    def chat(self, message: Union[str, List[Dict]], system_prompt: Optional[str] = None,
             context: Optional[List[Dict]] = None, model: str = "claude-sonnet-4-5-20250929",
             images: Optional[List[Dict]] = None, prefill: Optional[str] = None,
             max_tokens: int = 4096, enable_thinking: Optional[bool] = None,
             thinking_budget: Optional[int] = None) -> Optional[str]:
        """
        Send a chat message to Claude.
        
        Args:
            message: User message (string or list of content blocks for multimodal).
            system_prompt: Optional system prompt (uses default if None).
            context: Optional context messages (for conversation history).
            model: Claude model to use.
            images: Optional list of image content blocks (for vision).
            prefill: Optional prefill text to shape Claude's response.
            max_tokens: Maximum tokens for response (default: 4096).
            enable_thinking: Override thinking setting for this request.
            thinking_budget: Override thinking budget for this request.
        
        Returns:
            Claude's response text or None if error.
        """
        if not self.has_api_key():
            raise ValueError("API key not configured. Please set your Anthropic API key.")
        
        try:
            messages = []
            
            # Add context if provided
            if context:
                messages.extend(context)
            
            # Build user message content (support text, images, or mixed)
            user_content = self._build_user_content(message, images)
            messages.append({"role": "user", "content": user_content})
            
            # Add prefill if provided (assistant message to shape response)
            if prefill:
                messages.append({"role": "assistant", "content": prefill})
            
            # Prepare tools if MCP tools are available
            tools = None
            if self.use_mcp_tools and self.mcp_tools:
                tools = self.mcp_tools
            
            # Use system prompt (default if not provided)
            effective_system_prompt = system_prompt if system_prompt is not None else self.default_system_prompt
            
            # Determine thinking settings
            use_thinking = enable_thinking if enable_thinking is not None else self.enable_thinking
            thinking_config = None
            if use_thinking:
                budget = thinking_budget if thinking_budget is not None else self.thinking_budget
                thinking_config = {"type": "enabled", "budget_tokens": budget}
            
            # Make API call
            # Note: Claude 4.5 requires using only temperature OR top_p, not both
            api_kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            if effective_system_prompt:
                api_kwargs["system"] = effective_system_prompt
            if tools:
                api_kwargs["tools"] = tools
            if thinking_config:
                api_kwargs["thinking"] = thinking_config
            
            response = self.client.messages.create(**api_kwargs)
            
            # Handle stop reasons (including new refusal reason in Claude 4.5)
            if response.stop_reason == "refusal":
                logger.warning("Claude refused to respond to the request")
                return "I apologize, but I cannot assist with that request."
            
            if response.stop_reason == "tool_use" and response.content:
                # Process tool use synchronously with timeout
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Add overall timeout for tool processing (60 seconds total)
                    try:
                        tool_results = loop.run_until_complete(
                            asyncio.wait_for(self._process_tool_use(response.content), timeout=60.0)
                        )
                    except asyncio.TimeoutError:
                        logger.error("Tool processing timed out after 60 seconds")
                        # Return error message instead of hanging
                        return "I encountered a timeout while processing tool calls. The MCP servers may not be responding. Please check that the MCP servers are running (use the MCP Manager) and try again."
                    
                    # Add tool results to messages and continue conversation
                    # Convert response.content to proper format if needed
                    assistant_content = response.content
                    if not isinstance(assistant_content, list):
                        assistant_content = [assistant_content] if assistant_content else []
                    messages.append({"role": "assistant", "content": assistant_content})
                    # Tool results need to be wrapped in a user message
                    messages.append({"role": "user", "content": tool_results})
                    
                    # Get final response
                    api_kwargs = {
                        "model": model,
                        "max_tokens": 4096,
                        "messages": messages,
                    }
                    if system_prompt:
                        api_kwargs["system"] = system_prompt
                    if tools:
                        api_kwargs["tools"] = tools
                    
                    final_response = self.client.messages.create(**api_kwargs)
                    
                    # Handle refusal in final response
                    if final_response.stop_reason == "refusal":
                        logger.warning("Claude refused to respond to the request")
                        return "I apologize, but I cannot assist with that request."
                    
                    # Extract text from response (skip thinking blocks)
                    if final_response.content:
                        for content_block in final_response.content:
                            # Only return text from text blocks, skip thinking blocks
                            if hasattr(content_block, 'type') and content_block.type == 'text':
                                if hasattr(content_block, 'text'):
                                    return content_block.text
                finally:
                    loop.close()
            
            # Extract text from response (skip thinking blocks)
            if response.content:
                for content_block in response.content:
                    # Only return text from text blocks, skip thinking blocks
                    if hasattr(content_block, 'type') and content_block.type == 'text':
                        if hasattr(content_block, 'text'):
                            return content_block.text
            
            return None
        
        except Exception as e:
            logger.error(f"Error in Claude chat: {e}")
            raise
    
    def _build_user_content(self, message: Union[str, List[Dict]], images: Optional[List[Dict]] = None) -> Union[str, List[Dict]]:
        """
        Build user content for API request, supporting text, images, or mixed content.
        
        Args:
            message: User message (string or list of content blocks).
            images: Optional list of image content blocks.
        
        Returns:
            Content for user message (string or list of content blocks).
        """
        # If message is already a list of content blocks, use it directly
        if isinstance(message, list):
            if images:
                # Merge images into existing content blocks
                return message + images
            return message
        
        # If images are provided, create mixed content
        if images:
            content_blocks = []
            # Add images first
            content_blocks.extend(images)
            # Add text message
            content_blocks.append({"type": "text", "text": message})
            return content_blocks
        
        # Simple text message
        return message
    
    def encode_image_base64(self, image_path: Union[str, Path]) -> str:
        """
        Encode an image file to base64.
        
        Args:
            image_path: Path to image file.
        
        Returns:
            Base64-encoded image string.
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def create_image_block(self, image_source: Union[str, Path, bytes], 
                          source_type: str = "auto", media_type: str = "image/jpeg") -> Dict:
        """
        Create an image content block for Claude API.
        
        Args:
            image_source: Image source (URL string, file path, or base64 bytes).
            source_type: "url", "base64", or "auto" (auto-detect from source).
            media_type: Media type (image/jpeg, image/png, image/gif, image/webp).
        
        Returns:
            Image content block dictionary.
        """
        if source_type == "auto":
            if isinstance(image_source, str):
                if image_source.startswith(("http://", "https://")):
                    source_type = "url"
                else:
                    source_type = "base64"
            elif isinstance(image_source, (Path, bytes)):
                source_type = "base64"
        
        if source_type == "url":
            return {
                "type": "image",
                "source": {
                    "type": "url",
                    "url": str(image_source)
                }
            }
        elif source_type == "base64":
            if isinstance(image_source, (str, Path)):
                data = self.encode_image_base64(image_source)
            elif isinstance(image_source, bytes):
                data = base64.b64encode(image_source).decode('utf-8')
            else:
                raise ValueError(f"Invalid image source type: {type(image_source)}")
            
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": data
                }
            }
        else:
            raise ValueError(f"Invalid source_type: {source_type}. Use 'url' or 'base64'.")
    
    async def chat_stream(self, message: Union[str, List[Dict]], system_prompt: Optional[str] = None,
                         context: Optional[List[Dict]] = None, model: str = "claude-sonnet-4-5-20250929",
                         images: Optional[List[Dict]] = None, prefill: Optional[str] = None,
                         max_tokens: int = 4096, enable_thinking: Optional[bool] = None,
                         thinking_budget: Optional[int] = None) -> AsyncIterator[str]:
        """
        Send a chat message to Claude with streaming response.
        
        Args:
            message: User message (string or list of content blocks for multimodal).
            system_prompt: Optional system prompt (uses default if None).
            context: Optional context messages.
            model: Claude model to use.
            images: Optional list of image content blocks (for vision).
            prefill: Optional prefill text to shape Claude's response.
            max_tokens: Maximum tokens for response (default: 4096).
            enable_thinking: Override thinking setting for this request.
            thinking_budget: Override thinking budget for this request.
        
        Yields:
            Text chunks as they arrive.
        """
        if not self.has_api_key():
            raise ValueError("API key not configured. Please set your Anthropic API key.")
        
        try:
            messages = []
            
            if context:
                messages.extend(context)
            
            # Build user message content (support text, images, or mixed)
            user_content = self._build_user_content(message, images)
            messages.append({"role": "user", "content": user_content})
            
            # Add prefill if provided
            if prefill:
                messages.append({"role": "assistant", "content": prefill})

            # Prepare tools if MCP tools are available
            tools = None
            if self.use_mcp_tools and self.mcp_tools:
                tools = self.mcp_tools

            # Use system prompt (default if not provided)
            effective_system_prompt = system_prompt if system_prompt is not None else self.default_system_prompt
            
            # Determine thinking settings
            use_thinking = enable_thinking if enable_thinking is not None else self.enable_thinking
            thinking_config = None
            if use_thinking:
                budget = thinking_budget if thinking_budget is not None else self.thinking_budget
                thinking_config = {"type": "enabled", "budget_tokens": budget}

            api_kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            if effective_system_prompt:
                api_kwargs["system"] = effective_system_prompt
            if tools:
                api_kwargs["tools"] = tools
            if thinking_config:
                api_kwargs["thinking"] = thinking_config
            
            # Stream with proper tool use handling
            # First, make a non-streaming call to detect tool use
            # Then stream the response
            response = await self.async_client.messages.create(**api_kwargs)
            
            # Check if tool use is needed
            if response.stop_reason == "tool_use" and response.content:
                # Yield initial text if any
                for content_block in response.content:
                    # Only process text blocks, skip thinking blocks and other types
                    if hasattr(content_block, 'type') and content_block.type == "text":
                        if hasattr(content_block, 'text'):
                            yield content_block.text
                
                yield "\n\n[Processing tools...]\n"
                
                # Process tool use
                tool_results = await self._process_tool_use(response.content)
                
                # Add assistant message and tool results
                # Convert response.content to proper format if needed
                assistant_content = response.content
                if not isinstance(assistant_content, list):
                    assistant_content = [assistant_content] if assistant_content else []
                messages.append({"role": "assistant", "content": assistant_content})
                # Tool results need to be wrapped in a user message
                messages.append({"role": "user", "content": tool_results})
                
                # Continue conversation with tool results - now stream it
                continue_kwargs = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": messages,
                }
                if effective_system_prompt:
                    continue_kwargs["system"] = effective_system_prompt
                if tools:
                    continue_kwargs["tools"] = tools
                if thinking_config:
                    continue_kwargs["thinking"] = thinking_config
                
                # Stream the continuation (may need multiple rounds for tool use)
                max_iterations = 5  # Prevent infinite loops
                iteration = 0
                while iteration < max_iterations:
                    iteration += 1
                    continue_response = await self.async_client.messages.create(**continue_kwargs)
                    
                    # Stream text content - skip thinking blocks
                    for content_block in continue_response.content:
                        # Only yield text blocks, explicitly skip thinking blocks
                        if hasattr(content_block, 'type'):
                            if content_block.type == "text" and hasattr(content_block, 'text'):
                                yield content_block.text
                            # Skip thinking blocks silently
                            elif content_block.type == "thinking":
                                continue
                    
                    # Check if more tool use is needed
                    if continue_response.stop_reason == "tool_use" and continue_response.content:
                        yield "\n\n[Processing additional tools...]\n"
                        tool_results = await self._process_tool_use(continue_response.content)
                        # Convert response.content to proper format if needed
                        assistant_content = continue_response.content
                        if not isinstance(assistant_content, list):
                            assistant_content = [assistant_content] if assistant_content else []
                        messages.append({"role": "assistant", "content": assistant_content})
                        # Tool results need to be wrapped in a user message
                        messages.append({"role": "user", "content": tool_results})
                        # Update kwargs for next iteration
                        continue_kwargs["messages"] = messages
                    else:
                        # Done - no more tool use
                        break
            else:
                # No tool use - just stream the text response (skip thinking blocks)
                for content_block in response.content:
                    # Only yield text blocks, explicitly skip thinking blocks
                    if hasattr(content_block, 'type'):
                        if content_block.type == "text" and hasattr(content_block, 'text'):
                            yield content_block.text
                        # Skip thinking blocks silently
                        elif content_block.type == "thinking":
                            continue
        
        except Exception as e:
            logger.error(f"Error in Claude chat stream: {e}")
            raise
    
    def analyze_finding(self, finding: Dict) -> str:
        """
        Analyze a security finding using Claude.
        
        Args:
            finding: Finding dictionary.
        
        Returns:
            Analysis text.
        """
        system_prompt = (
            "You are a security analyst helping to analyze security findings. "
            "Provide clear, actionable analysis of security findings including "
            "threat assessment, recommended actions, and context."
        )
        
        # Format finding for prompt
        finding_text = json.dumps(finding, indent=2)
        # Remove embedding (too large)
        finding_text = finding_text.replace('"embedding": [', '"embedding": [vector data...')
        
        message = f"Analyze this security finding:\n\n{finding_text}\n\nProvide a detailed analysis."
        
        return self.chat(message, system_prompt=system_prompt, model="claude-sonnet-4-5-20250929")
    
    def correlate_findings(self, findings: List[Dict]) -> str:
        """
        Correlate multiple findings using Claude.
        
        Args:
            findings: List of finding dictionaries.
        
        Returns:
            Correlation analysis text.
        """
        system_prompt = (
            "You are a security analyst correlating multiple security findings. "
            "Identify patterns, relationships, and potential attack campaigns. "
            "Provide insights on how findings relate to each other."
        )
        
        findings_text = json.dumps(findings, indent=2)
        # Remove embeddings
        findings_text = findings_text.replace('"embedding": [', '"embedding": [vector data...')
        
        message = f"Correlate these security findings:\n\n{findings_text}\n\nProvide correlation analysis."
        
        return self.chat(message, system_prompt=system_prompt, model="claude-sonnet-4-5-20250929")
    
    def generate_case_summary(self, case: Dict, findings: List[Dict]) -> str:
        """
        Generate a case summary using Claude.
        
        Args:
            case: Case dictionary.
            findings: List of related findings.
        
        Returns:
            Case summary text.
        """
        system_prompt = (
            "You are a security analyst creating case summaries. "
            "Provide clear, concise summaries of investigation cases including "
            "key findings, threat assessment, and recommended next steps."
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
        
        return self.chat(message, system_prompt=system_prompt, model="claude-sonnet-4-5-20250929")

