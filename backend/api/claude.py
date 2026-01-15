"""Claude API endpoints for chat and streaming."""

from typing import List, Optional, Dict, Union, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import logging
import base64

from services.claude_factory import create_claude_service

router = APIRouter()
logger = logging.getLogger(__name__)


class ContentBlock(BaseModel):
    """Content block for message (text or image)."""
    type: str  # "text" or "image"
    text: Optional[str] = None
    source: Optional[Dict[str, Any]] = None  # For image: {"type": "base64", "media_type": "...", "data": "..."}


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # user or assistant
    content: Union[str, List[ContentBlock]]  # Can be string or list of content blocks


class ChatRequest(BaseModel):
    """Chat request model."""
    messages: List[ChatMessage]
    system_prompt: Optional[str] = None
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    enable_thinking: bool = False
    thinking_budget: int = 10000
    agent_id: Optional[str] = None
    streaming: bool = False


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Send a chat message to Claude and get a response.
    
    Args:
        request: Chat request with messages and parameters
    
    Returns:
        Claude's response
    """
    from services.soc_agents import AgentManager
    
    # If agent_id is provided, get the agent's system prompt and settings
    system_prompt = request.system_prompt
    enable_thinking = request.enable_thinking
    max_tokens = request.max_tokens
    
    if request.agent_id:
        agent_manager = AgentManager()
        agent = agent_manager.agents.get(request.agent_id)
        if agent:
            system_prompt = agent.system_prompt
            enable_thinking = agent.enable_thinking
            max_tokens = agent.max_tokens
            logger.info(f"Using agent: {agent.name}")
    
    claude_service = create_claude_service(
        use_mcp_tools=True,
        enable_thinking=enable_thinking,
        thinking_budget=request.thinking_budget
    )
    
    # Check if API key is configured (works for both implementations)
    if not claude_service.has_api_key():
        raise HTTPException(status_code=503, detail="Claude API not configured")
    
    try:
        # Convert messages to format expected by Claude
        messages = []
        for msg in request.messages:
            if isinstance(msg.content, str):
                messages.append({"role": msg.role, "content": msg.content})
            else:
                # Handle content blocks (text + images, skip thinking blocks)
                content_blocks = []
                for block in msg.content:
                    if block.type == "text":
                        content_blocks.append({"type": "text", "text": block.text})
                    elif block.type == "image" and block.source:
                        content_blocks.append({"type": "image", "source": block.source})
                    # Skip thinking blocks - they should not be included in requests
                    elif block.type == "thinking":
                        continue
                
                # Only add message if it has content after filtering
                if content_blocks:
                    messages.append({"role": msg.role, "content": content_blocks})
        
        # Split messages into context and current message
        # The last message should be the current user message
        if len(messages) == 0:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Get the last message as the current message
        current_message = messages[-1]["content"]
        
        # Use all previous messages as context (if any)
        context = messages[:-1] if len(messages) > 1 else None
        
        # Run sync chat() in executor to avoid event loop conflict
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: claude_service.chat(
                message=current_message,
                context=context,
                system_prompt=system_prompt,
                model=request.model,
                max_tokens=max_tokens
            )
        )
        
        return {
            "response": response,
            "model": request.model,
            "agent_id": request.agent_id
        }
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Send a chat message to Claude and stream the response.
    
    Args:
        request: Chat request with messages and parameters
    
    Returns:
        Streaming response
    """
    claude_service = create_claude_service(
        use_mcp_tools=True,
        enable_thinking=request.enable_thinking,
        thinking_budget=request.thinking_budget
    )
    
    # Check if API key is configured (works for both implementations)
    if not claude_service.has_api_key():
        raise HTTPException(status_code=503, detail="Claude API not configured")
    
    async def generate():
        try:
            # Convert messages to format expected by Claude
            messages = []
            for msg in request.messages:
                if isinstance(msg.content, str):
                    messages.append({"role": msg.role, "content": msg.content})
                else:
                    # Handle content blocks (text + images, skip thinking blocks)
                    content_blocks = []
                    for block in msg.content:
                        if block.type == "text":
                            content_blocks.append({"type": "text", "text": block.text})
                        elif block.type == "image" and block.source:
                            content_blocks.append({"type": "image", "source": block.source})
                        # Skip thinking blocks - they should not be included in requests
                        elif block.type == "thinking":
                            continue
                    
                    # Only add message if it has content after filtering
                    if content_blocks:
                        messages.append({"role": msg.role, "content": content_blocks})
            
            # Split messages into context and current message
            if len(messages) == 0:
                yield f"data: {json.dumps({'error': 'No messages provided'})}\n\n"
                return
            
            # Get the last message as the current message
            current_message = messages[-1]["content"]
            
            # Use all previous messages as context (if any)
            context = messages[:-1] if len(messages) > 1 else None
            
            async for chunk in claude_service.chat_stream(
                message=current_message,
                context=context,
                system_prompt=request.system_prompt,
                model=request.model,
                max_tokens=request.max_tokens
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for bidirectional chat with Claude.
    
    This allows for streaming responses and real-time interaction.
    """
    await websocket.accept()
    
    claude_service = create_claude_service(use_mcp_tools=True)
    
    # Check if API key is configured (works for both implementations)
    if not claude_service.has_api_key():
        await websocket.send_json({"error": "Claude API not configured"})
        await websocket.close()
        return
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            messages = data.get("messages", [])
            system_prompt = data.get("system_prompt")
            model = data.get("model", "claude-sonnet-4-20250514")
            max_tokens = data.get("max_tokens", 4096)
            enable_thinking = data.get("enable_thinking", False)
            thinking_budget = data.get("thinking_budget", 10000)
            
            # Update thinking settings if needed
            if enable_thinking != claude_service.enable_thinking:
                claude_service.enable_thinking = enable_thinking
                claude_service.thinking_budget = thinking_budget
            
            # Stream response back to client
            try:
                # Split messages into context and current message
                if len(messages) == 0:
                    await websocket.send_json({"error": "No messages provided"})
                    continue
                
                # Get the last message as the current message
                current_message = messages[-1]["content"]
                
                # Use all previous messages as context (if any)
                context = messages[:-1] if len(messages) > 1 else None
                
                async for chunk in claude_service.chat_stream(
                    message=current_message,
                    context=context,
                    system_prompt=system_prompt,
                    model=model,
                    max_tokens=max_tokens
                ):
                    await websocket.send_json(chunk)
            
            except Exception as e:
                logger.error(f"Error in chat stream: {e}")
                await websocket.send_json({"error": str(e)})
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


@router.get("/models")
async def get_models():
    """
    Get list of available Claude models.
    
    Returns:
        List of model names
    """
    return {
        "models": [
            {
                "id": "claude-sonnet-4-20250514",
                "name": "Claude 4.5 Sonnet",
                "description": "Most intelligent model, best for complex tasks"
            },
            {
                "id": "claude-3-5-sonnet-20241022",
                "name": "Claude 3.5 Sonnet",
                "description": "Previous generation, good balance of speed and intelligence"
            },
            {
                "id": "claude-3-5-haiku-20241022",
                "name": "Claude 3.5 Haiku",
                "description": "Fastest model, good for simple tasks"
            }
        ]
    }


@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file (image or document) for use in chat.
    
    Args:
        file: The file to upload
    
    Returns:
        Base64 encoded file content and metadata
    """
    try:
        # Read file content
        content = await file.read()
        
        # Determine media type
        media_type = file.content_type or "application/octet-stream"
        
        # For images, encode as base64
        if media_type.startswith("image/"):
            base64_data = base64.b64encode(content).decode("utf-8")
            return {
                "type": "image",
                "media_type": media_type,
                "data": base64_data,
                "filename": file.filename,
                "size": len(content)
            }
        else:
            # For other files, return as text or base64
            try:
                text_content = content.decode("utf-8")
                return {
                    "type": "text",
                    "content": text_content,
                    "filename": file.filename,
                    "size": len(content)
                }
            except UnicodeDecodeError:
                base64_data = base64.b64encode(content).decode("utf-8")
                return {
                    "type": "file",
                    "media_type": media_type,
                    "data": base64_data,
                    "filename": file.filename,
                    "size": len(content)
                }
    
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-finding")
async def analyze_finding(finding_id: str, context: Optional[str] = None):
    """
    Analyze a specific finding with Claude.
    
    Args:
        finding_id: The finding ID to analyze
        context: Optional additional context
    
    Returns:
        Analysis result
    """
    from services.data_service import DataService
    
    data_service = DataService()
    finding = data_service.get_finding(finding_id)
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    claude_service = create_claude_service(use_mcp_tools=True)
    
    # Check if API key is configured (works for both implementations)
    if not claude_service.has_api_key():
        raise HTTPException(status_code=503, detail="Claude API not configured")
    
    # Construct analysis prompt
    prompt = f"""Please analyze this security finding:

Finding ID: {finding.get('finding_id')}
Severity: {finding.get('severity')}
Data Source: {finding.get('data_source')}
Timestamp: {finding.get('timestamp')}
Description: {finding.get('description', 'N/A')}

Predicted Techniques: {', '.join([t.get('technique_id', '') for t in finding.get('predicted_techniques', [])])}

{f'Additional Context: {context}' if context else ''}

Please provide:
1. A summary of the threat
2. Potential impact
3. Recommended actions
4. Related MITRE ATT&CK techniques"""
    
    try:
        # Run sync chat() in executor to avoid event loop conflict
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: claude_service.chat(
                message=prompt,
                model="claude-sonnet-4-20250514",
                max_tokens=4096
            )
        )
        
        return {
            "finding_id": finding_id,
            "analysis": response
        }
    
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ChatReportRequest(BaseModel):
    """Request model for generating a chat report."""
    tab_title: str
    messages: List[ChatMessage]
    notes: Optional[str] = None


@router.post("/generate-chat-report")
async def generate_chat_report(request: ChatReportRequest):
    """
    Generate a PDF report from a chat conversation.
    
    Args:
        request: Chat report request with messages and metadata
    
    Returns:
        Report file information
    """
    from services.report_service import ReportService, REPORTLAB_AVAILABLE
    from pathlib import Path
    from datetime import datetime
    
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Report generation requires reportlab. Install with: pip install reportlab"
        )
    
    try:
        report_service = ReportService()
        
        # Create output directory
        output_dir = Path("TestOutputs")
        output_dir.mkdir(exist_ok=True)
        
        # Generate report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in request.tab_title)
        safe_title = safe_title[:50]  # Limit length
        filename = f"chat_report_{safe_title}_{timestamp}.pdf"
        output_path = output_dir / filename
        
        # Convert messages to simple dict format for report
        conversation_history = []
        for msg in request.messages:
            # Extract text content from message
            if isinstance(msg.content, str):
                content_text = msg.content
            else:
                # For content blocks, concatenate text blocks
                text_parts = []
                for block in msg.content:
                    if block.type == "text" and block.text:
                        text_parts.append(block.text)
                    elif block.type == "image":
                        text_parts.append("[Image attached]")
                content_text = "\n".join(text_parts)
            
            conversation_history.append({
                "role": msg.role,
                "content": content_text
            })
        
        # Generate the report
        success = report_service.generate_investigation_chat_report(
            output_path=output_path,
            tab_title=request.tab_title,
            conversation_history=conversation_history,
            focused_findings=None,  # Could be extended to include findings
            notes=request.notes
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to generate report")
        
        return {
            "success": True,
            "filename": filename,
            "path": str(output_path),
            "message": f"Report generated successfully: {filename}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating chat report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

