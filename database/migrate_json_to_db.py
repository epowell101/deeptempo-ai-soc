#!/usr/bin/env python3
"""
Migration script to import data from JSON files to PostgreSQL database.

This script:
1. Loads existing findings and cases from JSON files
2. Creates corresponding database records
3. Preserves all relationships and metadata
4. Provides detailed progress reporting

Usage:
    python database/migrate_json_to_db.py [--dry-run] [--clear]
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import init_database, get_db_manager
from database.service import DatabaseService
from database.models import Finding, Case

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JSONToDBMigrator:
    """Handles migration from JSON files to PostgreSQL database."""
    
    def __init__(self, data_dir: Path):
        """
        Initialize the migrator.
        
        Args:
            data_dir: Path to data directory containing JSON files
        """
        self.data_dir = data_dir
        self.findings_file = data_dir / "findings.json"
        self.cases_file = data_dir / "cases.json"
        self.db_service = DatabaseService()
        
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
    
    def load_json_findings(self) -> List[Dict]:
        """Load findings from JSON file."""
        if not self.findings_file.exists():
            logger.warning(f"Findings file not found: {self.findings_file}")
            return []
        
        try:
            with open(self.findings_file, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'findings' in data:
                findings = data['findings']
            elif isinstance(data, list):
                findings = data
            else:
                logger.error(f"Unexpected findings format: {type(data)}")
                return []
            
            logger.info(f"Loaded {len(findings)} findings from JSON")
            return findings
        
        except Exception as e:
            logger.error(f"Error loading findings from JSON: {e}")
            return []
    
    def load_json_cases(self) -> List[Dict]:
        """Load cases from JSON file."""
        if not self.cases_file.exists():
            logger.warning(f"Cases file not found: {self.cases_file}")
            return []
        
        try:
            with open(self.cases_file, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'cases' in data:
                cases = data['cases']
            elif isinstance(data, list):
                cases = data
            else:
                logger.error(f"Unexpected cases format: {type(data)}")
                return []
            
            logger.info(f"Loaded {len(cases)} cases from JSON")
            return cases
        
        except Exception as e:
            logger.error(f"Error loading cases from JSON: {e}")
            return []
    
    def parse_timestamp(self, timestamp_str: Any) -> datetime:
        """Parse timestamp string to datetime object."""
        if isinstance(timestamp_str, datetime):
            return timestamp_str
        
        if not timestamp_str:
            return datetime.utcnow()
        
        # Try different timestamp formats
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                # Remove timezone info if present (we'll store as UTC)
                ts_str = str(timestamp_str).replace('+00:00', '').replace('Z', '')
                return datetime.strptime(ts_str, fmt.replace('Z', '').replace('%z', ''))
            except ValueError:
                continue
        
        # If all parsing fails, return current time
        logger.warning(f"Could not parse timestamp: {timestamp_str}, using current time")
        return datetime.utcnow()
    
    def migrate_finding(self, finding_data: Dict, dry_run: bool = False) -> bool:
        """
        Migrate a single finding to the database.
        
        Args:
            finding_data: Finding dictionary from JSON
            dry_run: If True, don't actually insert into database
        
        Returns:
            True if successful, False otherwise
        """
        finding_id = finding_data.get('finding_id')
        if not finding_id:
            logger.error("Finding missing finding_id")
            return False
        
        try:
            # Check if finding already exists
            existing = self.db_service.get_finding(finding_id)
            if existing:
                logger.debug(f"Finding {finding_id} already exists, skipping")
                self.stats['findings_skipped'] += 1
                return True
            
            if dry_run:
                logger.info(f"[DRY RUN] Would import finding: {finding_id}")
                self.stats['findings_imported'] += 1
                return True
            
            # Parse timestamp
            timestamp = self.parse_timestamp(finding_data.get('timestamp'))
            
            # Create finding
            finding = self.db_service.create_finding(
                finding_id=finding_id,
                embedding=finding_data.get('embedding', []),
                mitre_predictions=finding_data.get('mitre_predictions', {}),
                anomaly_score=finding_data.get('anomaly_score', 0.0),
                timestamp=timestamp,
                data_source=finding_data.get('data_source', 'unknown'),
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
        
        except Exception as e:
            self.stats['findings_errors'] += 1
            logger.error(f"Error migrating finding {finding_id}: {e}")
            return False
    
    def migrate_case(self, case_data: Dict, dry_run: bool = False) -> bool:
        """
        Migrate a single case to the database.
        
        Args:
            case_data: Case dictionary from JSON
            dry_run: If True, don't actually insert into database
        
        Returns:
            True if successful, False otherwise
        """
        case_id = case_data.get('case_id')
        if not case_id:
            logger.error("Case missing case_id")
            return False
        
        try:
            # Check if case already exists
            existing = self.db_service.get_case(case_id)
            if existing:
                logger.debug(f"Case {case_id} already exists, skipping")
                self.stats['cases_skipped'] += 1
                return True
            
            if dry_run:
                logger.info(f"[DRY RUN] Would import case: {case_id}")
                self.stats['cases_imported'] += 1
                return True
            
            # Create case
            case = self.db_service.create_case(
                case_id=case_id,
                title=case_data.get('title', ''),
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
        
        except Exception as e:
            self.stats['cases_errors'] += 1
            logger.error(f"Error migrating case {case_id}: {e}")
            return False
    
    def migrate_all(self, dry_run: bool = False) -> bool:
        """
        Migrate all data from JSON to database.
        
        Args:
            dry_run: If True, don't actually insert into database
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("Starting JSON to PostgreSQL migration")
        logger.info("=" * 60)
        
        # Load data
        findings = self.load_json_findings()
        cases = self.load_json_cases()
        
        self.stats['findings_total'] = len(findings)
        self.stats['cases_total'] = len(cases)
        
        # Migrate findings first (cases reference findings)
        logger.info(f"\nMigrating {len(findings)} findings...")
        for i, finding_data in enumerate(findings, 1):
            if i % 100 == 0:
                logger.info(f"Progress: {i}/{len(findings)} findings")
            self.migrate_finding(finding_data, dry_run=dry_run)
        
        # Migrate cases
        logger.info(f"\nMigrating {len(cases)} cases...")
        for i, case_data in enumerate(cases, 1):
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(cases)} cases")
            self.migrate_case(case_data, dry_run=dry_run)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        logger.info(f"Findings:")
        logger.info(f"  Total:    {self.stats['findings_total']}")
        logger.info(f"  Imported: {self.stats['findings_imported']}")
        logger.info(f"  Skipped:  {self.stats['findings_skipped']}")
        logger.info(f"  Errors:   {self.stats['findings_errors']}")
        logger.info(f"\nCases:")
        logger.info(f"  Total:    {self.stats['cases_total']}")
        logger.info(f"  Imported: {self.stats['cases_imported']}")
        logger.info(f"  Skipped:  {self.stats['cases_skipped']}")
        logger.info(f"  Errors:   {self.stats['cases_errors']}")
        logger.info("=" * 60)
        
        success = (
            self.stats['findings_errors'] == 0 and
            self.stats['cases_errors'] == 0
        )
        
        if success:
            logger.info("✓ Migration completed successfully!")
        else:
            logger.warning("⚠ Migration completed with errors")
        
        return success


def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(description='Migrate JSON data to PostgreSQL')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run migration without actually inserting data'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing database tables before migration (USE WITH CAUTION!)'
    )
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=project_root / 'data',
        help='Path to data directory (default: ./data)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        init_database(echo=False, create_tables=True)
        
        # Clear tables if requested
        if args.clear:
            logger.warning("⚠ CLEARING ALL DATABASE TABLES ⚠")
            response = input("Are you sure you want to clear all tables? (yes/no): ")
            if response.lower() == 'yes':
                db_manager = get_db_manager()
                db_manager.drop_tables()
                db_manager.create_tables()
                logger.info("Database tables cleared and recreated")
            else:
                logger.info("Clear operation cancelled")
                return
        
        # Run migration
        migrator = JSONToDBMigrator(args.data_dir)
        success = migrator.migrate_all(dry_run=args.dry_run)
        
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.info("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

