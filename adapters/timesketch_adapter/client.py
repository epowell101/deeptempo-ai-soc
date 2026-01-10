"""
Timesketch Adapter for DeepTempo AI SOC

This adapter provides integration with Timesketch for timeline visualization
of security findings from DeepTempo LogLM.
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Try to import the official Timesketch API client
try:
    from timesketch_api_client import config as ts_config
    from timesketch_api_client import client as ts_client
    TIMESKETCH_AVAILABLE = True
except ImportError:
    TIMESKETCH_AVAILABLE = False
    logger.warning("timesketch-api-client not installed. Install with: pip install timesketch-api-client")


class TimesketchAdapter:
    """
    Adapter for integrating DeepTempo findings with Timesketch.
    
    Supports both direct API connection and mock mode for demos.
    """
    
    def __init__(
        self,
        host_uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        mock_mode: bool = False
    ):
        """
        Initialize the Timesketch adapter.
        
        Args:
            host_uri: Timesketch server URL (e.g., http://localhost:5000)
            username: Timesketch username
            password: Timesketch password
            mock_mode: If True, operate without actual Timesketch connection
        """
        self.host_uri = host_uri or os.environ.get("TIMESKETCH_HOST", "http://localhost:5000")
        self.username = username or os.environ.get("TIMESKETCH_USER", "dev")
        self.password = password or os.environ.get("TIMESKETCH_PASSWORD", "dev")
        self.mock_mode = mock_mode
        self._client = None
        self._connected = False
        
        # Mock data storage for demo mode
        self._mock_sketches: Dict[int, Dict] = {}
        self._mock_timelines: Dict[int, List[Dict]] = {}
        self._mock_sketch_counter = 1
        self._mock_timeline_counter = 1
        
    def connect(self) -> bool:
        """
        Establish connection to Timesketch server.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.mock_mode:
            logger.info("Running in mock mode - no actual Timesketch connection")
            self._connected = True
            return True
            
        if not TIMESKETCH_AVAILABLE:
            logger.error("timesketch-api-client not installed")
            return False
            
        try:
            self._client = ts_client.TimesketchApi(
                host_uri=self.host_uri,
                username=self.username,
                password=self.password,
                auth_mode="userpass"
            )
            self._connected = True
            logger.info(f"Connected to Timesketch at {self.host_uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Timesketch: {e}")
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if adapter is connected to Timesketch."""
        return self._connected
    
    def create_sketch(self, name: str, description: str = "") -> Optional[Dict]:
        """
        Create a new sketch in Timesketch.
        
        Args:
            name: Name of the sketch
            description: Optional description
            
        Returns:
            Sketch information dict or None if failed
        """
        if self.mock_mode:
            sketch_id = self._mock_sketch_counter
            self._mock_sketch_counter += 1
            sketch = {
                "id": sketch_id,
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "url": f"{self.host_uri}/sketch/{sketch_id}/"
            }
            self._mock_sketches[sketch_id] = sketch
            self._mock_timelines[sketch_id] = []
            logger.info(f"Created mock sketch: {name} (ID: {sketch_id})")
            return sketch
            
        if not self._connected or not self._client:
            logger.error("Not connected to Timesketch")
            return None
            
        try:
            sketch = self._client.create_sketch(name=name, description=description)
            return {
                "id": sketch.id,
                "name": sketch.name,
                "description": sketch.description,
                "url": f"{self.host_uri}/sketch/{sketch.id}/"
            }
        except Exception as e:
            logger.error(f"Failed to create sketch: {e}")
            return None
    
    def list_sketches(self) -> List[Dict]:
        """
        List all available sketches.
        
        Returns:
            List of sketch information dicts
        """
        if self.mock_mode:
            return list(self._mock_sketches.values())
            
        if not self._connected or not self._client:
            logger.error("Not connected to Timesketch")
            return []
            
        try:
            sketches = self._client.list_sketches()
            return [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "url": f"{self.host_uri}/sketch/{s.id}/"
                }
                for s in sketches
            ]
        except Exception as e:
            logger.error(f"Failed to list sketches: {e}")
            return []
    
    def get_sketch(self, sketch_id: int) -> Optional[Dict]:
        """
        Get a specific sketch by ID.
        
        Args:
            sketch_id: The sketch ID
            
        Returns:
            Sketch information dict or None if not found
        """
        if self.mock_mode:
            return self._mock_sketches.get(sketch_id)
            
        if not self._connected or not self._client:
            logger.error("Not connected to Timesketch")
            return None
            
        try:
            sketch = self._client.get_sketch(sketch_id)
            return {
                "id": sketch.id,
                "name": sketch.name,
                "description": sketch.description,
                "url": f"{self.host_uri}/sketch/{sketch.id}/"
            }
        except Exception as e:
            logger.error(f"Failed to get sketch {sketch_id}: {e}")
            return None
    
    def findings_to_timeline_events(self, findings: List[Dict]) -> List[Dict]:
        """
        Convert DeepTempo findings to Timesketch timeline event format.
        
        Args:
            findings: List of DeepTempo finding dicts
            
        Returns:
            List of Timesketch-compatible event dicts
        """
        events = []
        for finding in findings:
            # Extract timestamp from finding or use current time
            timestamp = finding.get("timestamp", datetime.now().isoformat())
            
            # Build message from finding details
            entity = finding.get("entity_context", {})
            mitre = finding.get("mitre_predictions", {})
            top_technique = max(mitre.items(), key=lambda x: x[1])[0] if mitre else "Unknown"
            
            message = (
                f"DeepTempo Finding: {finding.get('finding_id', 'unknown')} | "
                f"Score: {finding.get('anomaly_score', 0):.2f} | "
                f"Technique: {top_technique} | "
                f"Source: {finding.get('data_source', 'unknown')}"
            )
            
            # Create Timesketch event
            event = {
                "message": message,
                "datetime": timestamp,
                "timestamp_desc": "DeepTempo Detection",
                "finding_id": finding.get("finding_id", ""),
                "anomaly_score": finding.get("anomaly_score", 0),
                "data_source": finding.get("data_source", ""),
                "severity": finding.get("severity", "medium"),
                "cluster_id": finding.get("cluster_id", ""),
                "src_ip": entity.get("src_ip", ""),
                "dst_ip": entity.get("dst_ip", ""),
                "hostname": entity.get("hostname", ""),
                "user": entity.get("user", ""),
                "mitre_techniques": ",".join(mitre.keys()) if mitre else "",
                "top_mitre_technique": top_technique,
                "top_mitre_confidence": mitre.get(top_technique, 0) if mitre else 0
            }
            events.append(event)
            
        return events
    
    def upload_findings_as_timeline(
        self,
        sketch_id: int,
        findings: List[Dict],
        timeline_name: str = "DeepTempo Findings"
    ) -> Optional[Dict]:
        """
        Upload DeepTempo findings as a timeline to a sketch.
        
        Args:
            sketch_id: Target sketch ID
            findings: List of DeepTempo finding dicts
            timeline_name: Name for the timeline
            
        Returns:
            Timeline information dict or None if failed
        """
        events = self.findings_to_timeline_events(findings)
        
        if self.mock_mode:
            timeline_id = self._mock_timeline_counter
            self._mock_timeline_counter += 1
            timeline = {
                "id": timeline_id,
                "name": timeline_name,
                "sketch_id": sketch_id,
                "event_count": len(events),
                "events": events,
                "created_at": datetime.now().isoformat()
            }
            if sketch_id in self._mock_timelines:
                self._mock_timelines[sketch_id].append(timeline)
            logger.info(f"Uploaded {len(events)} events to mock timeline: {timeline_name}")
            return timeline
            
        if not self._connected or not self._client:
            logger.error("Not connected to Timesketch")
            return None
            
        try:
            sketch = self._client.get_sketch(sketch_id)
            
            # Convert events to JSONL format for upload
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                for event in events:
                    f.write(json.dumps(event) + '\n')
                temp_path = f.name
            
            # Upload using importer
            from timesketch_import_client import importer
            with importer.ImportStreamer() as streamer:
                streamer.set_sketch(sketch)
                streamer.set_timeline_name(timeline_name)
                
                for event in events:
                    streamer.add_dict(event)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            logger.info(f"Uploaded {len(events)} events to timeline: {timeline_name}")
            return {
                "name": timeline_name,
                "sketch_id": sketch_id,
                "event_count": len(events)
            }
        except Exception as e:
            logger.error(f"Failed to upload timeline: {e}")
            return None
    
    def search_events(
        self,
        sketch_id: int,
        query: str,
        time_start: Optional[str] = None,
        time_end: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Search for events in a sketch.
        
        Args:
            sketch_id: Sketch to search in
            query: Search query string
            time_start: Optional start time filter (ISO format)
            time_end: Optional end time filter (ISO format)
            max_results: Maximum number of results to return
            
        Returns:
            List of matching events
        """
        if self.mock_mode:
            # Simple mock search - filter by query in message
            results = []
            if sketch_id in self._mock_timelines:
                for timeline in self._mock_timelines[sketch_id]:
                    for event in timeline.get("events", []):
                        if query.lower() in event.get("message", "").lower():
                            results.append(event)
                            if len(results) >= max_results:
                                break
            return results[:max_results]
            
        if not self._connected or not self._client:
            logger.error("Not connected to Timesketch")
            return []
            
        try:
            sketch = self._client.get_sketch(sketch_id)
            search_obj = sketch.explore(
                query_string=query,
                return_fields="message,datetime,finding_id,anomaly_score,mitre_techniques",
                max_entries=max_results
            )
            
            results = []
            for event in search_obj.get("objects", []):
                results.append(event.get("_source", {}))
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_sketch_url(self, sketch_id: int) -> str:
        """
        Get the web URL for a sketch.
        
        Args:
            sketch_id: The sketch ID
            
        Returns:
            URL string to view the sketch in Timesketch UI
        """
        return f"{self.host_uri}/sketch/{sketch_id}/"
    
    def get_timeline_url(self, sketch_id: int, timeline_id: Optional[int] = None) -> str:
        """
        Get the web URL for viewing a timeline.
        
        Args:
            sketch_id: The sketch ID
            timeline_id: Optional specific timeline ID
            
        Returns:
            URL string to view the timeline in Timesketch UI
        """
        base_url = f"{self.host_uri}/sketch/{sketch_id}/explore"
        if timeline_id:
            return f"{base_url}?timeline={timeline_id}"
        return base_url
