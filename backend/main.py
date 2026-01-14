"""
FastAPI Backend for DeepTempo AI SOC Web Application

Main application entry point for the REST API server.
"""

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api import (
    findings_router,
    cases_router,
    mcp_router,
    claude_router,
    config_router,
    timesketch_router,
    attack_router,
    agents_router,
    custom_integrations_router,
    storage_status_router
)
from api.integrations_compatibility import router as compatibility_router
from api.ingestion import router as ingestion_router

# Configure logging
log_dir = Path.home() / '.deeptempo'
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / 'api.log')
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DeepTempo AI SOC API",
    description="REST API for DeepTempo AI SOC Application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:6988",  # Frontend dev server
        "http://localhost:3000",  # Alternative React dev server
        "http://localhost:5173"   # Alternative Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(findings_router, prefix="/api/findings", tags=["findings"])
app.include_router(cases_router, prefix="/api/cases", tags=["cases"])
app.include_router(mcp_router, prefix="/api/mcp", tags=["mcp"])
app.include_router(claude_router, prefix="/api/claude", tags=["claude"])
app.include_router(config_router, prefix="/api/config", tags=["config"])
app.include_router(timesketch_router, prefix="/api/timesketch", tags=["timesketch"])
app.include_router(attack_router, prefix="/api/attack", tags=["attack"])
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])
app.include_router(compatibility_router, prefix="/api/integrations", tags=["integrations"])
app.include_router(custom_integrations_router, prefix="/api/custom-integrations", tags=["custom-integrations"])
app.include_router(ingestion_router, prefix="/api/ingest", tags=["ingestion"])
app.include_router(storage_status_router, prefix="/api/storage", tags=["storage"])

@app.on_event("startup")
async def startup_event():
    """Initialize database, MCP tools and check integration compatibility on startup."""
    logger.info("=" * 60)
    logger.info("Starting DeepTempo AI SOC Backend")
    logger.info("=" * 60)
    
    # Initialize data storage backend
    logger.info("Initializing data storage...")
    try:
        from services.database_data_service import DatabaseDataService
        import os
        
        # Check configuration preference
        data_backend = os.getenv('DATA_BACKEND', 'database').lower()
        use_database = data_backend == 'database'
        
        if use_database:
            logger.info("Attempting to connect to PostgreSQL database...")
            try:
                # Create a test instance to check database availability
                test_service = DatabaseDataService(use_database=True, auto_fallback=True)
                
                if test_service.is_using_database():
                    logger.info("✓ PostgreSQL database connected and ready")
                    backend_info = test_service.get_backend_info()
                    logger.info(f"  Backend: {backend_info['backend']}")
                else:
                    logger.warning("⚠ PostgreSQL not available")
                    logger.warning("  Using JSON file storage as fallback")
                    logger.warning("  To enable PostgreSQL:")
                    logger.warning("    1. Start database: ./start_database.sh")
                    logger.warning("    2. Restart application: ./start_web.sh")
                
            except Exception as e:
                logger.warning(f"⚠ Could not connect to PostgreSQL: {e}")
                logger.warning("  Using JSON file storage as fallback")
        else:
            logger.info("Using JSON file storage (DATA_BACKEND=json)")
            
    except ImportError as e:
        logger.warning(f"Database modules not available: {e}")
        logger.warning("Using JSON file storage")
    except Exception as e:
        logger.error(f"Error during storage initialization: {e}")
        logger.warning("Falling back to JSON file storage")
    
    # Check integration compatibility
    logger.info("Checking integration compatibility...")
    try:
        from services.integration_compatibility_service import get_compatibility_service
        
        compat_service = get_compatibility_service()
        system_info = compat_service.get_system_info()
        logger.info(f"System: Python {system_info['python_version']} on {system_info['platform']}")
        
        # Log compatibility issues
        statuses = compat_service.get_all_statuses()
        incompatible = [k for k, v in statuses.items() if v.get('status') == 'incompatible']
        not_installed = [k for k, v in statuses.items() if v.get('status') == 'not_installed']
        
        if incompatible:
            logger.warning(f"Incompatible integrations: {', '.join(incompatible)}")
        if not_installed:
            logger.info(f"Not installed integrations: {', '.join(not_installed)}")
        
        installed_count = sum(1 for v in statuses.values() if v.get('installed'))
        logger.info(f"Integration status: {installed_count}/{len(statuses)} installed")
    except Exception as e:
        logger.error(f"Error checking compatibility: {e}")
    
    logger.info("Initializing MCP client and loading tools...")
    try:
        from services.mcp_client import get_mcp_client
        from services.mcp_service import MCPService
        import asyncio
        
        # Get MCP client and service
        mcp_client = get_mcp_client()
        
        if mcp_client:
            # Get list of all servers
            mcp_service = mcp_client.mcp_service
            servers = mcp_service.list_servers()
            
            # Connect to each server to cache tools
            connected_count = 0
            for server_name in servers:
                try:
                    success = await mcp_client.connect_to_server(server_name)
                    if success:
                        connected_count += 1
                        logger.info(f"Connected to MCP server: {server_name}")
                    else:
                        logger.warning(f"Failed to connect to MCP server: {server_name}")
                except Exception as e:
                    logger.error(f"Error connecting to {server_name}: {e}")
            
            logger.info(f"MCP initialization complete: {connected_count}/{len(servers)} servers connected")
            
            # Log available tools
            tools = await mcp_client.list_tools()
            total_tools = sum(len(t) for t in tools.values())
            logger.info(f"Loaded {total_tools} MCP tools from {len(tools)} servers")
        else:
            logger.warning("MCP client not available - MCP SDK may not be installed")
    except Exception as e:
        logger.error(f"Error during MCP initialization: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up MCP connections on shutdown."""
    logger.info("Shutting down MCP connections...")
    try:
        from services.mcp_client import get_mcp_client
        
        mcp_client = get_mcp_client()
        if mcp_client:
            # Close all MCP sessions
            await mcp_client.close_all()
            logger.info("All MCP connections closed")
            
            # Stop all MCP server processes managed by MCPService
            mcp_service = mcp_client.mcp_service
            if mcp_service:
                stop_results = mcp_service.stop_all()
                stopped_count = sum(1 for success in stop_results.values() if success)
                logger.info(f"Stopped {stopped_count} MCP server processes")
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {e}")


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint with storage backend info."""
    try:
        from services.database_data_service import DatabaseDataService
        
        # Check storage backend
        service = DatabaseDataService(use_database=True, auto_fallback=True)
        backend_info = service.get_backend_info()
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "storage": {
                "backend": backend_info['backend'],
                "database_available": backend_info['database_available']
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "healthy",
            "version": "1.0.0",
            "storage": {
                "backend": "unknown",
                "error": str(e)
            }
        }

# Serve React static files in production
frontend_build_dir = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build_dir.exists():
    app.mount("/static", StaticFiles(directory=frontend_build_dir / "static"), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve React app for all non-API routes."""
        # Don't interfere with API routes
        if full_path.startswith("api/"):
            return {"error": "Not found"}, 404
        
        # Serve index.html for React routing
        index_file = frontend_build_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "Frontend not built"}, 404

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting DeepTempo AI SOC API server...")
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=6987,
        reload=True,
        log_level="info"
    )

