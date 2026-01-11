"""Background auto-sync service for Timesketch integration."""

import logging
import threading
import time
from typing import Optional, Dict, List
from datetime import datetime, timezone
from pathlib import Path
import json

from services.sketch_manager import SketchManager
from services.timesketch_service import TimesketchService
from services.timeline_service import TimelineService
from services.data_service import DataService
from ui.timesketch_config import TimesketchConfigDialog

logger = logging.getLogger(__name__)


class AutoSyncService:
    """Background service for automatically syncing cases to Timesketch."""
    
    def __init__(self):
        self.sketch_manager = SketchManager()
        self.data_service = DataService()
        self.timeline_service = TimelineService()
        self.timesketch_service: Optional[TimesketchService] = None
        
        self._sync_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._sync_interval = 300  # Default: 5 minutes
        self._is_running = False
        self._last_sync_time: Optional[datetime] = None
        self._sync_stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'last_error': None
        }
    
    def start(self, sync_interval: int = 300):
        """
        Start the auto-sync service.
        
        Args:
            sync_interval: Sync interval in seconds (default: 300)
        """
        if self._is_running:
            logger.warning("Auto-sync service is already running")
            return
        
        self._sync_interval = sync_interval
        self._stop_event.clear()
        self._is_running = True
        
        # Load Timesketch service
        self.timesketch_service = TimesketchConfigDialog.load_service()
        if not self.timesketch_service:
            logger.warning("Timesketch not configured, auto-sync cannot start")
            self._is_running = False
            return
        
        # Start sync thread
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
        
        logger.info(f"Auto-sync service started (interval: {sync_interval}s)")
    
    def stop(self):
        """Stop the auto-sync service."""
        if not self._is_running:
            return
        
        self._is_running = False
        self._stop_event.set()
        
        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5)
        
        logger.info("Auto-sync service stopped")
    
    def _sync_loop(self):
        """Main sync loop running in background thread."""
        while self._is_running and not self._stop_event.is_set():
            try:
                # Check if auto-sync is enabled in config
                config = self._load_config()
                if not config.get('auto_sync', False):
                    logger.debug("Auto-sync disabled in configuration")
                    time.sleep(60)  # Check again in 1 minute
                    continue
                
                # Perform sync
                self._perform_sync()
                
                # Wait for next sync interval
                self._stop_event.wait(self._sync_interval)
            
            except Exception as e:
                logger.error(f"Error in auto-sync loop: {e}")
                self._sync_stats['failed_syncs'] += 1
                self._sync_stats['last_error'] = str(e)
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _perform_sync(self):
        """Perform synchronization of all cases."""
        logger.info("Starting auto-sync cycle")
        
        if not self.timesketch_service:
            # Try to reload service
            self.timesketch_service = TimesketchConfigDialog.load_service()
            if not self.timesketch_service:
                logger.warning("Timesketch service not available - skipping sync")
                return
        
        # Get all cases
        cases = self.data_service.get_cases()
        mappings = self.sketch_manager.list_all_mappings()
        
        # Create mapping lookup
        mapping_lookup = {m.get('case_id'): m for m in mappings}
        
        synced_count = 0
        failed_count = 0
        
        for case in cases:
            case_id = case.get('case_id')
            if not case_id:
                continue
            
            # Check if case should be synced
            mapping = mapping_lookup.get(case_id)
            if mapping and not mapping.get('auto_sync', True):
                continue  # Skip cases with auto-sync disabled
            
            try:
                # Get findings for case
                finding_ids = case.get('finding_ids', [])
                findings = []
                for finding_id in finding_ids:
                    finding = self.data_service.get_finding(finding_id)
                    if finding:
                        findings.append(finding)
                
                # Check if case was updated since last sync
                if mapping:
                    last_sync_str = mapping.get('last_sync')
                    if last_sync_str:
                        try:
                            last_sync = datetime.fromisoformat(last_sync_str.replace('Z', '+00:00'))
                            case_updated = datetime.fromisoformat(
                                case.get('updated_at', case.get('created_at', '')).replace('Z', '+00:00')
                            )
                            
                            # Only sync if case was updated after last sync
                            if case_updated <= last_sync:
                                continue
                        except Exception:
                            pass  # Sync anyway if date parsing fails
                
                # Sync case
                success = self.sketch_manager.sync_case_to_sketch(
                    case_id,
                    case,
                    findings,
                    self.timesketch_service,
                    self.timeline_service
                )
                
                if success:
                    synced_count += 1
                else:
                    failed_count += 1
                    self.sketch_manager.update_sync_status(case_id, 'error', 'Auto-sync failed')
            
            except Exception as e:
                logger.error(f"Error syncing case {case_id}: {e}")
                failed_count += 1
                self.sketch_manager.update_sync_status(case_id, 'error', str(e))
        
        # Update stats
        self._sync_stats['total_syncs'] += 1
        self._sync_stats['successful_syncs'] += synced_count
        self._sync_stats['failed_syncs'] += failed_count
        self._last_sync_time = datetime.now(timezone.utc)
        
        logger.info(f"Auto-sync completed: {synced_count} synced, {failed_count} failed")
    
    def _load_config(self) -> Dict:
        """Load Timesketch configuration."""
        config_file = TimesketchConfigDialog.CONFIG_FILE
        if not config_file.exists():
            return {'auto_sync': False}
        
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {'auto_sync': False}
    
    def get_status(self) -> Dict:
        """
        Get auto-sync service status.
        
        Returns:
            Dictionary with status information.
        """
        return {
            'is_running': self._is_running,
            'sync_interval': self._sync_interval,
            'last_sync_time': self._last_sync_time.isoformat() if self._last_sync_time else None,
            'stats': self._sync_stats.copy()
        }
    
    def sync_now(self) -> Dict:
        """
        Trigger an immediate sync (synchronous).
        
        Returns:
            Dictionary with sync results.
        """
        if not self.timesketch_service:
            self.timesketch_service = TimesketchConfigDialog.load_service()
            if not self.timesketch_service:
                return {
                    'success': False,
                    'error': 'Timesketch not configured'
                }
        
        try:
            self._perform_sync()
            return {
                'success': True,
                'stats': self._sync_stats.copy()
            }
        except Exception as e:
            logger.error(f"Error in manual sync: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
_auto_sync_service: Optional[AutoSyncService] = None


def get_auto_sync_service() -> AutoSyncService:
    """Get or create the global auto-sync service instance."""
    global _auto_sync_service
    if _auto_sync_service is None:
        _auto_sync_service = AutoSyncService()
    return _auto_sync_service

