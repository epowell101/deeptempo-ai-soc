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

