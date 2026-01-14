"""
Database service layer for DeepTempo AI SOC.

Provides high-level database operations for cases, findings, and related entities.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import Session

from database.models import Case, Finding, SketchMapping, AttackLayer, case_findings
from database.connection import get_db_manager

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service layer for database operations."""
    
    def __init__(self):
        """Initialize the database service."""
        self.db_manager = get_db_manager()
    
    # ========== Finding Operations ==========
    
    def create_finding(
        self,
        finding_id: str,
        embedding: List[float],
        mitre_predictions: dict,
        anomaly_score: float,
        timestamp: datetime,
        data_source: str,
        **kwargs
    ) -> Optional[Finding]:
        """
        Create a new finding.
        
        Args:
            finding_id: Unique finding ID
            embedding: 768-dimensional embedding vector
            mitre_predictions: MITRE ATT&CK predictions
            anomaly_score: Anomaly score (0-1)
            timestamp: Finding timestamp
            data_source: Data source type
            **kwargs: Additional fields (entity_context, evidence_links, cluster_id, severity, status)
        
        Returns:
            Created Finding object or None if failed
        """
        try:
            with self.db_manager.session_scope() as session:
                finding = Finding(
                    finding_id=finding_id,
                    embedding=embedding,
                    mitre_predictions=mitre_predictions,
                    anomaly_score=anomaly_score,
                    timestamp=timestamp,
                    data_source=data_source,
                    entity_context=kwargs.get('entity_context'),
                    evidence_links=kwargs.get('evidence_links'),
                    cluster_id=kwargs.get('cluster_id'),
                    severity=kwargs.get('severity'),
                    status=kwargs.get('status', 'new')
                )
                session.add(finding)
                session.flush()
                session.refresh(finding)
                logger.info(f"Created finding: {finding_id}")
                return finding
        except Exception as e:
            logger.error(f"Error creating finding {finding_id}: {e}")
            return None
    
    def get_finding(self, finding_id: str) -> Optional[Finding]:
        """
        Get a finding by ID.
        
        Args:
            finding_id: Finding ID
        
        Returns:
            Finding object or None if not found
        """
        try:
            with self.db_manager.session_scope() as session:
                finding = session.get(Finding, finding_id)
                if finding:
                    # Detach from session to avoid lazy loading issues
                    session.expunge(finding)
                return finding
        except Exception as e:
            logger.error(f"Error getting finding {finding_id}: {e}")
            return None
    
    def get_findings(
        self,
        severity: Optional[str] = None,
        data_source: Optional[str] = None,
        cluster_id: Optional[str] = None,
        min_anomaly_score: Optional[float] = None,
        status: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Finding]:
        """
        Get findings with optional filters.
        
        Args:
            severity: Filter by severity
            data_source: Filter by data source
            cluster_id: Filter by cluster ID
            min_anomaly_score: Minimum anomaly score
            status: Filter by status
            limit: Maximum number of results
            offset: Offset for pagination
        
        Returns:
            List of Finding objects
        """
        try:
            with self.db_manager.session_scope() as session:
                query = select(Finding)
                
                # Apply filters
                filters = []
                if severity:
                    filters.append(Finding.severity == severity)
                if data_source:
                    filters.append(Finding.data_source == data_source)
                if cluster_id is not None:
                    filters.append(Finding.cluster_id == cluster_id)
                if min_anomaly_score is not None:
                    filters.append(Finding.anomaly_score >= min_anomaly_score)
                if status:
                    filters.append(Finding.status == status)
                
                if filters:
                    query = query.where(and_(*filters))
                
                # Apply ordering, limit, and offset
                query = query.order_by(Finding.timestamp.desc())
                query = query.limit(limit).offset(offset)
                
                findings = session.execute(query).scalars().all()
                
                # Detach from session
                for finding in findings:
                    session.expunge(finding)
                
                return findings
        except Exception as e:
            logger.error(f"Error getting findings: {e}")
            return []
    
    def update_finding(self, finding_id: str, **updates) -> bool:
        """
        Update a finding.
        
        Args:
            finding_id: Finding ID
            **updates: Fields to update
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.session_scope() as session:
                finding = session.get(Finding, finding_id)
                if not finding:
                    logger.warning(f"Finding not found: {finding_id}")
                    return False
                
                # Update allowed fields
                for key, value in updates.items():
                    if hasattr(finding, key):
                        setattr(finding, key, value)
                
                finding.updated_at = datetime.utcnow()
                session.flush()
                logger.info(f"Updated finding: {finding_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating finding {finding_id}: {e}")
            return False
    
    def delete_finding(self, finding_id: str) -> bool:
        """
        Delete a finding.
        
        Args:
            finding_id: Finding ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.session_scope() as session:
                finding = session.get(Finding, finding_id)
                if not finding:
                    logger.warning(f"Finding not found: {finding_id}")
                    return False
                
                session.delete(finding)
                logger.info(f"Deleted finding: {finding_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting finding {finding_id}: {e}")
            return False
    
    # ========== Case Operations ==========
    
    def create_case(
        self,
        case_id: str,
        title: str,
        finding_ids: List[str],
        **kwargs
    ) -> Optional[Case]:
        """
        Create a new case.
        
        Args:
            case_id: Unique case ID
            title: Case title
            finding_ids: List of finding IDs to link
            **kwargs: Additional fields (description, status, priority, assignee, tags, etc.)
        
        Returns:
            Created Case object or None if failed
        """
        try:
            with self.db_manager.session_scope() as session:
                # Create case
                now = datetime.utcnow()
                case = Case(
                    case_id=case_id,
                    title=title,
                    description=kwargs.get('description', ''),
                    status=kwargs.get('status', 'new'),
                    priority=kwargs.get('priority', 'medium'),
                    assignee=kwargs.get('assignee'),
                    tags=kwargs.get('tags', []),
                    notes=kwargs.get('notes', []),
                    timeline=kwargs.get('timeline', [{'timestamp': now.isoformat() + 'Z', 'event': 'Case created'}]),
                    activities=kwargs.get('activities', []),
                    resolution_steps=kwargs.get('resolution_steps', []),
                    mitre_techniques=kwargs.get('mitre_techniques'),
                )
                session.add(case)
                session.flush()
                
                # Link findings
                if finding_ids:
                    findings = session.execute(
                        select(Finding).where(Finding.finding_id.in_(finding_ids))
                    ).scalars().all()
                    case.findings.extend(findings)
                    session.flush()
                
                session.refresh(case)
                logger.info(f"Created case: {case_id} with {len(finding_ids)} findings")
                return case
        except Exception as e:
            logger.error(f"Error creating case {case_id}: {e}")
            return None
    
    def get_case(self, case_id: str, include_findings: bool = False) -> Optional[Case]:
        """
        Get a case by ID.
        
        Args:
            case_id: Case ID
            include_findings: If True, include full finding objects
        
        Returns:
            Case object or None if not found
        """
        try:
            with self.db_manager.session_scope() as session:
                case = session.get(Case, case_id)
                if case:
                    # Force load findings if needed
                    if include_findings:
                        _ = case.findings  # Trigger lazy load
                    session.expunge(case)
                return case
        except Exception as e:
            logger.error(f"Error getting case {case_id}: {e}")
            return None
    
    def get_cases(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Case]:
        """
        Get cases with optional filters.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            assignee: Filter by assignee
            limit: Maximum number of results
            offset: Offset for pagination
        
        Returns:
            List of Case objects
        """
        try:
            with self.db_manager.session_scope() as session:
                query = select(Case)
                
                # Apply filters
                filters = []
                if status:
                    filters.append(Case.status == status)
                if priority:
                    filters.append(Case.priority == priority)
                if assignee:
                    filters.append(Case.assignee == assignee)
                
                if filters:
                    query = query.where(and_(*filters))
                
                # Apply ordering, limit, and offset
                query = query.order_by(Case.created_at.desc())
                query = query.limit(limit).offset(offset)
                
                cases = session.execute(query).scalars().all()
                
                # Detach from session
                for case in cases:
                    session.expunge(case)
                
                return cases
        except Exception as e:
            logger.error(f"Error getting cases: {e}")
            return []
    
    def update_case(self, case_id: str, **updates) -> bool:
        """
        Update a case.
        
        Args:
            case_id: Case ID
            **updates: Fields to update
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.session_scope() as session:
                case = session.get(Case, case_id)
                if not case:
                    logger.warning(f"Case not found: {case_id}")
                    return False
                
                # Update allowed fields
                for key, value in updates.items():
                    if hasattr(case, key):
                        setattr(case, key, value)
                
                case.updated_at = datetime.utcnow()
                session.flush()
                logger.info(f"Updated case: {case_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating case {case_id}: {e}")
            return False
    
    def delete_case(self, case_id: str) -> bool:
        """
        Delete a case.
        
        Args:
            case_id: Case ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.session_scope() as session:
                case = session.get(Case, case_id)
                if not case:
                    logger.warning(f"Case not found: {case_id}")
                    return False
                
                session.delete(case)
                logger.info(f"Deleted case: {case_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting case {case_id}: {e}")
            return False
    
    def add_finding_to_case(self, case_id: str, finding_id: str) -> bool:
        """
        Add a finding to a case.
        
        Args:
            case_id: Case ID
            finding_id: Finding ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.session_scope() as session:
                case = session.get(Case, case_id)
                finding = session.get(Finding, finding_id)
                
                if not case or not finding:
                    logger.warning(f"Case or finding not found: {case_id}, {finding_id}")
                    return False
                
                if finding not in case.findings:
                    case.findings.append(finding)
                    case.updated_at = datetime.utcnow()
                    session.flush()
                    logger.info(f"Added finding {finding_id} to case {case_id}")
                
                return True
        except Exception as e:
            logger.error(f"Error adding finding to case: {e}")
            return False
    
    def remove_finding_from_case(self, case_id: str, finding_id: str) -> bool:
        """
        Remove a finding from a case.
        
        Args:
            case_id: Case ID
            finding_id: Finding ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.session_scope() as session:
                case = session.get(Case, case_id)
                finding = session.get(Finding, finding_id)
                
                if not case or not finding:
                    logger.warning(f"Case or finding not found: {case_id}, {finding_id}")
                    return False
                
                if finding in case.findings:
                    case.findings.remove(finding)
                    case.updated_at = datetime.utcnow()
                    session.flush()
                    logger.info(f"Removed finding {finding_id} from case {case_id}")
                
                return True
        except Exception as e:
            logger.error(f"Error removing finding from case: {e}")
            return False
    
    # ========== Statistics ==========
    
    def get_case_statistics(self) -> Dict[str, Any]:
        """
        Get case statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.db_manager.session_scope() as session:
                total = session.query(func.count(Case.case_id)).scalar()
                
                # Count by status
                status_counts = {}
                for status, count in session.query(
                    Case.status, func.count(Case.case_id)
                ).group_by(Case.status).all():
                    status_counts[status] = count
                
                # Count by priority
                priority_counts = {}
                for priority, count in session.query(
                    Case.priority, func.count(Case.case_id)
                ).group_by(Case.priority).all():
                    priority_counts[priority] = count
                
                return {
                    'total': total,
                    'by_status': status_counts,
                    'by_priority': priority_counts
                }
        except Exception as e:
            logger.error(f"Error getting case statistics: {e}")
            return {'total': 0, 'by_status': {}, 'by_priority': {}}
    
    def get_finding_statistics(self) -> Dict[str, Any]:
        """
        Get finding statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.db_manager.session_scope() as session:
                total = session.query(func.count(Finding.finding_id)).scalar()
                
                # Count by severity
                severity_counts = {}
                for severity, count in session.query(
                    Finding.severity, func.count(Finding.finding_id)
                ).group_by(Finding.severity).all():
                    severity_counts[severity or 'unknown'] = count
                
                # Count by data source
                data_source_counts = {}
                for data_source, count in session.query(
                    Finding.data_source, func.count(Finding.finding_id)
                ).group_by(Finding.data_source).all():
                    data_source_counts[data_source] = count
                
                return {
                    'total': total,
                    'by_severity': severity_counts,
                    'by_data_source': data_source_counts
                }
        except Exception as e:
            logger.error(f"Error getting finding statistics: {e}")
            return {'total': 0, 'by_severity': {}, 'by_data_source': {}}

