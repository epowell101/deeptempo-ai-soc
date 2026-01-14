"""
Database-backed data service for unified access to PostgreSQL data with fallback to JSON.

This service provides a compatible interface with the original DataService but uses
PostgreSQL as the primary data store, with optional fallback to JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class DatabaseDataService:
    """Service for accessing and managing data via PostgreSQL database with automatic JSON fallback."""
    
    def __init__(self, use_database: bool = True, data_dir: Optional[Path] = None, auto_fallback: bool = True):
        """
        Initialize the database data service.
        
        Args:
            use_database: If True, try to use PostgreSQL first
            data_dir: Optional path to data directory for JSON fallback
            auto_fallback: If True, automatically fallback to JSON if database unavailable
        """
        self.use_database = False  # Will be set to True if database works
        self._db_service = None
        self._json_service = None
        self._auto_fallback = auto_fallback
        
        # Try to initialize database service if requested
        if use_database:
            database_available = self._try_initialize_database()
            
            if database_available:
                self.use_database = True
                logger.info("✓ Using PostgreSQL database for data storage")
            elif auto_fallback:
                logger.warning("⚠ PostgreSQL not available, falling back to JSON file storage")
                self._initialize_json_service(data_dir)
            else:
                logger.error("❌ PostgreSQL not available and auto-fallback disabled")
                raise RuntimeError("Database connection required but unavailable")
        else:
            # Explicitly requested JSON storage
            logger.info("Using JSON file storage (DATA_BACKEND=json)")
            self._initialize_json_service(data_dir)
    
    def _try_initialize_database(self) -> bool:
        """
        Try to initialize PostgreSQL database connection.
        
        Returns:
            True if database is available and ready, False otherwise
        """
        try:
            from database.connection import get_db_manager, init_database
            from database.service import DatabaseService
            
            # Try to initialize database
            try:
                init_database(echo=False, create_tables=True)
            except Exception as init_error:
                logger.debug(f"Database initialization warning: {init_error}")
            
            # Get database manager and check health
            db_manager = get_db_manager()
            
            # Perform health check
            if db_manager.health_check():
                self._db_service = DatabaseService()
                logger.info("✓ PostgreSQL connection verified")
                return True
            else:
                logger.warning("Database health check failed")
                return False
                
        except ImportError as e:
            logger.debug(f"Database modules not available: {e}")
            return False
        except Exception as e:
            logger.warning(f"Failed to connect to PostgreSQL: {e}")
            logger.debug(f"Database connection error details: {e}", exc_info=True)
            return False
    
    def _initialize_json_service(self, data_dir: Optional[Path] = None):
        """Initialize JSON file storage service."""
        from services.data_service import DataService
        self._json_service = DataService(data_dir=data_dir)
        logger.info("✓ JSON file storage initialized")
    
    def is_using_database(self) -> bool:
        """Check if currently using PostgreSQL database."""
        return self.use_database and self._db_service is not None
    
    def get_backend_info(self) -> dict:
        """Get information about the current backend."""
        return {
            'backend': 'postgresql' if self.use_database else 'json',
            'database_available': self._db_service is not None,
            'json_available': self._json_service is not None,
            'auto_fallback': self._auto_fallback
        }
    
    # ========== Finding Operations ==========
    
    def get_findings(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get all findings.
        
        Args:
            force_refresh: Force refresh from data source (ignored for database).
        
        Returns:
            List of finding dictionaries.
        """
        if self.use_database and self._db_service:
            try:
                findings_objs = self._db_service.get_findings(limit=10000)
                return [f.to_dict() for f in findings_objs]
            except Exception as e:
                logger.error(f"Error getting findings from database: {e}")
                return []
        else:
            return self._json_service.get_findings(force_refresh=force_refresh)
    
    def get_finding(self, finding_id: str) -> Optional[Dict]:
        """
        Get a specific finding by ID.
        
        Args:
            finding_id: The finding ID.
        
        Returns:
            Finding dictionary or None if not found.
        """
        if self.use_database and self._db_service:
            try:
                finding = self._db_service.get_finding(finding_id)
                return finding.to_dict() if finding else None
            except Exception as e:
                logger.error(f"Error getting finding from database: {e}")
                return None
        else:
            return self._json_service.get_finding(finding_id)
    
    def save_findings(self, findings: List[Dict]) -> bool:
        """
        Save findings.
        
        Args:
            findings: List of finding dictionaries.
        
        Returns:
            True if successful, False otherwise.
        """
        if self.use_database and self._db_service:
            # Not implemented for database (use create_finding instead)
            logger.warning("save_findings not implemented for database backend")
            return False
        else:
            return self._json_service.save_findings(findings)
    
    # ========== Case Operations ==========
    
    def get_cases(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get all cases.
        
        Args:
            force_refresh: Force refresh from data source (ignored for database).
        
        Returns:
            List of case dictionaries.
        """
        if self.use_database and self._db_service:
            try:
                cases_objs = self._db_service.get_cases(limit=10000)
                return [c.to_dict() for c in cases_objs]
            except Exception as e:
                logger.error(f"Error getting cases from database: {e}")
                return []
        else:
            return self._json_service.get_cases(force_refresh=force_refresh)
    
    def get_case(self, case_id: str) -> Optional[Dict]:
        """
        Get a specific case by ID.
        
        Args:
            case_id: The case ID.
        
        Returns:
            Case dictionary or None if not found.
        """
        if self.use_database and self._db_service:
            try:
                case = self._db_service.get_case(case_id, include_findings=True)
                return case.to_dict() if case else None
            except Exception as e:
                logger.error(f"Error getting case from database: {e}")
                return None
        else:
            return self._json_service.get_case(case_id)
    
    def save_cases(self, cases: List[Dict]) -> bool:
        """
        Save cases.
        
        Args:
            cases: List of case dictionaries.
        
        Returns:
            True if successful, False otherwise.
        """
        if self.use_database and self._db_service:
            # Not implemented for database (use create_case instead)
            logger.warning("save_cases not implemented for database backend")
            return False
        else:
            return self._json_service.save_cases(cases)
    
    def create_case(
        self,
        title: str,
        finding_ids: List[str],
        priority: str = "medium",
        description: str = "",
        status: str = "open"
    ) -> Optional[Dict]:
        """
        Create a new case.
        
        Args:
            title: Case title.
            finding_ids: List of finding IDs to link.
            priority: Case priority (low, medium, high, critical).
            description: Case description.
            status: Case status (new, open, in-progress, resolved, closed).
        
        Returns:
            Created case dictionary or None if failed.
        """
        if self.use_database and self._db_service:
            try:
                import uuid
                case_id = f"case-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:8]}"
                
                case = self._db_service.create_case(
                    case_id=case_id,
                    title=title,
                    finding_ids=finding_ids,
                    description=description,
                    status=status,
                    priority=priority
                )
                return case.to_dict() if case else None
            except Exception as e:
                logger.error(f"Error creating case in database: {e}")
                return None
        else:
            return self._json_service.create_case(
                title=title,
                finding_ids=finding_ids,
                priority=priority,
                description=description,
                status=status
            )
    
    def update_case(self, case_id: str, **updates) -> bool:
        """
        Update an existing case.
        
        Args:
            case_id: The case ID to update.
            **updates: Fields to update (status, priority, notes, etc.).
        
        Returns:
            True if successful, False otherwise.
        """
        if self.use_database and self._db_service:
            try:
                return self._db_service.update_case(case_id, **updates)
            except Exception as e:
                logger.error(f"Error updating case in database: {e}")
                return False
        else:
            return self._json_service.update_case(case_id, **updates)
    
    def delete_case(self, case_id: str) -> bool:
        """
        Delete a case.
        
        Args:
            case_id: The case ID to delete.
        
        Returns:
            True if successful, False otherwise.
        """
        if self.use_database and self._db_service:
            try:
                return self._db_service.delete_case(case_id)
            except Exception as e:
                logger.error(f"Error deleting case from database: {e}")
                return False
        else:
            return self._json_service.delete_case(case_id)
    
    # ========== Demo Layer Operations (JSON only for now) ==========
    
    def get_demo_layer(self) -> Optional[Dict]:
        """Get the ATT&CK Navigator demo layer."""
        if self._json_service:
            return self._json_service.get_demo_layer()
        return None
    
    def save_demo_layer(self, layer: Dict) -> bool:
        """Save ATT&CK Navigator layer."""
        if self._json_service:
            return self._json_service.save_demo_layer(layer)
        return False
    
    # ========== Export/Import Operations ==========
    
    def export_findings(self, output_path: Path, format: str = "json") -> bool:
        """Export findings to a file."""
        findings = self.get_findings()
        
        try:
            if format == "jsonl":
                with open(output_path, 'w') as f:
                    for finding in findings:
                        f.write(json.dumps(finding) + '\n')
            else:  # json
                with open(output_path, 'w') as f:
                    json.dump({"findings": findings}, f, indent=2)
            
            logger.info(f"Exported {len(findings)} findings to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting findings: {e}")
            return False
    
    def import_findings(self, input_path: Path) -> int:
        """Import findings from a file."""
        if self._json_service:
            return self._json_service.import_findings(input_path)
        return 0
    
    # ========== Sketch Mappings ==========
    
    def get_sketch_mappings(self, force_refresh: bool = False) -> List[Dict]:
        """Get all sketch mappings."""
        if self._json_service:
            return self._json_service.get_sketch_mappings(force_refresh=force_refresh)
        return []
    
    def save_sketch_mappings(self, mappings: List[Dict]) -> bool:
        """Save sketch mappings."""
        if self._json_service:
            return self._json_service.save_sketch_mappings(mappings)
        return False
    
    # ========== Configuration ==========
    
    def set_data_source(self, source: str, **kwargs):
        """Set the data source (only for JSON backend)."""
        if self._json_service:
            self._json_service.set_data_source(source, **kwargs)
    
    def load_s3_config(self):
        """Load S3 configuration (only for JSON backend)."""
        if self._json_service:
            return self._json_service.load_s3_config()
        return False

