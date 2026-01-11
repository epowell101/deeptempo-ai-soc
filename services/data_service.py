"""Data service for unified access to JSON data files with caching."""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import keyring

logger = logging.getLogger(__name__)


class DataService:
    """Service for accessing and managing data files."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the data service.
        
        Args:
            data_dir: Optional path to data directory. Defaults to project data/ directory.
        """
        if data_dir is None:
            # Default to project data directory
            project_root = Path(__file__).parent.parent
            data_dir = project_root / "data"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.findings_file = self.data_dir / "findings.json"
        self.cases_file = self.data_dir / "cases.json"
        self.demo_layer_file = self.data_dir / "demo_layer.json"
        self.sketch_mappings_file = self.data_dir / "sketch_mappings.json"
        
        # Cache
        self._findings_cache: Optional[List[Dict]] = None
        self._cases_cache: Optional[List[Dict]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 5  # Cache TTL in seconds
        
        # Data source configuration
        self._data_source = "local"  # local, s3, or file
        self._s3_service = None
        self._uploaded_file_path = None
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache_timestamp is None:
            return False
        
        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age < self._cache_ttl
    
    def _invalidate_cache(self):
        """Invalidate the cache."""
        self._findings_cache = None
        self._cases_cache = None
        self._cache_timestamp = None
    
    def set_data_source(self, source: str, **kwargs):
        """
        Set the data source.
        
        Args:
            source: Data source type ("local", "s3", or "file")
            **kwargs: Additional arguments:
                - For "s3": bucket_name, region, access_key, secret_key, findings_path, cases_path
                - For "file": file_path
        """
        self._data_source = source
        self._invalidate_cache()
        
        if source == "s3":
            try:
                from services.s3_service import S3Service
                self._s3_service = S3Service(
                    bucket_name=kwargs.get('bucket_name', ''),
                    region_name=kwargs.get('region', 'us-east-1'),
                    aws_access_key_id=kwargs.get('access_key') or None,
                    aws_secret_access_key=kwargs.get('secret_key') or None
                )
                self._s3_findings_path = kwargs.get('findings_path', 'findings.json')
                self._s3_cases_path = kwargs.get('cases_path', 'cases.json')
            except ImportError:
                logger.error("boto3 not installed. Cannot use S3 data source.")
                self._data_source = "local"
        elif source == "file":
            self._uploaded_file_path = kwargs.get('file_path')
        else:
            self._s3_service = None
            self._uploaded_file_path = None
    
    def load_s3_config(self):
        """Load S3 configuration from settings."""
        try:
            config_file = Path.home() / '.deeptempo' / 's3_config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                SERVICE_NAME = "deeptempo-ai-soc"
                access_key = keyring.get_password(SERVICE_NAME, "s3_access_key_id") or ""
                secret_key = keyring.get_password(SERVICE_NAME, "s3_secret_access_key") or ""
                
                self.set_data_source(
                    "s3",
                    bucket_name=config.get('bucket_name', ''),
                    region=config.get('region', 'us-east-1'),
                    access_key=access_key,
                    secret_key=secret_key,
                    findings_path=config.get('findings_path', 'findings.json'),
                    cases_path=config.get('cases_path', 'cases.json')
                )
                return True
        except Exception as e:
            logger.error(f"Error loading S3 config: {e}")
        return False
    
    def get_findings(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get all findings.
        
        Args:
            force_refresh: Force refresh from disk, ignoring cache.
        
        Returns:
            List of finding dictionaries.
        """
        if not force_refresh and self._is_cache_valid() and self._findings_cache is not None:
            return self._findings_cache
        
        # Load from appropriate source
        if self._data_source == "s3" and self._s3_service:
            findings = self._s3_service.get_findings(self._s3_findings_path)
            self._findings_cache = findings
            self._cache_timestamp = datetime.now()
            return findings
        elif self._data_source == "file" and self._uploaded_file_path:
            try:
                with open(self._uploaded_file_path, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and 'findings' in data:
                    findings = data['findings']
                elif isinstance(data, list):
                    findings = data
                else:
                    logger.error(f"Unexpected findings format: {type(data)}")
                    findings = []
                
                self._findings_cache = findings
                self._cache_timestamp = datetime.now()
                return findings
            except Exception as e:
                logger.error(f"Error loading findings from file: {e}")
                return []
        else:
            # Default to local file
            if not self.findings_file.exists():
                logger.warning(f"Findings file not found: {self.findings_file}")
                self._findings_cache = []
                return []
            
            try:
                with open(self.findings_file, 'r') as f:
                    data = json.load(f)
                
                # Handle both formats: {"findings": [...]} or [...]
                if isinstance(data, dict) and 'findings' in data:
                    findings = data['findings']
                elif isinstance(data, list):
                    findings = data
                else:
                    logger.error(f"Unexpected findings format: {type(data)}")
                    findings = []
                
                self._findings_cache = findings
                self._cache_timestamp = datetime.now()
                return findings
            
            except Exception as e:
                logger.error(f"Error loading findings: {e}")
                return []
    
    def get_finding(self, finding_id: str) -> Optional[Dict]:
        """
        Get a specific finding by ID.
        
        Args:
            finding_id: The finding ID.
        
        Returns:
            Finding dictionary or None if not found.
        """
        findings = self.get_findings()
        for finding in findings:
            if finding.get('finding_id') == finding_id:
                return finding
        return None
    
    def save_findings(self, findings: List[Dict]) -> bool:
        """
        Save findings to disk.
        
        Args:
            findings: List of finding dictionaries.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Ensure directory exists
            self.findings_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save in standard format
            data = {"findings": findings}
            
            with open(self.findings_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Invalidate cache
            self._invalidate_cache()
            
            logger.info(f"Saved {len(findings)} findings to {self.findings_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving findings: {e}")
            return False
    
    def get_cases(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get all cases.
        
        Args:
            force_refresh: Force refresh from disk, ignoring cache.
        
        Returns:
            List of case dictionaries.
        """
        if not force_refresh and self._is_cache_valid() and self._cases_cache is not None:
            return self._cases_cache
        
        # Load from appropriate source
        if self._data_source == "s3" and self._s3_service:
            cases = self._s3_service.get_cases(self._s3_cases_path)
            self._cases_cache = cases
            self._cache_timestamp = datetime.now()
            return cases
        elif self._data_source == "file" and self._uploaded_file_path:
            # For uploaded files, try to load cases from the same file or separate cases file
            try:
                with open(self._uploaded_file_path, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, dict):
                    if 'cases' in data:
                        cases = data['cases']
                    else:
                        cases = []
                elif isinstance(data, list):
                    # Assume it's findings only
                    cases = []
                else:
                    cases = []
                
                self._cases_cache = cases
                self._cache_timestamp = datetime.now()
                return cases
            except Exception as e:
                logger.error(f"Error loading cases from file: {e}")
                return []
        else:
            # Default to local file
            if not self.cases_file.exists():
                logger.warning(f"Cases file not found: {self.cases_file}")
                self._cases_cache = []
                return []
            
            try:
                with open(self.cases_file, 'r') as f:
                    data = json.load(f)
                
                # Handle both formats: {"cases": [...]} or [...]
                if isinstance(data, dict) and 'cases' in data:
                    cases = data['cases']
                elif isinstance(data, list):
                    cases = data
                else:
                    logger.error(f"Unexpected cases format: {type(data)}")
                    cases = []
                
                self._cases_cache = cases
                self._cache_timestamp = datetime.now()
                return cases
            
            except Exception as e:
                logger.error(f"Error loading cases: {e}")
                return []
    
    def get_case(self, case_id: str) -> Optional[Dict]:
        """
        Get a specific case by ID.
        
        Args:
            case_id: The case ID.
        
        Returns:
            Case dictionary or None if not found.
        """
        cases = self.get_cases()
        for case in cases:
            if case.get('case_id') == case_id:
                return case
        return None
    
    def save_cases(self, cases: List[Dict]) -> bool:
        """
        Save cases to disk.
        
        Args:
            cases: List of case dictionaries.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Ensure directory exists
            self.cases_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save in standard format
            data = {"cases": cases}
            
            with open(self.cases_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Invalidate cache
            self._invalidate_cache()
            
            logger.info(f"Saved {len(cases)} cases to {self.cases_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving cases: {e}")
            return False
    
    def create_case(self, title: str, finding_ids: List[str], priority: str = "medium",
                   description: str = "", status: str = "open") -> Optional[Dict]:
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
        import uuid
        
        cases = self.get_cases()
        
        case_id = f"case-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat() + "Z"
        
        new_case = {
            "case_id": case_id,
            "title": title,
            "description": description,
            "finding_ids": finding_ids,
            "status": status,
            "priority": priority,
            "assignee": "",
            "tags": [],
            "notes": [],
            "timeline": [
                {
                    "timestamp": now,
                    "event": "Case created"
                }
            ],
            "created_at": now,
            "updated_at": now
        }
        
        cases.append(new_case)
        
        if self.save_cases(cases):
            return new_case
        return None
    
    def update_case(self, case_id: str, **updates) -> bool:
        """
        Update an existing case.
        
        Args:
            case_id: The case ID to update.
            **updates: Fields to update (status, priority, notes, etc.).
        
        Returns:
            True if successful, False otherwise.
        """
        cases = self.get_cases()
        
        for case in cases:
            if case.get('case_id') == case_id:
                # Update fields
                if 'status' in updates:
                    case['status'] = updates['status']
                if 'priority' in updates:
                    case['priority'] = updates['priority']
                if 'notes' in updates:
                    if 'notes' not in case:
                        case['notes'] = []
                    case['notes'].append({
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "text": updates['notes']
                    })
                if 'title' in updates:
                    case['title'] = updates['title']
                if 'description' in updates:
                    case['description'] = updates['description']
                
                case['updated_at'] = datetime.utcnow().isoformat() + "Z"
                
                return self.save_cases(cases)
        
        return False
    
    def get_demo_layer(self) -> Optional[Dict]:
        """
        Get the ATT&CK Navigator demo layer.
        
        Returns:
            Layer dictionary or None if not found.
        """
        if not self.demo_layer_file.exists():
            return None
        
        try:
            with open(self.demo_layer_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading demo layer: {e}")
            return None
    
    def save_demo_layer(self, layer: Dict) -> bool:
        """
        Save ATT&CK Navigator layer.
        
        Args:
            layer: Layer dictionary.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.demo_layer_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.demo_layer_file, 'w') as f:
                json.dump(layer, f, indent=2)
            
            logger.info(f"Saved demo layer to {self.demo_layer_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving demo layer: {e}")
            return False
    
    def export_findings(self, output_path: Path, format: str = "json") -> bool:
        """
        Export findings to a file.
        
        Args:
            output_path: Output file path.
            format: Export format (json or jsonl).
        
        Returns:
            True if successful, False otherwise.
        """
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
        """
        Import findings from a file.
        
        Args:
            input_path: Input file path.
        
        Returns:
            Number of findings imported.
        """
        if not input_path.exists():
            logger.error(f"Import file not found: {input_path}")
            return 0
        
        try:
            findings = []
            
            if input_path.suffix == ".jsonl":
                with open(input_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            findings.append(json.loads(line))
            else:  # json
                with open(input_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        findings = data
                    elif isinstance(data, dict) and 'findings' in data:
                        findings = data['findings']
            
            if findings:
                existing = self.get_findings()
                # Merge, avoiding duplicates
                existing_ids = {f.get('finding_id') for f in existing}
                new_findings = [f for f in findings if f.get('finding_id') not in existing_ids]
                all_findings = existing + new_findings
                self.save_findings(all_findings)
            
            logger.info(f"Imported {len(findings)} findings from {input_path}")
            return len(findings)
        
        except Exception as e:
            logger.error(f"Error importing findings: {e}")
            return 0
    
    def get_sketch_mappings(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get all sketch mappings.
        
        Args:
            force_refresh: Force refresh from disk.
        
        Returns:
            List of mapping dictionaries.
        """
        if not self.sketch_mappings_file.exists():
            return []
        
        try:
            with open(self.sketch_mappings_file, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'mappings' in data:
                return data['mappings']
            elif isinstance(data, list):
                return data
            else:
                return []
        
        except Exception as e:
            logger.error(f"Error loading sketch mappings: {e}")
            return []
    
    def save_sketch_mappings(self, mappings: List[Dict]) -> bool:
        """
        Save sketch mappings.
        
        Args:
            mappings: List of mapping dictionaries.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.sketch_mappings_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {"mappings": mappings}
            
            with open(self.sketch_mappings_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(mappings)} sketch mappings")
            return True
        
        except Exception as e:
            logger.error(f"Error saving sketch mappings: {e}")
            return False

