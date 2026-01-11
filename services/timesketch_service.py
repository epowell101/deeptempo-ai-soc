"""Timesketch API service for timeline analysis integration."""

import logging
import requests
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class TimesketchService:
    """Service for interacting with Timesketch API."""
    
    def __init__(self, server_url: str, username: Optional[str] = None, 
                 password: Optional[str] = None, api_token: Optional[str] = None):
        """
        Initialize Timesketch service.
        
        Args:
            server_url: Timesketch server URL (e.g., "https://timesketch.example.com")
            username: Username for authentication (if using password auth)
            password: Password for authentication
            api_token: API token for authentication (alternative to username/password)
        """
        self.server_url = server_url.rstrip('/')
        self.api_base = f"{self.server_url}/api/v1"
        self.username = username
        self.password = password
        self.api_token = api_token
        self.session_token: Optional[str] = None
        self.session = requests.Session()
        self.session.verify = True  # SSL verification
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def authenticate(self) -> bool:
        """
        Authenticate with Timesketch server.
        
        Returns:
            True if authentication successful, False otherwise.
        """
        try:
            if self.api_token:
                # Use API token authentication
                self.session.headers['Authorization'] = f'Bearer {self.api_token}'
                # Test authentication
                response = self.session.get(f"{self.api_base}/sketches/")
                if response.status_code == 200:
                    logger.info("Timesketch authentication successful (API token)")
                    return True
            elif self.username and self.password:
                # Use username/password authentication
                auth_data = {
                    'username': self.username,
                    'password': self.password
                }
                response = self.session.post(
                    f"{self.server_url}/login/",
                    json=auth_data
                )
                if response.status_code == 200:
                    # Extract session token from cookies or response
                    if 'session' in response.cookies:
                        self.session_token = response.cookies['session']
                        self.session.cookies.set('session', self.session_token)
                    logger.info("Timesketch authentication successful (username/password)")
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status_code}")
                    return False
            else:
                logger.error("No authentication credentials provided")
                return False
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during authentication: {e}")
            return False
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test connection to Timesketch server.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.authenticate():
                return False, "Authentication failed"
            
            response = self.session.get(f"{self.api_base}/sketches/", params={'limit': 1})
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"Connection failed: HTTP {response.status_code}"
        
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
    
    def create_sketch(self, name: str, description: str = "") -> Optional[str]:
        """
        Create a new sketch in Timesketch.
        
        Args:
            name: Sketch name
            description: Sketch description
        
        Returns:
            Sketch ID if successful, None otherwise.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return None
            
            data = {
                'name': name,
                'description': description
            }
            
            response = self.session.post(f"{self.api_base}/sketches/", json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                sketch_id = result.get('objects', [{}])[0].get('id') if 'objects' in result else result.get('id')
                logger.info(f"Created sketch: {sketch_id}")
                return str(sketch_id)
            else:
                logger.error(f"Failed to create sketch: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Error creating sketch: {e}")
            return None
    
    def get_sketch(self, sketch_id: str) -> Optional[Dict]:
        """
        Get sketch details.
        
        Args:
            sketch_id: Sketch ID
        
        Returns:
            Sketch dictionary or None if error.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return None
            
            response = self.session.get(f"{self.api_base}/sketches/{sketch_id}/")
            
            if response.status_code == 200:
                result = response.json()
                return result.get('objects', [{}])[0] if 'objects' in result else result
            else:
                logger.error(f"Failed to get sketch: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"Error getting sketch: {e}")
            return None
    
    def list_sketches(self, limit: int = 100) -> List[Dict]:
        """
        List all sketches.
        
        Args:
            limit: Maximum number of sketches to return
        
        Returns:
            List of sketch dictionaries.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return []
            
            response = self.session.get(f"{self.api_base}/sketches/", params={'limit': limit})
            
            if response.status_code == 200:
                result = response.json()
                sketches = result.get('objects', [])
                return sketches
            else:
                logger.error(f"Failed to list sketches: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error listing sketches: {e}")
            return []
    
    def add_timeline(self, sketch_id: str, timeline_name: str, events: List[Dict]) -> Optional[str]:
        """
        Add a timeline with events to a sketch.
        
        Args:
            sketch_id: Sketch ID
            timeline_name: Name for the timeline
            events: List of event dictionaries
        
        Returns:
            Timeline ID if successful, None otherwise.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return None
            
            # Create timeline
            timeline_data = {
                'name': timeline_name,
                'description': f'Timeline from DeepTempo: {timeline_name}'
            }
            
            response = self.session.post(
                f"{self.api_base}/sketches/{sketch_id}/timelines/",
                json=timeline_data
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Failed to create timeline: {response.status_code}")
                return None
            
            result = response.json()
            timeline_id = result.get('objects', [{}])[0].get('id') if 'objects' in result else result.get('id')
            
            if not timeline_id:
                logger.error("No timeline ID in response")
                return None
            
            # Import events to timeline
            # Timesketch typically uses CSV or JSON format for import
            # We'll use the import endpoint
            import_data = {
                'timeline_id': timeline_id,
                'events': events
            }
            
            import_response = self.session.post(
                f"{self.api_base}/sketches/{sketch_id}/timelines/{timeline_id}/import/",
                json=import_data
            )
            
            if import_response.status_code in [200, 201]:
                logger.info(f"Added {len(events)} events to timeline {timeline_id}")
                return str(timeline_id)
            else:
                logger.error(f"Failed to import events: {import_response.status_code}")
                return str(timeline_id)  # Timeline created but events not imported
        
        except Exception as e:
            logger.error(f"Error adding timeline: {e}")
            return None
    
    def search_sketch(self, sketch_id: str, query: str, limit: int = 100) -> List[Dict]:
        """
        Search events in a sketch.
        
        Args:
            sketch_id: Sketch ID
            query: Search query string
            limit: Maximum number of results
        
        Returns:
            List of matching events.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return []
            
            search_data = {
                'query': query,
                'limit': limit
            }
            
            response = self.session.post(
                f"{self.api_base}/sketches/{sketch_id}/explore/",
                json=search_data
            )
            
            if response.status_code == 200:
                result = response.json()
                events = result.get('objects', [])
                return events
            else:
                logger.error(f"Search failed: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error searching sketch: {e}")
            return []
    
    def run_analyzer(self, sketch_id: str, analyzer_name: str, timeline_id: Optional[str] = None) -> Optional[Dict]:
        """
        Run an analyzer on a sketch or timeline.
        
        Args:
            sketch_id: Sketch ID
            analyzer_name: Name of analyzer to run
            timeline_id: Optional timeline ID (if None, runs on all timelines)
        
        Returns:
            Analyzer result dictionary or None if error.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return None
            
            analyzer_data = {
                'analyzer_name': analyzer_name
            }
            
            if timeline_id:
                analyzer_data['timeline_id'] = timeline_id
            
            response = self.session.post(
                f"{self.api_base}/sketches/{sketch_id}/analyze/",
                json=analyzer_data
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return result
            else:
                logger.error(f"Analyzer failed: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"Error running analyzer: {e}")
            return None
    
    def get_timeline_events(self, sketch_id: str, timeline_id: str, 
                           filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """
        Get events from a timeline.
        
        Args:
            sketch_id: Sketch ID
            timeline_id: Timeline ID
            filters: Optional filters (time range, etc.)
            limit: Maximum number of events
        
        Returns:
            List of events.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return []
            
            params = {'limit': limit}
            if filters:
                params.update(filters)
            
            response = self.session.get(
                f"{self.api_base}/sketches/{sketch_id}/timelines/{timeline_id}/events/",
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                events = result.get('objects', [])
                return events
            else:
                logger.error(f"Failed to get events: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting timeline events: {e}")
            return []
    
    def add_comment(self, sketch_id: str, event_id: str, comment: str) -> bool:
        """
        Add a comment to an event.
        
        Args:
            sketch_id: Sketch ID
            event_id: Event ID
            comment: Comment text
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return False
            
            comment_data = {
                'comment': comment
            }
            
            response = self.session.post(
                f"{self.api_base}/sketches/{sketch_id}/events/{event_id}/comments/",
                json=comment_data
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Added comment to event {event_id}")
                return True
            else:
                logger.error(f"Failed to add comment: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return False
    
    def add_label(self, sketch_id: str, event_id: str, label: str) -> bool:
        """
        Add a label to an event.
        
        Args:
            sketch_id: Sketch ID
            event_id: Event ID
            label: Label name
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return False
            
            label_data = {
                'label': label
            }
            
            response = self.session.post(
                f"{self.api_base}/sketches/{sketch_id}/events/{event_id}/labels/",
                json=label_data
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Added label {label} to event {event_id}")
                return True
            else:
                logger.error(f"Failed to add label: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Error adding label: {e}")
            return False
    
    def get_sketch_analyses(self, sketch_id: str) -> List[Dict]:
        """
        Get analysis results for a sketch.
        
        Args:
            sketch_id: Sketch ID
        
        Returns:
            List of analysis results.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return []
            
            response = self.session.get(
                f"{self.api_base}/sketches/{sketch_id}/analyses/"
            )
            
            if response.status_code == 200:
                result = response.json()
                analyses = result.get('objects', [])
                return analyses
            else:
                logger.error(f"Failed to get analyses: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting analyses: {e}")
            return []
    
    def get_event_comments(self, sketch_id: str, event_id: str) -> List[Dict]:
        """
        Get comments for an event.
        
        Args:
            sketch_id: Sketch ID
            event_id: Event ID
        
        Returns:
            List of comment dictionaries.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return []
            
            response = self.session.get(
                f"{self.api_base}/sketches/{sketch_id}/events/{event_id}/comments/"
            )
            
            if response.status_code == 200:
                result = response.json()
                comments = result.get('objects', [])
                return comments
            else:
                logger.error(f"Failed to get comments: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            return []
    
    def get_sketch_collaborators(self, sketch_id: str) -> List[Dict]:
        """
        Get collaborators for a sketch.
        
        Args:
            sketch_id: Sketch ID
        
        Returns:
            List of collaborator dictionaries.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return []
            
            response = self.session.get(
                f"{self.api_base}/sketches/{sketch_id}/collaborators/"
            )
            
            if response.status_code == 200:
                result = response.json()
                collaborators = result.get('objects', [])
                return collaborators
            else:
                logger.error(f"Failed to get collaborators: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting collaborators: {e}")
            return []
    
    def get_sketch_activity(self, sketch_id: str, limit: int = 50) -> List[Dict]:
        """
        Get activity feed for a sketch.
        
        Args:
            sketch_id: Sketch ID
            limit: Maximum number of activities
        
        Returns:
            List of activity dictionaries.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return []
            
            response = self.session.get(
                f"{self.api_base}/sketches/{sketch_id}/activity/",
                params={'limit': limit}
            )
            
            if response.status_code == 200:
                result = response.json()
                activities = result.get('objects', [])
                return activities
            else:
                logger.error(f"Failed to get activity: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting activity: {e}")
            return []
    
    def share_sketch(self, sketch_id: str, username: str, permission: str = 'read') -> bool:
        """
        Share a sketch with a user.
        
        Args:
            sketch_id: Sketch ID
            username: Username to share with
            permission: Permission level ('read', 'write', 'delete')
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            if not self.session_token and not self.api_token:
                if not self.authenticate():
                    return False
            
            share_data = {
                'username': username,
                'permission': permission
            }
            
            response = self.session.post(
                f"{self.api_base}/sketches/{sketch_id}/collaborators/",
                json=share_data
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Shared sketch {sketch_id} with {username}")
                return True
            else:
                logger.error(f"Failed to share sketch: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Error sharing sketch: {e}")
            return False

