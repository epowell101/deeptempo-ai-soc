"""
SQLAlchemy Database Models for DeepTempo AI SOC

Defines the database schema for cases, findings, and related entities.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, JSON, 
    ForeignKey, Table, Index, Boolean, ARRAY
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Association table for case-finding many-to-many relationship
case_findings = Table(
    'case_findings',
    Base.metadata,
    Column('case_id', String, ForeignKey('cases.case_id', ondelete='CASCADE'), primary_key=True),
    Column('finding_id', String, ForeignKey('findings.finding_id', ondelete='CASCADE'), primary_key=True),
    Column('added_at', DateTime, default=datetime.utcnow, nullable=False),
)


class Finding(Base):
    """Finding model - represents a security finding from DeepTempo LogLM."""
    
    __tablename__ = 'findings'
    
    # Primary key
    finding_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # Core finding data
    embedding: Mapped[List[float]] = mapped_column(ARRAY(Float), nullable=False)
    mitre_predictions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Entity context (optional fields)
    entity_context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Evidence links
    evidence_links: Mapped[Optional[List[dict]]] = mapped_column(JSONB, nullable=True)
    
    # Metadata
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_source: Mapped[str] = mapped_column(String(50), nullable=False)
    cluster_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default='new',
        server_default='new'
    )
    
    # AI-generated enrichment (cached analysis)
    ai_enrichment: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False, 
        default=datetime.utcnow,
        server_default='now()'
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False, 
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default='now()'
    )
    
    # Relationships
    cases: Mapped[List["Case"]] = relationship(
        "Case",
        secondary=case_findings,
        back_populates="findings",
        lazy='selectin'
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_finding_timestamp', 'timestamp'),
        Index('idx_finding_severity', 'severity'),
        Index('idx_finding_status', 'status'),
        Index('idx_finding_data_source', 'data_source'),
        Index('idx_finding_cluster_id', 'cluster_id'),
        Index('idx_finding_anomaly_score', 'anomaly_score'),
    )
    
    def to_dict(self) -> dict:
        """Convert finding to dictionary."""
        return {
            'finding_id': self.finding_id,
            'embedding': self.embedding,
            'mitre_predictions': self.mitre_predictions,
            'anomaly_score': self.anomaly_score,
            'entity_context': self.entity_context,
            'evidence_links': self.evidence_links,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'data_source': self.data_source,
            'cluster_id': self.cluster_id,
            'severity': self.severity,
            'status': self.status,
            'ai_enrichment': self.ai_enrichment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Case(Base):
    """Case model - represents an investigation case grouping related findings."""
    
    __tablename__ = 'cases'
    
    # Primary key
    case_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # Basic case information
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True, default='')
    
    # Status and priority
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        default='new',
        server_default='new'
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default='medium',
        server_default='medium'
    )
    
    # Assignment
    assignee: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Tags (array of strings)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True, default=[])
    
    # Notes (JSONB array)
    notes: Mapped[List[dict]] = mapped_column(JSONB, nullable=True, default=[])
    
    # Timeline events (JSONB array)
    timeline: Mapped[List[dict]] = mapped_column(JSONB, nullable=False, default=[])
    
    # Activities (JSONB array)
    activities: Mapped[Optional[List[dict]]] = mapped_column(JSONB, nullable=True, default=[])
    
    # Resolution steps (JSONB array)
    resolution_steps: Mapped[Optional[List[dict]]] = mapped_column(JSONB, nullable=True, default=[])
    
    # MITRE ATT&CK techniques
    mitre_techniques: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default='now()'
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default='now()'
    )
    
    # Relationships
    findings: Mapped[List[Finding]] = relationship(
        "Finding",
        secondary=case_findings,
        back_populates="cases",
        lazy='selectin'
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_case_status', 'status'),
        Index('idx_case_priority', 'priority'),
        Index('idx_case_assignee', 'assignee'),
        Index('idx_case_created_at', 'created_at'),
        Index('idx_case_updated_at', 'updated_at'),
    )
    
    def to_dict(self, include_findings: bool = False) -> dict:
        """Convert case to dictionary."""
        result = {
            'case_id': self.case_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assignee': self.assignee,
            'tags': self.tags or [],
            'notes': self.notes or [],
            'timeline': self.timeline or [],
            'activities': self.activities or [],
            'resolution_steps': self.resolution_steps or [],
            'mitre_techniques': self.mitre_techniques or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_findings:
            result['findings'] = [f.to_dict() for f in self.findings]
        else:
            result['finding_ids'] = [f.finding_id for f in self.findings]
        
        return result


class SketchMapping(Base):
    """Timesketch mapping model - links cases/findings to Timesketch sketches."""
    
    __tablename__ = 'sketch_mappings'
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Mapping information
    case_id: Mapped[Optional[str]] = mapped_column(
        String(50), 
        ForeignKey('cases.case_id', ondelete='CASCADE'),
        nullable=True
    )
    finding_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey('findings.finding_id', ondelete='CASCADE'),
        nullable=True
    )
    
    # Timesketch information
    sketch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    sketch_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sketch_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default='now()'
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_sketch_case_id', 'case_id'),
        Index('idx_sketch_finding_id', 'finding_id'),
        Index('idx_sketch_id', 'sketch_id'),
    )
    
    def to_dict(self) -> dict:
        """Convert sketch mapping to dictionary."""
        return {
            'id': self.id,
            'case_id': self.case_id,
            'finding_id': self.finding_id,
            'sketch_id': self.sketch_id,
            'sketch_name': self.sketch_name,
            'sketch_url': self.sketch_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class AttackLayer(Base):
    """ATT&CK Navigator layer storage."""
    
    __tablename__ = 'attack_layers'
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Layer information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    layer_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Association with case (optional)
    case_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey('cases.case_id', ondelete='SET NULL'),
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default='now()'
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default='now()'
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_attack_layer_case_id', 'case_id'),
        Index('idx_attack_layer_created_at', 'created_at'),
    )
    
    def to_dict(self) -> dict:
        """Convert attack layer to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'layer_data': self.layer_data,
            'case_id': self.case_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class AIDecisionLog(Base):
    """
    AI Decision Log - Tracks AI decisions for feedback and learning.
    
    This model enables human oversight and continuous improvement of AI agents
    by tracking all AI decisions, collecting human feedback, and measuring accuracy.
    """
    
    __tablename__ = 'ai_decision_logs'
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Decision context
    agent_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    workflow_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    finding_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey('findings.finding_id', ondelete='CASCADE'),
        nullable=True
    )
    case_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey('cases.case_id', ondelete='CASCADE'),
        nullable=True
    )
    
    # AI's decision
    decision_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Additional decision metadata
    decision_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Human feedback
    human_reviewer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    human_decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    feedback_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Grading (0-1 scale)
    accuracy_grade: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reasoning_grade: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    action_appropriateness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Outcome tracking
    actual_outcome: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    time_saved_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default='now()'
    )
    feedback_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_ai_decision_agent_id', 'agent_id'),
        Index('idx_ai_decision_finding_id', 'finding_id'),
        Index('idx_ai_decision_case_id', 'case_id'),
        Index('idx_ai_decision_timestamp', 'timestamp'),
        Index('idx_ai_decision_human_decision', 'human_decision'),
        Index('idx_ai_decision_actual_outcome', 'actual_outcome'),
    )
    
    def to_dict(self) -> dict:
        """Convert AI decision log to dictionary."""
        return {
            'id': self.id,
            'decision_id': self.decision_id,
            'agent_id': self.agent_id,
            'workflow_id': self.workflow_id,
            'finding_id': self.finding_id,
            'case_id': self.case_id,
            'decision_type': self.decision_type,
            'confidence_score': self.confidence_score,
            'reasoning': self.reasoning,
            'recommended_action': self.recommended_action,
            'decision_metadata': self.decision_metadata,
            'human_reviewer': self.human_reviewer,
            'human_decision': self.human_decision,
            'feedback_comment': self.feedback_comment,
            'accuracy_grade': self.accuracy_grade,
            'reasoning_grade': self.reasoning_grade,
            'action_appropriateness': self.action_appropriateness,
            'actual_outcome': self.actual_outcome,
            'time_saved_minutes': self.time_saved_minutes,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'feedback_timestamp': self.feedback_timestamp.isoformat() if self.feedback_timestamp else None,
        }


class SystemConfig(Base):
    """
    System Configuration - Stores system-wide configuration settings.
    
    This replaces file-based configs in ~/.deeptempo/ for better multi-user
    support, ACID compliance, and audit trails.
    """
    
    __tablename__ = 'system_config'
    
    # Primary key
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    
    # Configuration value (flexible JSONB storage)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='general',
        server_default='general'
    )
    
    # Audit fields
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default='now()'
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default='now()'
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_system_config_type', 'config_type'),
        Index('idx_system_config_updated_at', 'updated_at'),
    )
    
    def to_dict(self) -> dict:
        """Convert system config to dictionary."""
        return {
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'config_type': self.config_type,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class UserPreference(Base):
    """
    User Preferences - Stores per-user preferences and settings.
    
    Supports multi-user deployments with individual user settings.
    """
    
    __tablename__ = 'user_preferences'
    
    # Primary key
    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    
    # Preferences as flexible JSONB
    preferences: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    
    # User metadata
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default='now()'
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default='now()'
    )
    
    # Last login tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def to_dict(self) -> dict:
        """Convert user preference to dictionary."""
        return {
            'user_id': self.user_id,
            'preferences': self.preferences,
            'display_name': self.display_name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }


class IntegrationConfig(Base):
    """
    Integration Configuration - Stores non-sensitive integration settings.
    
    Note: Secrets (API keys, passwords) remain in secrets_manager for security.
    This stores connection details, preferences, and enabled/disabled state.
    """
    
    __tablename__ = 'integration_configs'
    
    # Primary key
    integration_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    
    # Integration state
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Configuration (non-sensitive only)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    
    # Metadata
    integration_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    integration_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Health status
    last_test_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_test_success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default='now()'
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default='now()'
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_integration_enabled', 'enabled'),
        Index('idx_integration_type', 'integration_type'),
        Index('idx_integration_updated_at', 'updated_at'),
    )
    
    def to_dict(self) -> dict:
        """Convert integration config to dictionary."""
        return {
            'integration_id': self.integration_id,
            'enabled': self.enabled,
            'config': self.config,
            'integration_name': self.integration_name,
            'integration_type': self.integration_type,
            'description': self.description,
            'last_test_at': self.last_test_at.isoformat() if self.last_test_at else None,
            'last_test_success': self.last_test_success,
            'last_error': self.last_error,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ConfigAuditLog(Base):
    """
    Configuration Audit Log - Tracks all configuration changes for compliance.
    
    Provides full audit trail of who changed what and when.
    """
    
    __tablename__ = 'config_audit_log'
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # What was changed
    config_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config_key: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Change details
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # create, update, delete
    old_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Who made the change
    changed_by: Mapped[str] = mapped_column(String(100), nullable=False)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # When
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default='now()'
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_config_type', 'config_type'),
        Index('idx_audit_config_key', 'config_key'),
        Index('idx_audit_changed_by', 'changed_by'),
        Index('idx_audit_timestamp', 'timestamp'),
    )
    
    def to_dict(self) -> dict:
        """Convert audit log entry to dictionary."""
        return {
            'id': self.id,
            'config_type': self.config_type,
            'config_key': self.config_key,
            'action': self.action,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'changed_by': self.changed_by,
            'change_reason': self.change_reason,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }

