"""Sketch manager for managing case-sketch relationships."""

import logging
import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SketchManager:
    """Manages the relationship between DeepTempo cases and Timesketch sketches."""
    
    def __init__(self, mappings_file: Optional[Path] = None):
        """
        Initialize sketch manager.
        
        Args:
            mappings_file: Path to sketch mappings file. Defaults to data/sketch_mappings.json
        """
        if mappings_file is None:
            project_root = Path(__file__).parent.parent
            mappings_file = project_root / "data" / "sketch_mappings.json"
        
        self.mappings_file = Path(mappings_file)
        self.mappings_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_mappings(self) -> Dict:
        """Load sketch mappings from file."""
        if not self.mappings_file.exists():
            return {"mappings": []}
        
        try:
            with open(self.mappings_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading sketch mappings: {e}")
            return {"mappings": []}
    
    def _save_mappings(self, data: Dict) -> bool:
        """Save sketch mappings to file."""
        try:
            with open(self.mappings_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving sketch mappings: {e}")
            return False
    
    def create_sketch_for_case(self, case_id: str, sketch_id: str, 
                               sketch_name: str, timesketch_service) -> bool:
        """
        Create a mapping between a case and a sketch.
        
        Args:
            case_id: Case ID
            sketch_id: Sketch ID from Timesketch
            sketch_name: Sketch name
            timesketch_service: TimesketchService instance (can be None)
        
        Returns:
            True if successful, False otherwise.
        """
        if not timesketch_service:
            logger.warning(f"Cannot create sketch mapping for {case_id}: Timesketch service not available")
            return False
        
        try:
            data = self._load_mappings()
            mappings = data.get('mappings', [])
            
            # Check if mapping already exists
            for mapping in mappings:
                if mapping.get('case_id') == case_id:
                    # Update existing mapping
                    mapping['sketch_id'] = sketch_id
                    mapping['sketch_name'] = sketch_name
                    mapping['last_sync'] = datetime.now().isoformat()
                    mapping['sync_status'] = 'synced'
                    break
            else:
                # Create new mapping
                new_mapping = {
                    'case_id': case_id,
                    'sketch_id': sketch_id,
                    'sketch_name': sketch_name,
                    'created_at': datetime.now().isoformat(),
                    'last_sync': datetime.now().isoformat(),
                    'sync_status': 'synced',
                    'auto_sync': True
                }
                mappings.append(new_mapping)
            
            data['mappings'] = mappings
            return self._save_mappings(data)
        
        except Exception as e:
            logger.error(f"Error creating sketch mapping: {e}")
            return False
    
    def get_sketch_for_case(self, case_id: str) -> Optional[Dict]:
        """
        Get sketch information for a case.
        
        Args:
            case_id: Case ID
        
        Returns:
            Mapping dictionary or None if not found.
        """
        data = self._load_mappings()
        mappings = data.get('mappings', [])
        
        for mapping in mappings:
            if mapping.get('case_id') == case_id:
                return mapping
        
        return None
    
    def get_sketch_id_for_case(self, case_id: str) -> Optional[str]:
        """
        Get sketch ID for a case.
        
        Args:
            case_id: Case ID
        
        Returns:
            Sketch ID or None if not found.
        """
        mapping = self.get_sketch_for_case(case_id)
        return mapping.get('sketch_id') if mapping else None
    
    def sync_case_to_sketch(self, case_id: str, case: Dict, findings: List[Dict],
                           timesketch_service, timeline_service) -> bool:
        """
        Sync a case and its findings to Timesketch.
        
        Args:
            case_id: Case ID
            case: Case dictionary
            findings: List of related findings
            timesketch_service: TimesketchService instance (can be None)
            timeline_service: TimelineService instance
        
        Returns:
            True if successful, False otherwise.
        """
        if not timesketch_service:
            logger.warning(f"Cannot sync case {case_id}: Timesketch service not available")
            return False
        
        try:
            # Get or create sketch
            mapping = self.get_sketch_for_case(case_id)
            
            if mapping:
                sketch_id = mapping.get('sketch_id')
            else:
                # Create new sketch
                sketch_name = f"Case: {case.get('title', case_id)}"
                sketch_description = case.get('description', '')
                sketch_id = timesketch_service.create_sketch(sketch_name, sketch_description)
                
                if not sketch_id:
                    logger.error(f"Failed to create sketch for case {case_id}")
                    return False
                
                # Create mapping
                self.create_sketch_for_case(case_id, sketch_id, sketch_name, timesketch_service)
            
            # Convert case and findings to timeline events
            events = timeline_service.case_to_timeline_events(case, findings)
            
            if not events:
                logger.warning(f"No events to sync for case {case_id}")
                return True  # No events is not an error
            
            # Add timeline to sketch
            timeline_name = f"Case Timeline - {case.get('title', case_id)}"
            timeline_id = timesketch_service.add_timeline(sketch_id, timeline_name, events)
            
            if timeline_id:
                # Update sync status
                mapping = self.get_sketch_for_case(case_id)
                if mapping:
                    data = self._load_mappings()
                    mappings = data.get('mappings', [])
                    for m in mappings:
                        if m.get('case_id') == case_id:
                            m['last_sync'] = datetime.now().isoformat()
                            m['sync_status'] = 'synced'
                            m['timeline_id'] = timeline_id
                            break
                    data['mappings'] = mappings
                    self._save_mappings(data)
                
                logger.info(f"Synced case {case_id} to sketch {sketch_id}")
                return True
            else:
                logger.error(f"Failed to add timeline to sketch {sketch_id}")
                return False
        
        except Exception as e:
            logger.error(f"Error syncing case to sketch: {e}")
            return False
    
    def update_sketch_from_case(self, case: Dict, sketch_id: str, 
                               timesketch_service) -> bool:
        """
        Update a sketch from case data.
        
        Args:
            case: Case dictionary
            sketch_id: Sketch ID
            timesketch_service: TimesketchService instance
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Update sketch metadata
            sketch = timesketch_service.get_sketch(sketch_id)
            if not sketch:
                return False
            
            # Update sketch name and description if changed
            new_name = f"Case: {case.get('title', 'Untitled')}"
            new_description = case.get('description', '')
            
            # Note: Timesketch API may require separate update endpoint
            # This is a placeholder - actual implementation depends on API
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating sketch from case: {e}")
            return False
    
    def link_findings_to_sketch(self, finding_ids: List[str], sketch_id: str,
                                timesketch_service, timeline_service,
                                data_service) -> bool:
        """
        Link findings to an existing sketch.
        
        Args:
            finding_ids: List of finding IDs
            sketch_id: Sketch ID
            timesketch_service: TimesketchService instance
            timeline_service: TimelineService instance
            data_service: DataService instance
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Get findings
            findings = []
            for finding_id in finding_ids:
                finding = data_service.get_finding(finding_id)
                if finding:
                    findings.append(finding)
            
            if not findings:
                return False
            
            # Convert to events
            events = timeline_service.findings_to_timeline_events(findings)
            
            # Add to sketch
            timeline_name = f"Additional Findings - {datetime.now().strftime('%Y-%m-%d')}"
            timeline_id = timesketch_service.add_timeline(sketch_id, timeline_name, events)
            
            return timeline_id is not None
        
        except Exception as e:
            logger.error(f"Error linking findings to sketch: {e}")
            return False
    
    def get_sketch_metadata(self, sketch_id: str, timesketch_service) -> Optional[Dict]:
        """
        Get metadata for a sketch.
        
        Args:
            sketch_id: Sketch ID
            timesketch_service: TimesketchService instance
        
        Returns:
            Sketch metadata dictionary or None.
        """
        return timesketch_service.get_sketch(sketch_id)
    
    def list_all_mappings(self) -> List[Dict]:
        """
        List all case-sketch mappings.
        
        Returns:
            List of mapping dictionaries.
        """
        data = self._load_mappings()
        return data.get('mappings', [])
    
    def update_sync_status(self, case_id: str, status: str, error: Optional[str] = None) -> bool:
        """
        Update sync status for a case.
        
        Args:
            case_id: Case ID
            status: Sync status (synced, pending, error)
            error: Optional error message
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            data = self._load_mappings()
            mappings = data.get('mappings', [])
            
            for mapping in mappings:
                if mapping.get('case_id') == case_id:
                    mapping['sync_status'] = status
                    mapping['last_sync'] = datetime.now().isoformat()
                    if error:
                        mapping['last_error'] = error
                    break
            
            data['mappings'] = mappings
            return self._save_mappings(data)
        
        except Exception as e:
            logger.error(f"Error updating sync status: {e}")
            return False
    
    def archive_sketch(self, sketch_id: str) -> bool:
        """
        Archive a sketch mapping (mark as archived, don't delete).
        
        Args:
            sketch_id: Sketch ID
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            data = self._load_mappings()
            mappings = data.get('mappings', [])
            
            for mapping in mappings:
                if mapping.get('sketch_id') == sketch_id:
                    mapping['archived'] = True
                    mapping['archived_at'] = datetime.now().isoformat()
                    break
            
            data['mappings'] = mappings
            return self._save_mappings(data)
        
        except Exception as e:
            logger.error(f"Error archiving sketch: {e}")
            return False

