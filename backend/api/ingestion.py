"""
Data Ingestion API endpoints.

Handles uploading and ingesting findings/cases from various file formats:
- JSON files
- CSV files
- JSONL (JSON Lines) files
"""

import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pathlib import Path
import tempfile

from services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)

router = APIRouter()


class IngestionStats(BaseModel):
    """Ingestion statistics response."""
    findings_total: int
    findings_imported: int
    findings_skipped: int
    findings_errors: int
    cases_total: int
    cases_imported: int
    cases_skipped: int
    cases_errors: int
    success: bool
    message: str


@router.post("/upload", response_model=IngestionStats)
async def upload_and_ingest_file(
    file: UploadFile = File(...),
    data_type: str = Form("finding"),
    format: Optional[str] = Form(None)
):
    """
    Upload and ingest a file containing findings or cases.
    
    Args:
        file: The file to upload (JSON, CSV, or JSONL)
        data_type: Type of data ('finding' or 'case')
        format: File format ('json', 'csv', 'jsonl'). Auto-detected if not provided.
    
    Returns:
        Ingestion statistics
    """
    if data_type not in ['finding', 'case']:
        raise HTTPException(status_code=400, detail="data_type must be 'finding' or 'case'")
    
    # Auto-detect format from filename if not provided
    if not format:
        filename = file.filename.lower()
        if filename.endswith('.json'):
            format = 'json'
        elif filename.endswith('.csv'):
            format = 'csv'
        elif filename.endswith('.jsonl') or filename.endswith('.ndjson'):
            format = 'jsonl'
        else:
            raise HTTPException(
                status_code=400,
                detail="Unable to detect file format. Please specify format parameter or use .json, .csv, or .jsonl extension"
            )
    
    if format not in ['json', 'csv', 'jsonl']:
        raise HTTPException(status_code=400, detail="format must be 'json', 'csv', or 'jsonl'")
    
    try:
        # Read file content
        content = await file.read()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix=f'.{format}') as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        
        try:
            # Ingest the file
            ingestion_service = IngestionService()
            
            if format == 'json':
                stats = ingestion_service.ingest_json_file(temp_path)
            elif format == 'csv':
                stats = ingestion_service.ingest_csv_file(temp_path, data_type=data_type)
            elif format == 'jsonl':
                stats = ingestion_service.ingest_jsonl_file(temp_path, data_type=data_type)
            
            # Clean up temp file
            temp_path.unlink()
            
            # Determine success
            success = (
                stats['findings_errors'] == 0 and
                stats['cases_errors'] == 0 and
                (stats['findings_imported'] > 0 or stats['cases_imported'] > 0 or
                 stats['findings_skipped'] > 0 or stats['cases_skipped'] > 0)
            )
            
            # Build message
            messages = []
            if stats['findings_imported'] > 0:
                messages.append(f"Imported {stats['findings_imported']} findings")
            if stats['findings_skipped'] > 0:
                messages.append(f"Skipped {stats['findings_skipped']} duplicate findings")
            if stats['cases_imported'] > 0:
                messages.append(f"Imported {stats['cases_imported']} cases")
            if stats['cases_skipped'] > 0:
                messages.append(f"Skipped {stats['cases_skipped']} duplicate cases")
            if stats['findings_errors'] > 0:
                messages.append(f"⚠ {stats['findings_errors']} finding errors")
            if stats['cases_errors'] > 0:
                messages.append(f"⚠ {stats['cases_errors']} case errors")
            
            message = ". ".join(messages) if messages else "No data imported"
            
            return IngestionStats(
                **stats,
                success=success,
                message=message
            )
        
        finally:
            # Ensure temp file is deleted
            if temp_path.exists():
                temp_path.unlink()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest-string", response_model=IngestionStats)
async def ingest_from_string(
    data: str = Form(...),
    format: str = Form("json"),
    data_type: str = Form("finding")
):
    """
    Ingest data from a string.
    
    Args:
        data: Data as string
        format: Format ('json', 'csv', 'jsonl')
        data_type: Type of data ('finding' or 'case')
    
    Returns:
        Ingestion statistics
    """
    if data_type not in ['finding', 'case']:
        raise HTTPException(status_code=400, detail="data_type must be 'finding' or 'case'")
    
    if format not in ['json', 'csv', 'jsonl']:
        raise HTTPException(status_code=400, detail="format must be 'json', 'csv', or 'jsonl'")
    
    try:
        ingestion_service = IngestionService()
        stats = ingestion_service.ingest_from_string(data, format=format, data_type=data_type)
        
        # Determine success
        success = (
            stats['findings_errors'] == 0 and
            stats['cases_errors'] == 0 and
            (stats['findings_imported'] > 0 or stats['cases_imported'] > 0)
        )
        
        # Build message
        messages = []
        if stats['findings_imported'] > 0:
            messages.append(f"Imported {stats['findings_imported']} findings")
        if stats['findings_skipped'] > 0:
            messages.append(f"Skipped {stats['findings_skipped']} duplicate findings")
        if stats['cases_imported'] > 0:
            messages.append(f"Imported {stats['cases_imported']} cases")
        if stats['cases_skipped'] > 0:
            messages.append(f"Skipped {stats['cases_skipped']} duplicate cases")
        if stats['findings_errors'] > 0:
            messages.append(f"⚠ {stats['findings_errors']} finding errors")
        if stats['cases_errors'] > 0:
            messages.append(f"⚠ {stats['cases_errors']} case errors")
        
        message = ". ".join(messages) if messages else "No data imported"
        
        return IngestionStats(
            **stats,
            success=success,
            message=message
        )
    
    except Exception as e:
        logger.error(f"Error ingesting string data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/formats")
async def get_supported_formats():
    """
    Get information about supported file formats.
    
    Returns:
        Dictionary of supported formats and their specifications
    """
    return {
        "formats": {
            "json": {
                "name": "JSON",
                "extensions": [".json"],
                "description": "Standard JSON format",
                "example_structure": {
                    "findings": [
                        {
                            "finding_id": "f-20260114-abc123",
                            "embedding": [0.1, 0.2, "...768 values"],
                            "mitre_predictions": {"T1071.001": 0.85},
                            "anomaly_score": 0.75,
                            "timestamp": "2026-01-14T10:00:00Z",
                            "data_source": "flow",
                            "severity": "high",
                            "status": "new"
                        }
                    ],
                    "cases": [
                        {
                            "case_id": "case-2026-01-14-xyz789",
                            "title": "Investigation",
                            "finding_ids": ["f-20260114-abc123"],
                            "status": "open",
                            "priority": "high"
                        }
                    ]
                }
            },
            "jsonl": {
                "name": "JSON Lines",
                "extensions": [".jsonl", ".ndjson"],
                "description": "One JSON object per line",
                "example": '{"finding_id": "f-123", "anomaly_score": 0.8}\n{"finding_id": "f-456", "anomaly_score": 0.9}'
            },
            "csv": {
                "name": "CSV",
                "extensions": [".csv"],
                "description": "Comma-separated values",
                "finding_columns": [
                    "finding_id",
                    "anomaly_score",
                    "timestamp",
                    "data_source",
                    "severity",
                    "status",
                    "cluster_id",
                    "embedding (comma-separated floats)",
                    "mitre_predictions (JSON string or technique:score pairs)",
                    "entity_context (JSON string)"
                ],
                "case_columns": [
                    "case_id",
                    "title",
                    "description",
                    "finding_ids (comma-separated)",
                    "status",
                    "priority",
                    "assignee",
                    "tags (comma-separated)"
                ]
            }
        },
        "data_types": {
            "finding": "Security findings with embeddings and MITRE predictions",
            "case": "Investigation cases grouping related findings"
        },
        "notes": [
            "finding_id and case_id are auto-generated if not provided",
            "Duplicate IDs are automatically skipped",
            "All data is stored in PostgreSQL when available, falls back to JSON files",
            "Embeddings default to 768-dimensional zero vector if not provided",
            "Timestamps are parsed from various formats or default to current time"
        ]
    }


@router.get("/csv-template/{data_type}")
async def get_csv_template(data_type: str):
    """
    Get a CSV template for the specified data type.
    
    Args:
        data_type: Type of data ('finding' or 'case')
    
    Returns:
        CSV template string
    """
    if data_type == 'finding':
        return {
            "template": "finding_id,anomaly_score,timestamp,data_source,severity,status,cluster_id,mitre_predictions,entity_context\n" +
                       "f-20260114-example,0.85,2026-01-14T10:00:00Z,flow,high,new,c-beaconing-001,\"{\"\"T1071.001\"\": 0.85}\",\"{\"\"src_ip\"\": \"\"192.168.1.100\"\"}\"\n",
            "description": "CSV template for findings. Note: embedding column omitted for brevity (768 values)"
        }
    elif data_type == 'case':
        return {
            "template": "case_id,title,description,finding_ids,status,priority,assignee,tags\n" +
                       "case-2026-01-14-example,Suspicious Activity,Investigation of unusual network traffic,\"f-123,f-456\",open,high,analyst@example.com,\"lateral-movement,investigation\"\n",
            "description": "CSV template for cases"
        }
    else:
        raise HTTPException(status_code=400, detail="data_type must be 'finding' or 'case'")

