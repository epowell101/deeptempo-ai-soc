"""Agents API endpoints for SOC agent management."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from services.soc_agents import SOCAgentLibrary, AgentManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Global agent manager instance
agent_manager = AgentManager()


class InvestigationRequest(BaseModel):
    """Request to start an investigation with an agent."""
    finding_id: str
    agent_id: Optional[str] = "investigator"
    additional_context: Optional[str] = None


@router.get("/agents")
async def list_agents():
    """
    Get list of all available SOC agents.
    
    Returns:
        List of agents with their metadata
    """
    try:
        agents = agent_manager.get_agent_list()
        return {
            "agents": agents,
            "current_agent": agent_manager.current_agent_id
        }
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """
    Get details for a specific agent.
    
    Args:
        agent_id: The agent ID
    
    Returns:
        Agent details
    """
    try:
        agent = agent_manager.agents.get(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "icon": agent.icon,
            "color": agent.color,
            "specialization": agent.specialization,
            "recommended_tools": agent.recommended_tools,
            "max_tokens": agent.max_tokens,
            "enable_thinking": agent.enable_thinking
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/set-current")
async def set_current_agent(agent_id: str):
    """
    Set the current active agent.
    
    Args:
        agent_id: The agent ID to set as current
    
    Returns:
        Success status
    """
    try:
        success = agent_manager.set_current_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
        return {
            "success": True,
            "current_agent": agent_manager.current_agent_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting current agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/investigate")
async def start_investigation(request: InvestigationRequest):
    """
    Start an investigation on a finding with a specific agent.
    
    Args:
        request: Investigation request with finding ID and agent
    
    Returns:
        Investigation prompt and agent details
    """
    from services.data_service import DataService
    
    try:
        # Get the finding
        data_service = DataService()
        finding = data_service.get_finding(request.finding_id)
        
        if not finding:
            raise HTTPException(status_code=404, detail=f"Finding not found: {request.finding_id}")
        
        # Get the agent
        agent = agent_manager.agents.get(request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {request.agent_id}")
        
        # Construct investigation prompt
        techniques = finding.get('predicted_techniques', [])
        technique_str = ', '.join([t.get('technique_id', '') for t in techniques]) if techniques else 'None'
        
        prompt = f"""Please investigate this security finding:

**Finding ID:** {finding.get('finding_id')}
**Severity:** {finding.get('severity')}
**Data Source:** {finding.get('data_source')}
**Timestamp:** {finding.get('timestamp')}
**Anomaly Score:** {finding.get('anomaly_score', 'N/A')}
**Description:** {finding.get('description', 'N/A')}
**Predicted MITRE ATT&CK Techniques:** {technique_str}

{f'**Additional Context:** {request.additional_context}' if request.additional_context else ''}

Please conduct a thorough investigation of this finding. Use your available tools to gather more information, correlate with other findings, and provide your analysis."""
        
        return {
            "prompt": prompt,
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "icon": agent.icon,
                "color": agent.color,
                "system_prompt": agent.system_prompt
            },
            "finding": finding
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting investigation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

