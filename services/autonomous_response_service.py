"""Autonomous response service with approval workflow integration."""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class AutonomousResponseService:
    """Service for managing autonomous threat response with approval workflow."""
    
    def __init__(self):
        """Initialize autonomous response service."""
        self.approval_service = None
        self._load_services()
    
    def _load_services(self):
        """Load required services."""
        try:
            from services.approval_service import get_approval_service, ActionType
            self.approval_service = get_approval_service()
            self.ActionType = ActionType
        except Exception as e:
            logger.error(f"Error loading services: {e}")
    
    def correlate_alerts(
        self,
        tempo_flow_alert: Optional[Dict] = None,
        crowdstrike_alert: Optional[Dict] = None,
        splunk_results: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Correlate alerts from multiple sources and calculate confidence score.
        
        Args:
            tempo_flow_alert: Alert from Tempo Flow
            crowdstrike_alert: Alert from CrowdStrike
            splunk_results: Results from Splunk queries
        
        Returns:
            Correlation result with confidence score and reasoning
        """
        confidence = 0.0
        evidence = []
        indicators = []
        reasoning = []
        
        # Correlate Tempo Flow alerts
        if tempo_flow_alert:
            evidence.append(f"Tempo Flow: {tempo_flow_alert.get('finding_id', 'unknown')}")
            
            severity = tempo_flow_alert.get('severity', '').lower()
            if severity in ['high', 'critical']:
                confidence += 0.15
                reasoning.append(f"High severity detection in Tempo Flow ({severity})")
            
            # Check for specific attack patterns
            mitre_predictions = tempo_flow_alert.get('mitre_predictions', {})
            if any(t.startswith('T1486') for t in mitre_predictions):  # Ransomware
                confidence += 0.25
                reasoning.append("Ransomware behavior detected (T1486)")
                indicators.append("ransomware")
            
            if any(t.startswith('T1071') for t in mitre_predictions):  # C2
                confidence += 0.20
                reasoning.append("C2 communication detected (T1071)")
                indicators.append("c2_communication")
            
            if any(t.startswith('T1021') for t in mitre_predictions):  # Lateral movement
                confidence += 0.15
                reasoning.append("Lateral movement detected (T1021)")
                indicators.append("lateral_movement")
        
        # Correlate CrowdStrike alerts
        if crowdstrike_alert:
            cs_alerts = crowdstrike_alert.get('alerts', [])
            if cs_alerts:
                evidence.append(f"CrowdStrike: {len(cs_alerts)} alert(s)")
                
                for alert in cs_alerts:
                    severity = alert.get('severity', '').lower()
                    if severity == 'critical':
                        confidence += 0.15
                        reasoning.append("Critical severity in CrowdStrike")
                    
                    detection_type = alert.get('detection_type', '').lower()
                    if detection_type == 'malware':
                        confidence += 0.20
                        reasoning.append(f"Malware detected: {alert.get('description', '')}")
                        indicators.append("malware")
                    
                    # Check if already isolated
                    if alert.get('isolated', False):
                        reasoning.append("Host already isolated in CrowdStrike")
        
        # Correlate Splunk results
        if splunk_results and len(splunk_results) > 0:
            evidence.append(f"Splunk: {len(splunk_results)} event(s)")
            
            # High volume of events indicates active threat
            if len(splunk_results) > 50:
                confidence += 0.10
                reasoning.append(f"High volume of events ({len(splunk_results)})")
        
        # Time correlation bonus
        if tempo_flow_alert and crowdstrike_alert:
            # If alerts are within 5 minutes, add correlation bonus
            confidence += 0.10
            reasoning.append("Temporal correlation between multiple sources")
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        return {
            "confidence": confidence,
            "indicators": indicators,
            "evidence": evidence,
            "reasoning": reasoning,
            "recommendation": self._get_recommendation(confidence, indicators)
        }
    
    def _get_recommendation(self, confidence: float, indicators: List[str]) -> str:
        """Get recommendation based on confidence and indicators."""
        if confidence >= 0.90:
            return "AUTO-ISOLATE: Confidence threshold met for automatic isolation"
        elif confidence >= 0.85:
            return "ISOLATE WITH APPROVAL: High confidence, recommend isolation with quick approval"
        elif confidence >= 0.70:
            return "MANUAL REVIEW: Moderate confidence, requires analyst review"
        else:
            return "MONITOR: Low confidence, continue monitoring"
    
    def create_isolation_action(
        self,
        ip_address: str,
        hostname: Optional[str],
        confidence: float,
        reason: str,
        evidence: List[str],
        correlation_data: Dict
    ) -> Optional[Dict]:
        """
        Create an isolation action (auto-execute if confidence >= 0.90).
        
        Args:
            ip_address: Target IP address
            hostname: Target hostname (optional)
            confidence: Confidence score (0.0-1.0)
            reason: Reason for isolation
            evidence: List of evidence IDs
            correlation_data: Data from correlation analysis
        
        Returns:
            Action result
        """
        if not self.approval_service:
            logger.error("Approval service not available")
            return {"error": "Approval service not available"}
        
        try:
            # Create pending action
            action = self.approval_service.create_action(
                action_type=self.ActionType.ISOLATE_HOST,
                title=f"Isolate Host: {hostname or ip_address}",
                description=f"Network isolation of compromised host based on correlated detections.\n\n"
                           f"Indicators: {', '.join(correlation_data.get('indicators', []))}\n"
                           f"Reasoning: {' | '.join(correlation_data.get('reasoning', []))}",
                target=ip_address,
                confidence=confidence,
                reason=reason,
                evidence=evidence,
                created_by="auto_responder",
                parameters={
                    "hostname": hostname,
                    "correlation": correlation_data
                }
            )
            
            # Check if auto-approved (confidence >= 0.90)
            if action.status == "approved":
                logger.info(f"Action {action.action_id} auto-approved (confidence: {confidence:.2%})")
                
                # Execute isolation (would call actual CrowdStrike API in production)
                execution_result = self._execute_isolation(ip_address, hostname, reason, confidence)
                
                # Mark as executed
                self.approval_service.mark_executed(action.action_id, execution_result)
                
                return {
                    "status": "executed",
                    "action_id": action.action_id,
                    "message": f"Host {hostname or ip_address} isolated automatically",
                    "confidence": confidence,
                    "result": execution_result
                }
            else:
                logger.info(f"Action {action.action_id} pending approval (confidence: {confidence:.2%})")
                return {
                    "status": "pending_approval",
                    "action_id": action.action_id,
                    "message": f"Isolation action created, awaiting analyst approval",
                    "confidence": confidence,
                    "requires_approval": True
                }
        
        except Exception as e:
            logger.error(f"Error creating isolation action: {e}")
            return {"error": str(e)}
    
    def _execute_isolation(
        self,
        ip_address: str,
        hostname: Optional[str],
        reason: str,
        confidence: float
    ) -> Dict:
        """
        Execute host isolation via CrowdStrike.
        
        In production, this would call the actual CrowdStrike API.
        For now, it returns a mock result.
        """
        logger.info(f"Executing isolation: {hostname or ip_address} (confidence: {confidence:.2%})")
        
        # Mock execution result
        return {
            "success": True,
            "action": "host_isolated",
            "ip_address": ip_address,
            "hostname": hostname,
            "reason": reason,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "isolation_type": "network",
            "message": "Host has been network isolated successfully (MOCK)",
            "next_steps": [
                "Verify threat containment",
                "Conduct forensic analysis",
                "Remediate threat",
                "Consider unisolation after remediation"
            ]
        }
    
    def execute_approved_actions(self) -> List[Dict]:
        """
        Execute all approved actions that haven't been executed yet.
        
        Returns:
            List of execution results
        """
        if not self.approval_service:
            return []
        
        try:
            from services.approval_service import ActionStatus
            
            # Get approved but not executed actions
            approved_actions = self.approval_service.list_actions(status=ActionStatus.APPROVED)
            results = []
            
            for action in approved_actions:
                # Skip if already executed
                if action.executed_at:
                    continue
                
                # Execute based on action type
                if action.action_type == "isolate_host":
                    result = self._execute_isolation(
                        ip_address=action.target,
                        hostname=action.parameters.get('hostname'),
                        reason=action.reason,
                        confidence=action.confidence
                    )
                    
                    if result.get('success'):
                        self.approval_service.mark_executed(action.action_id, result)
                    else:
                        self.approval_service.mark_failed(action.action_id, result.get('error', 'Unknown error'))
                    
                    results.append({
                        "action_id": action.action_id,
                        "action_type": action.action_type,
                        "target": action.target,
                        "result": result
                    })
            
            return results
        
        except Exception as e:
            logger.error(f"Error executing approved actions: {e}")
            return []
    
    def investigate_and_respond(
        self,
        finding_id: str,
        auto_execute: bool = True
    ) -> Dict:
        """
        Full investigation and response workflow for a finding.
        
        Args:
            finding_id: Finding ID to investigate
            auto_execute: Whether to auto-execute high-confidence actions
        
        Returns:
            Investigation and response result
        """
        try:
            # Load finding
            from services.data_service import DataService
            data_service = DataService()
            finding = data_service.get_finding(finding_id)
            
            if not finding:
                return {"error": f"Finding {finding_id} not found"}
            
            # Extract entity information
            entity_context = finding.get('entity_context', {})
            src_ips = entity_context.get('src_ips', [])
            hostnames = entity_context.get('hostnames', [])
            
            if not src_ips:
                return {"error": "No source IPs found in finding"}
            
            target_ip = src_ips[0]
            target_hostname = hostnames[0] if hostnames else None
            
            # Correlate with multiple sources
            correlation = self.correlate_alerts(
                tempo_flow_alert=finding,
                crowdstrike_alert=None,  # Would fetch from CrowdStrike in production
                splunk_results=None  # Would fetch from Splunk in production
            )
            
            # Determine action
            confidence = correlation['confidence']
            
            if confidence >= 0.85 and auto_execute:
                # Create isolation action
                action_result = self.create_isolation_action(
                    ip_address=target_ip,
                    hostname=target_hostname,
                    confidence=confidence,
                    reason=f"Automated response to finding {finding_id}",
                    evidence=[finding_id],
                    correlation_data=correlation
                )
                
                return {
                    "finding_id": finding_id,
                    "target": target_ip,
                    "correlation": correlation,
                    "action": action_result
                }
            else:
                # Just report findings
                return {
                    "finding_id": finding_id,
                    "target": target_ip,
                    "correlation": correlation,
                    "action": {
                        "status": "no_action",
                        "reason": f"Confidence below threshold ({confidence:.2%} < 0.85)"
                    }
                }
        
        except Exception as e:
            logger.error(f"Error in investigate_and_respond: {e}")
            return {"error": str(e)}


# Singleton instance
_autonomous_response_service: Optional[AutonomousResponseService] = None


def get_autonomous_response_service() -> AutonomousResponseService:
    """Get singleton AutonomousResponseService instance."""
    global _autonomous_response_service
    if _autonomous_response_service is None:
        _autonomous_response_service = AutonomousResponseService()
    return _autonomous_response_service

