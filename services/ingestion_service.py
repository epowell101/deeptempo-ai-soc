"""
Data Ingestion Service for DeepTempo AI SOC

Handles ingestion of findings and cases from various formats:
- JSON files
- CSV files  
- JSONL (JSON Lines) files
- Direct JSON data

All data is stored in PostgreSQL when available, with fallback to JSON files.
"""

import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from io import StringIO

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting data from various formats into the database."""
    
    def __init__(self):
        """Initialize the ingestion service."""
        # Import here to avoid circular dependencies
        try:
            from database.service import DatabaseService
            from database.connection import get_db_manager
            
            db_manager = get_db_manager()
            if db_manager.health_check():
                self.db_service = DatabaseService()
                self.use_database = True
                logger.info("Ingestion service using PostgreSQL database")
            else:
                self.db_service = None
                self.use_database = False
                logger.warning("Database unavailable, using JSON fallback")
        except Exception as e:
            logger.warning(f"Database not available: {e}, using JSON fallback")
            self.db_service = None
            self.use_database = False
        
        # Statistics for reporting
        self.stats = {
            'findings_total': 0,
            'findings_imported': 0,
            'findings_skipped': 0,
            'findings_errors': 0,
            'cases_total': 0,
            'cases_imported': 0,
            'cases_skipped': 0,
            'cases_errors': 0,
        }
    
    def reset_stats(self):
        """Reset ingestion statistics."""
        for key in self.stats:
            self.stats[key] = 0
    
    def parse_timestamp(self, timestamp_value: Any) -> datetime:
        """
        Parse various timestamp formats to datetime.
        
        Args:
            timestamp_value: Timestamp as string, int, or datetime
        
        Returns:
            datetime object
        """
        if isinstance(timestamp_value, datetime):
            return timestamp_value
        
        if not timestamp_value:
            return datetime.utcnow()
        
        # If it's a Unix timestamp (int or float)
        if isinstance(timestamp_value, (int, float)):
            try:
                return datetime.fromtimestamp(timestamp_value)
            except (ValueError, OSError):
                pass
        
        # Try various string formats
        timestamp_str = str(timestamp_value)
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
        ]
        
        for fmt in formats:
            try:
                ts_str = timestamp_str.replace('+00:00', '').replace('Z', '')
                return datetime.strptime(ts_str, fmt.replace('Z', '').replace('%z', ''))
            except ValueError:
                continue
        
        logger.warning(f"Could not parse timestamp: {timestamp_value}, using current time")
        return datetime.utcnow()
    
    def ingest_finding(self, finding_data: Dict[str, Any]) -> bool:
        """
        Ingest a single finding into the database.
        
        Args:
            finding_data: Finding dictionary
        
        Returns:
            True if successful, False otherwise
        """
        finding_id = finding_data.get('finding_id')
        if not finding_id:
            logger.error("Finding missing finding_id")
            self.stats['findings_errors'] += 1
            return False
        
        try:
            if self.use_database and self.db_service:
                # Check if finding already exists
                existing = self.db_service.get_finding(finding_id)
                if existing:
                    logger.debug(f"Finding {finding_id} already exists, skipping")
                    self.stats['findings_skipped'] += 1
                    return True
                
                # Parse timestamp
                timestamp = self.parse_timestamp(finding_data.get('timestamp'))
                
                # Create finding in database
                finding = self.db_service.create_finding(
                    finding_id=finding_id,
                    embedding=finding_data.get('embedding', [0.0] * 768),  # Default empty embedding
                    mitre_predictions=finding_data.get('mitre_predictions', {}),
                    anomaly_score=float(finding_data.get('anomaly_score', 0.0)),
                    timestamp=timestamp,
                    data_source=finding_data.get('data_source', 'imported'),
                    entity_context=finding_data.get('entity_context'),
                    evidence_links=finding_data.get('evidence_links'),
                    cluster_id=finding_data.get('cluster_id'),
                    severity=finding_data.get('severity'),
                    status=finding_data.get('status', 'new')
                )
                
                if finding:
                    self.stats['findings_imported'] += 1
                    logger.debug(f"Imported finding: {finding_id}")
                    return True
                else:
                    self.stats['findings_errors'] += 1
                    logger.error(f"Failed to create finding: {finding_id}")
                    return False
            else:
                # Fallback to JSON file storage
                from services.data_service import DataService
                data_service = DataService()
                findings = data_service.get_findings()
                
                # Check for duplicate
                if any(f.get('finding_id') == finding_id for f in findings):
                    self.stats['findings_skipped'] += 1
                    return True
                
                findings.append(finding_data)
                if data_service.save_findings(findings):
                    self.stats['findings_imported'] += 1
                    return True
                else:
                    self.stats['findings_errors'] += 1
                    return False
        
        except Exception as e:
            self.stats['findings_errors'] += 1
            logger.error(f"Error ingesting finding {finding_id}: {e}")
            return False
    
    def ingest_case(self, case_data: Dict[str, Any]) -> bool:
        """
        Ingest a single case into the database.
        
        Args:
            case_data: Case dictionary
        
        Returns:
            True if successful, False otherwise
        """
        case_id = case_data.get('case_id')
        if not case_id:
            logger.error("Case missing case_id")
            self.stats['cases_errors'] += 1
            return False
        
        try:
            if self.use_database and self.db_service:
                # Check if case already exists
                existing = self.db_service.get_case(case_id)
                if existing:
                    logger.debug(f"Case {case_id} already exists, skipping")
                    self.stats['cases_skipped'] += 1
                    return True
                
                # Create case in database
                case = self.db_service.create_case(
                    case_id=case_id,
                    title=case_data.get('title', 'Imported Case'),
                    finding_ids=case_data.get('finding_ids', []),
                    description=case_data.get('description', ''),
                    status=case_data.get('status', 'new'),
                    priority=case_data.get('priority', 'medium'),
                    assignee=case_data.get('assignee'),
                    tags=case_data.get('tags', []),
                    notes=case_data.get('notes', []),
                    timeline=case_data.get('timeline', []),
                    activities=case_data.get('activities', []),
                    resolution_steps=case_data.get('resolution_steps', []),
                    mitre_techniques=case_data.get('mitre_techniques')
                )
                
                if case:
                    self.stats['cases_imported'] += 1
                    logger.debug(f"Imported case: {case_id}")
                    return True
                else:
                    self.stats['cases_errors'] += 1
                    logger.error(f"Failed to create case: {case_id}")
                    return False
            else:
                # Fallback to JSON file storage
                from services.data_service import DataService
                data_service = DataService()
                cases = data_service.get_cases()
                
                # Check for duplicate
                if any(c.get('case_id') == case_id for c in cases):
                    self.stats['cases_skipped'] += 1
                    return True
                
                cases.append(case_data)
                if data_service.save_cases(cases):
                    self.stats['cases_imported'] += 1
                    return True
                else:
                    self.stats['cases_errors'] += 1
                    return False
        
        except Exception as e:
            self.stats['cases_errors'] += 1
            logger.error(f"Error ingesting case {case_id}: {e}")
            return False
    
    def ingest_json_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Ingest data from a JSON file.
        
        Args:
            file_path: Path to JSON file
        
        Returns:
            Dictionary with statistics
        """
        self.reset_stats()
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return self.stats
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            findings = []
            cases = []
            
            if isinstance(data, dict):
                findings = data.get('findings', [])
                cases = data.get('cases', [])
            elif isinstance(data, list):
                # Assume it's a list of findings or cases based on keys
                if data and 'finding_id' in data[0]:
                    findings = data
                elif data and 'case_id' in data[0]:
                    cases = data
            
            self.stats['findings_total'] = len(findings)
            self.stats['cases_total'] = len(cases)
            
            # Ingest findings
            for finding in findings:
                self.ingest_finding(finding)
            
            # Ingest cases
            for case in cases:
                self.ingest_case(case)
            
            logger.info(f"JSON ingestion complete: {self.stats}")
            return self.stats
        
        except Exception as e:
            logger.error(f"Error ingesting JSON file: {e}")
            return self.stats
    
    def ingest_jsonl_file(self, file_path: Union[str, Path], data_type: str = 'finding') -> Dict[str, Any]:
        """
        Ingest data from a JSONL (JSON Lines) file.
        
        Args:
            file_path: Path to JSONL file
            data_type: Type of data ('finding' or 'case')
        
        Returns:
            Dictionary with statistics
        """
        self.reset_stats()
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return self.stats
        
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        if data_type == 'finding':
                            self.stats['findings_total'] += 1
                            self.ingest_finding(data)
                        elif data_type == 'case':
                            self.stats['cases_total'] += 1
                            self.ingest_case(data)
                    
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON on line {line_num}: {e}")
                        if data_type == 'finding':
                            self.stats['findings_errors'] += 1
                        else:
                            self.stats['cases_errors'] += 1
            
            logger.info(f"JSONL ingestion complete: {self.stats}")
            return self.stats
        
        except Exception as e:
            logger.error(f"Error ingesting JSONL file: {e}")
            return self.stats
    
    def ingest_csv_file(self, file_path: Union[str, Path], data_type: str = 'finding') -> Dict[str, Any]:
        """
        Ingest data from a CSV file.
        
        Args:
            file_path: Path to CSV file
            data_type: Type of data ('finding' or 'case')
        
        Returns:
            Dictionary with statistics
        """
        self.reset_stats()
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return self.stats
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        if data_type == 'finding':
                            self.stats['findings_total'] += 1
                            finding_data = self._csv_row_to_finding(row)
                            self.ingest_finding(finding_data)
                        elif data_type == 'case':
                            self.stats['cases_total'] += 1
                            case_data = self._csv_row_to_case(row)
                            self.ingest_case(case_data)
                    
                    except Exception as e:
                        logger.error(f"Error processing CSV row {row_num}: {e}")
                        if data_type == 'finding':
                            self.stats['findings_errors'] += 1
                        else:
                            self.stats['cases_errors'] += 1
            
            logger.info(f"CSV ingestion complete: {self.stats}")
            return self.stats
        
        except Exception as e:
            logger.error(f"Error ingesting CSV file: {e}")
            return self.stats
    
    def _csv_row_to_finding(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert CSV row to finding dictionary.
        
        Args:
            row: CSV row as dictionary
        
        Returns:
            Finding dictionary
        """
        # Generate finding_id if not present
        finding_id = row.get('finding_id')
        if not finding_id:
            import uuid
            finding_id = f"f-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        
        # Parse embedding if present (comma-separated floats)
        embedding = []
        if 'embedding' in row and row['embedding']:
            try:
                embedding = [float(x.strip()) for x in row['embedding'].split(',')]
            except ValueError:
                logger.warning(f"Invalid embedding format for {finding_id}, using empty")
                embedding = [0.0] * 768
        else:
            embedding = [0.0] * 768
        
        # Parse MITRE predictions (JSON string or comma-separated)
        mitre_predictions = {}
        if 'mitre_predictions' in row and row['mitre_predictions']:
            try:
                mitre_predictions = json.loads(row['mitre_predictions'])
            except json.JSONDecodeError:
                # Try comma-separated format: T1071.001:0.85,T1048.003:0.72
                try:
                    for pair in row['mitre_predictions'].split(','):
                        technique, score = pair.split(':')
                        mitre_predictions[technique.strip()] = float(score.strip())
                except:
                    logger.warning(f"Invalid mitre_predictions format for {finding_id}")
        
        # Parse entity context (JSON string)
        entity_context = None
        if 'entity_context' in row and row['entity_context']:
            try:
                entity_context = json.loads(row['entity_context'])
            except json.JSONDecodeError:
                logger.warning(f"Invalid entity_context format for {finding_id}")
        
        return {
            'finding_id': finding_id,
            'embedding': embedding,
            'mitre_predictions': mitre_predictions,
            'anomaly_score': float(row.get('anomaly_score', 0.0)),
            'timestamp': row.get('timestamp', datetime.utcnow().isoformat()),
            'data_source': row.get('data_source', 'csv_import'),
            'entity_context': entity_context,
            'evidence_links': None,
            'cluster_id': row.get('cluster_id'),
            'severity': row.get('severity'),
            'status': row.get('status', 'new')
        }
    
    def _csv_row_to_case(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert CSV row to case dictionary.
        
        Args:
            row: CSV row as dictionary
        
        Returns:
            Case dictionary
        """
        # Generate case_id if not present
        case_id = row.get('case_id')
        if not case_id:
            import uuid
            case_id = f"case-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:8]}"
        
        # Parse finding_ids (comma-separated)
        finding_ids = []
        if 'finding_ids' in row and row['finding_ids']:
            finding_ids = [fid.strip() for fid in row['finding_ids'].split(',')]
        
        # Parse tags (comma-separated)
        tags = []
        if 'tags' in row and row['tags']:
            tags = [tag.strip() for tag in row['tags'].split(',')]
        
        return {
            'case_id': case_id,
            'title': row.get('title', 'Imported Case'),
            'description': row.get('description', ''),
            'finding_ids': finding_ids,
            'status': row.get('status', 'new'),
            'priority': row.get('priority', 'medium'),
            'assignee': row.get('assignee'),
            'tags': tags,
            'notes': [],
            'timeline': [],
            'activities': [],
            'resolution_steps': [],
            'mitre_techniques': None
        }
    
    def ingest_from_string(
        self,
        data_string: str,
        format: str = 'json',
        data_type: str = 'finding'
    ) -> Dict[str, Any]:
        """
        Ingest data from a string.
        
        Args:
            data_string: Data as string
            format: Format ('json', 'jsonl', 'csv')
            data_type: Type of data ('finding' or 'case')
        
        Returns:
            Dictionary with statistics
        """
        self.reset_stats()
        
        try:
            if format == 'json':
                data = json.loads(data_string)
                
                findings = []
                cases = []
                
                if isinstance(data, dict):
                    findings = data.get('findings', [])
                    cases = data.get('cases', [])
                elif isinstance(data, list):
                    if data and 'finding_id' in data[0]:
                        findings = data
                    elif data and 'case_id' in data[0]:
                        cases = data
                
                self.stats['findings_total'] = len(findings)
                self.stats['cases_total'] = len(cases)
                
                for finding in findings:
                    self.ingest_finding(finding)
                
                for case in cases:
                    self.ingest_case(case)
            
            elif format == 'jsonl':
                for line in data_string.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    
                    data = json.loads(line)
                    
                    if data_type == 'finding':
                        self.stats['findings_total'] += 1
                        self.ingest_finding(data)
                    elif data_type == 'case':
                        self.stats['cases_total'] += 1
                        self.ingest_case(data)
            
            elif format == 'csv':
                reader = csv.DictReader(StringIO(data_string))
                
                for row in reader:
                    if data_type == 'finding':
                        self.stats['findings_total'] += 1
                        finding_data = self._csv_row_to_finding(row)
                        self.ingest_finding(finding_data)
                    elif data_type == 'case':
                        self.stats['cases_total'] += 1
                        case_data = self._csv_row_to_case(row)
                        self.ingest_case(case_data)
            
            logger.info(f"String ingestion complete: {self.stats}")
            return self.stats
        
        except Exception as e:
            logger.error(f"Error ingesting from string: {e}")
            return self.stats

