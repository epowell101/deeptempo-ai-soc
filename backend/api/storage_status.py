"""
Storage backend status API endpoints.

Provides information about the current data storage backend (PostgreSQL or JSON).
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def get_storage_status():
    """
    Get information about the current storage backend.
    
    Returns:
        Dictionary with storage backend information
    """
    try:
        from services.database_data_service import DatabaseDataService
        
        # Create a test instance to check backend
        test_service = DatabaseDataService(use_database=True, auto_fallback=True)
        backend_info = test_service.get_backend_info()
        
        return {
            'backend': backend_info['backend'],
            'database_available': backend_info['database_available'],
            'json_available': backend_info['json_available'],
            'description': _get_backend_description(backend_info['backend']),
            'recommendations': _get_recommendations(backend_info)
        }
    
    except Exception as e:
        logger.error(f"Error getting storage status: {e}")
        return {
            'backend': 'unknown',
            'database_available': False,
            'json_available': True,
            'error': str(e),
            'description': 'Unable to determine storage backend'
        }


def _get_backend_description(backend: str) -> str:
    """Get human-readable description of the backend."""
    descriptions = {
        'postgresql': 'Using PostgreSQL database for production-grade data storage',
        'json': 'Using JSON file storage (development/fallback mode)',
        'unknown': 'Storage backend status unknown'
    }
    return descriptions.get(backend, 'Unknown storage backend')


def _get_recommendations(backend_info: dict) -> list:
    """Get recommendations based on current backend status."""
    recommendations = []
    
    backend = backend_info.get('backend')
    database_available = backend_info.get('database_available', False)
    
    if backend == 'json' and not database_available:
        recommendations.append({
            'title': 'Enable PostgreSQL for Production',
            'description': 'Currently using JSON file storage. For better performance and reliability, enable PostgreSQL.',
            'action': 'Start database with: ./start_database.sh',
            'priority': 'medium'
        })
    
    if backend == 'postgresql':
        recommendations.append({
            'title': 'Database Running',
            'description': 'PostgreSQL is active and ready for production use.',
            'action': 'Set up automated backups for data protection',
            'priority': 'low'
        })
    
    return recommendations


@router.get("/health")
async def check_storage_health():
    """
    Perform health check on the storage backend.
    
    Returns:
        Health status of the storage backend
    """
    try:
        from services.database_data_service import DatabaseDataService
        
        # Try to initialize and get status
        service = DatabaseDataService(use_database=True, auto_fallback=True)
        is_healthy = True
        
        # Test basic operations
        try:
            findings = service.get_findings()
            cases = service.get_cases()
            
            return {
                'healthy': is_healthy,
                'backend': 'postgresql' if service.is_using_database() else 'json',
                'findings_count': len(findings),
                'cases_count': len(cases),
                'message': 'Storage backend is functioning normally'
            }
        
        except Exception as e:
            return {
                'healthy': False,
                'backend': 'unknown',
                'error': str(e),
                'message': 'Storage backend health check failed'
            }
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            'healthy': False,
            'backend': 'unknown',
            'error': str(e),
            'message': 'Unable to perform health check'
        }


@router.post("/reconnect")
async def reconnect_database():
    """
    Attempt to reconnect to PostgreSQL database without restarting the application.
    
    This is useful when:
    - PostgreSQL was started after the application
    - Database configuration was changed
    - Connection was lost and needs to be re-established
    
    Returns:
        Status of the reconnection attempt
    """
    try:
        from database.connection import get_db_manager
        
        logger.info("Attempting to reconnect to PostgreSQL database...")
        
        # Get the database manager
        db_manager = get_db_manager()
        
        # Close existing connections
        db_manager.close()
        
        # Reinitialize the database connection
        db_manager.initialize(echo=False)
        db_manager.create_tables()
        
        # Test the connection
        if db_manager.health_check():
            logger.info("✓ Successfully reconnected to PostgreSQL")
            
            return {
                'success': True,
                'backend': 'postgresql',
                'message': 'Successfully reconnected to PostgreSQL database',
                'database_available': True,
                'connection_info': {
                    'host': db_manager.config.host,
                    'port': db_manager.config.port,
                    'database': db_manager.config.database
                }
            }
        else:
            logger.warning("Database health check failed after reconnection attempt")
            return {
                'success': False,
                'backend': 'json',
                'message': 'Database reconnection failed. Health check did not pass.',
                'database_available': False,
                'recommendation': 'Ensure PostgreSQL is running: ./start_database.sh'
            }
    
    except Exception as e:
        logger.error(f"Error reconnecting to database: {e}")
        return {
            'success': False,
            'backend': 'json',
            'message': f'Failed to reconnect: {str(e)}',
            'database_available': False,
            'recommendation': 'Check PostgreSQL logs and ensure it is running'
        }


@router.post("/switch-backend")
async def switch_backend(backend: str):
    """
    Attempt to switch storage backend (requires restart).
    
    Args:
        backend: Target backend ('database' or 'json')
    
    Returns:
        Status of the switch request
    """
    if backend not in ['database', 'json']:
        return {
            'success': False,
            'message': 'Invalid backend. Must be "database" or "json"'
        }
    
    import os
    from pathlib import Path
    
    try:
        # Update .env file
        env_file = Path('.env')
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            updated = False
            with open(env_file, 'w') as f:
                for line in lines:
                    if line.startswith('DATA_BACKEND='):
                        f.write(f'DATA_BACKEND={backend}\n')
                        updated = True
                    else:
                        f.write(line)
                
                if not updated:
                    f.write(f'\n# Data storage backend\nDATA_BACKEND={backend}\n')
            
            return {
                'success': True,
                'message': f'Backend set to {backend}. Please restart the application for changes to take effect.',
                'requires_restart': True
            }
        else:
            return {
                'success': False,
                'message': '.env file not found. Please create one from env.example'
            }
    
    except Exception as e:
        logger.error(f"Error switching backend: {e}")
        return {
            'success': False,
            'message': f'Failed to switch backend: {str(e)}'
        }

