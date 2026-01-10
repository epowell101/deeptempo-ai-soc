"""Claude API service for Anthropic integration."""

import logging
import json
from typing import Optional, List, Dict, AsyncIterator
from pathlib import Path
import keyring
import platform

try:
    from anthropic import Anthropic, AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for interacting with Claude API."""
    
    SERVICE_NAME = "deeptempo-ai-soc"
    API_KEY_NAME = "anthropic_api_key"
    
    def __init__(self):
        """Initialize Claude service."""
        self.client: Optional[Anthropic] = None
        self.async_client: Optional[AsyncAnthropic] = None
        self.api_key: Optional[str] = None
        
        # Try to load API key
        self._load_api_key()
    
    def _load_api_key(self) -> bool:
        """Load API key from secure storage."""
        try:
            # Try keyring first (more secure)
            try:
                self.api_key = keyring.get_password(self.SERVICE_NAME, self.API_KEY_NAME)
            except Exception:
                # Fallback to config file
                config_file = Path.home() / ".deeptempo" / "config.json"
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        self.api_key = config.get('anthropic_api_key')
            
            # Also check environment variable
            if not self.api_key:
                import os
                self.api_key = os.environ.get('ANTHROPIC_API_KEY')
            
            if self.api_key and ANTHROPIC_AVAILABLE:
                self.client = Anthropic(api_key=self.api_key)
                self.async_client = AsyncAnthropic(api_key=self.api_key)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error loading API key: {e}")
            return False
    
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
                # Try to save to keyring
                try:
                    keyring.set_password(self.SERVICE_NAME, self.API_KEY_NAME, self.api_key)
                except Exception:
                    # Fallback to config file
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
        
        except Exception as e:
            logger.error(f"Error setting API key: {e}")
            return False
    
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return self.api_key is not None and self.client is not None
    
    def chat(self, message: str, system_prompt: Optional[str] = None,
             context: Optional[List[Dict]] = None, model: str = "claude-3-5-sonnet-20241022") -> Optional[str]:
        """
        Send a chat message to Claude.
        
        Args:
            message: User message.
            system_prompt: Optional system prompt.
            context: Optional context messages (for conversation history).
            model: Claude model to use.
        
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
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Make API call
            response = self.client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages
            )
            
            # Extract text from response
            if response.content:
                return response.content[0].text
            
            return None
        
        except Exception as e:
            logger.error(f"Error in Claude chat: {e}")
            raise
    
    async def chat_stream(self, message: str, system_prompt: Optional[str] = None,
                         context: Optional[List[Dict]] = None,
                         model: str = "claude-3-5-sonnet-20241022") -> AsyncIterator[str]:
        """
        Send a chat message to Claude with streaming response.
        
        Args:
            message: User message.
            system_prompt: Optional system prompt.
            context: Optional context messages.
            model: Claude model to use.
        
        Yields:
            Text chunks as they arrive.
        """
        if not self.has_api_key():
            raise ValueError("API key not configured. Please set your Anthropic API key.")
        
        try:
            messages = []
            
            if context:
                messages.extend(context)
            
            messages.append({"role": "user", "content": message})
            
            async with self.async_client.messages.stream(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        
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
        
        return self.chat(message, system_prompt=system_prompt)
    
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
        
        return self.chat(message, system_prompt=system_prompt)
    
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
        
        return self.chat(message, system_prompt=system_prompt)

