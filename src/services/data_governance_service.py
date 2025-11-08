"""
Data Governance Service for managing data access, quality, and compliance.

This service provides high-level governance operations using Lake Formation
and implements the DataGovernanceService interface from the design document.

Requirements: 5.1, 5.4, 5.5
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.infrastructure.lake_formation_client import (
    LakeFormationClient,
    AccessResult,
    LineageResult,
    AuditResult,
    PermissionType
)

logger = logging.getLogger(__name__)


@dataclass
class ComplianceResult:
    """Result of compliance check operation."""
    success: bool
    dataset: str
    regulations: List[str]
    compliant: bool
    violations: List[str]
    timestamp: datetime


class DataGovernanceService:
    """
    High-level data governance service.
    
    Provides governance operations including:
    - Access control management
    - Data lineage tracking
    - Audit logging
    - Compliance monitoring
    """
    
    def __init__(
        self,
        region_name: str = 'us-east-1',
        profile_name: Optional[str] = None
    ):
        """
        Initialize Data Governance Service.
        
        Args:
            region_name: AWS region name
            profile_name: AWS profile name (optional)
        """
        self.lf_client = LakeFormationClient(
            region_name=region_name,
            profile_name=profile_name
        )
        self.region_name = region_name
        
        logger.info("Initialized Data Governance Service")
    
    def grant_table_access(
        self,
        user: str,
        table: str,
        permissions: List[str]
    ) -> AccessResult:
        """
        Grant table access to a user.
        
        Args:
            user: User or role ARN
            table: Table name in format 'database.table'
            permissions: List of permissions to grant
            
        Returns:
            AccessResult with operation details
        """
        try:
            # Parse table name
            if '.' not in table:
                raise ValueError(f"Table must be in format 'database.table', got: {table}")
            
            database_name, table_name = table.split('.', 1)
            
            # Grant permissions
            result = self.lf_client.grant_table_access(
                principal=user,
                database_name=database_name,
                table_name=table_name,
                permissions=permissions
            )
            
            logger.info(f"Granted {permissions} on {table} to {user}")
            return result
            
        except Exception as e:
            logger.error(f"Error granting table access: {str(e)}")
            return AccessResult(
                success=False,
                principal=user,
                resource=table,
                permissions=permissions,
                message=f'Error: {str(e)}',
                timestamp=datetime.utcnow()
            )
    
    def revoke_table_access(
        self,
        user: str,
        table: str,
        permissions: List[str]
    ) -> AccessResult:
        """
        Revoke table access from a user.
        
        Args:
            user: User or role ARN
            table: Table name in format 'database.table'
            permissions: List of permissions to revoke
            
        Returns:
            AccessResult with operation details
        """
        try:
            # Parse table name
            if '.' not in table:
                raise ValueError(f"Table must be in format 'database.table', got: {table}")
            
            database_name, table_name = table.split('.', 1)
            
            # Revoke permissions
            result = self.lf_client.revoke_table_access(
                principal=user,
                database_name=database_name,
                table_name=table_name,
                permissions=permissions
            )
            
            logger.info(f"Revoked {permissions} on {table} from {user}")
            return result
            
        except Exception as e:
            logger.error(f"Error revoking table access: {str(e)}")
            return AccessResult(
                success=False,
                principal=user,
                resource=table,
                permissions=permissions,
                message=f'Error: {str(e)}',
                timestamp=datetime.utcnow()
            )
    
    def grant_database_access(
        self,
        user: str,
        database: str,
        permissions: List[str]
    ) -> AccessResult:
        """
        Grant database-level access to a user.
        
        Args:
            user: User or role ARN
            database: Database name
            permissions: List of permissions to grant
            
        Returns:
            AccessResult with operation details
        """
        result = self.lf_client.grant_database_access(
            principal=user,
            database_name=database,
            permissions=permissions
        )
        
        logger.info(f"Granted {permissions} on database {database} to {user}")
        return result
    
    def setup_concert_data_permissions(
        self,
        data_engineer_role: str,
        data_scientist_role: str,
        analyst_role: str,
        database_name: str = 'concert_data'
    ) -> Dict[str, List[AccessResult]]:
        """
        Set up standard permissions for concert data platform roles.
        
        Args:
            data_engineer_role: ARN for data engineer role
            data_scientist_role: ARN for data scientist role
            analyst_role: ARN for analyst role
            database_name: Database name
            
        Returns:
            Dictionary of results by role
        """
        results = {
            'data_engineer': [],
            'data_scientist': [],
            'analyst': []
        }
        
        # Data Engineers: Full access to all tables
        engineer_tables = ['artists', 'venues', 'concerts', 'ticket_sales']
        for table in engineer_tables:
            result = self.grant_table_access(
                user=data_engineer_role,
                table=f"{database_name}.{table}",
                permissions=['SELECT', 'INSERT', 'DELETE', 'ALTER']
            )
            results['data_engineer'].append(result)
        
        # Data Scientists: Read access + ability to create derived tables
        scientist_perms = self.lf_client.grant_database_access(
            principal=data_scientist_role,
            database_name=database_name,
            permissions=['CREATE_TABLE']
        )
        results['data_scientist'].append(scientist_perms)
        
        for table in engineer_tables:
            result = self.grant_table_access(
                user=data_scientist_role,
                table=f"{database_name}.{table}",
                permissions=['SELECT']
            )
            results['data_scientist'].append(result)
        
        # Analysts: Read-only access
        for table in engineer_tables:
            result = self.grant_table_access(
                user=analyst_role,
                table=f"{database_name}.{table}",
                permissions=['SELECT']
            )
            results['analyst'].append(result)
        
        logger.info("Set up concert data permissions for all roles")
        return results

    def track_data_lineage(
        self,
        source: str,
        target: str,
        transformation: str
    ) -> LineageResult:
        """
        Track data lineage from source to target.
        
        Args:
            source: Source data identifier
            target: Target data identifier
            transformation: Description of transformation
            
        Returns:
            LineageResult with tracking details
        """
        result = self.lf_client.track_data_lineage(
            source=source,
            target=target,
            transformation=transformation
        )
        
        logger.info(f"Tracked lineage: {source} -> {target}")
        return result
    
    def track_etl_lineage(
        self,
        source_table: str,
        target_table: str,
        etl_job_name: str,
        transformation_details: Optional[Dict[str, Any]] = None
    ) -> LineageResult:
        """
        Track lineage for ETL job execution.
        
        Args:
            source_table: Source table name
            target_table: Target table name
            etl_job_name: Name of ETL job
            transformation_details: Additional transformation metadata
            
        Returns:
            LineageResult with tracking details
        """
        transformation = f"ETL Job: {etl_job_name}"
        
        result = self.lf_client.track_data_lineage(
            source=source_table,
            target=target_table,
            transformation=transformation,
            metadata=transformation_details
        )
        
        logger.info(f"Tracked ETL lineage: {source_table} -> {target_table} via {etl_job_name}")
        return result
    
    def audit_data_access(
        self,
        user: str,
        resource: str,
        action: str
    ) -> AuditResult:
        """
        Log data access for audit purposes.
        
        Args:
            user: User performing the action
            resource: Resource being accessed
            action: Action being performed
            
        Returns:
            AuditResult with audit log details
        """
        result = self.lf_client.audit_data_access(
            user=user,
            resource=resource,
            action=action
        )
        
        logger.info(f"Audited: {user} performed {action} on {resource}")
        return result
    
    def get_access_audit_report(
        self,
        days: int = 7,
        user: Optional[str] = None,
        resource: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate audit report for data access.
        
        Args:
            days: Number of days to look back
            user: Filter by user (optional)
            resource: Filter by resource (optional)
            
        Returns:
            List of audit log entries
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        logs = self.lf_client.get_audit_logs(
            start_time=start_time,
            end_time=end_time,
            user=user,
            resource=resource
        )
        
        logger.info(f"Generated audit report: {len(logs)} entries over {days} days")
        return logs
    
    def get_lineage_report(
        self,
        resource: str,
        direction: str = 'both'
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get data lineage report for a resource.
        
        Args:
            resource: Resource identifier
            direction: 'upstream', 'downstream', or 'both'
            
        Returns:
            Dictionary with lineage information
        """
        lineage = self.lf_client.get_data_lineage(
            resource=resource,
            direction=direction
        )
        
        upstream_count = len(lineage.get('upstream', []))
        downstream_count = len(lineage.get('downstream', []))
        
        logger.info(
            f"Generated lineage report for {resource}: "
            f"{upstream_count} upstream, {downstream_count} downstream"
        )
        
        return lineage
    
    def check_compliance(
        self,
        dataset: str,
        regulations: List[str]
    ) -> ComplianceResult:
        """
        Check dataset compliance with regulations.
        
        Args:
            dataset: Dataset identifier
            regulations: List of regulations to check
            
        Returns:
            ComplianceResult with compliance status
        """
        violations = []
        
        # Check for audit logging
        if 'AUDIT_REQUIRED' in regulations:
            recent_logs = self.get_access_audit_report(
                days=1,
                resource=dataset
            )
            if not recent_logs:
                violations.append('No recent audit logs found')
        
        # Check for access controls
        if 'ACCESS_CONTROL' in regulations:
            permissions = self.lf_client.list_permissions(
                resource_type='TABLE'
            )
            
            # Check if dataset has any permissions configured
            dataset_perms = [
                p for p in permissions
                if dataset in str(p.get('Resource', {}))
            ]
            
            if not dataset_perms:
                violations.append('No access controls configured')
        
        # Check for data lineage
        if 'LINEAGE_TRACKING' in regulations:
            lineage = self.get_lineage_report(dataset)
            if not lineage.get('upstream') and not lineage.get('downstream'):
                violations.append('No lineage information available')
        
        compliant = len(violations) == 0
        
        result = ComplianceResult(
            success=True,
            dataset=dataset,
            regulations=regulations,
            compliant=compliant,
            violations=violations,
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"Compliance check for {dataset}: "
            f"{'COMPLIANT' if compliant else 'NON-COMPLIANT'}"
        )
        
        return result
    
    def register_concert_data_catalog(
        self,
        database_name: str,
        s3_bucket: str,
        s3_prefix: str = 'processed'
    ) -> Dict[str, Any]:
        """
        Register concert data tables in the Glue Data Catalog.
        
        Args:
            database_name: Database name
            s3_bucket: S3 bucket name
            s3_prefix: S3 prefix for data
            
        Returns:
            Registration results
        """
        results = {}
        
        # Define concert data tables
        tables = {
            'artists': [
                {'Name': 'artist_id', 'Type': 'string'},
                {'Name': 'name', 'Type': 'string'},
                {'Name': 'genre', 'Type': 'array<string>'},
                {'Name': 'popularity_score', 'Type': 'double'},
                {'Name': 'formation_date', 'Type': 'date'},
                {'Name': 'spotify_id', 'Type': 'string'},
                {'Name': 'created_at', 'Type': 'timestamp'},
                {'Name': 'updated_at', 'Type': 'timestamp'}
            ],
            'venues': [
                {'Name': 'venue_id', 'Type': 'string'},
                {'Name': 'name', 'Type': 'string'},
                {'Name': 'city', 'Type': 'string'},
                {'Name': 'state', 'Type': 'string'},
                {'Name': 'country', 'Type': 'string'},
                {'Name': 'capacity', 'Type': 'int'},
                {'Name': 'venue_type', 'Type': 'string'},
                {'Name': 'ticketmaster_id', 'Type': 'string'},
                {'Name': 'created_at', 'Type': 'timestamp'},
                {'Name': 'updated_at', 'Type': 'timestamp'}
            ],
            'concerts': [
                {'Name': 'concert_id', 'Type': 'string'},
                {'Name': 'artist_id', 'Type': 'string'},
                {'Name': 'venue_id', 'Type': 'string'},
                {'Name': 'event_date', 'Type': 'timestamp'},
                {'Name': 'total_attendance', 'Type': 'int'},
                {'Name': 'revenue', 'Type': 'double'},
                {'Name': 'status', 'Type': 'string'},
                {'Name': 'created_at', 'Type': 'timestamp'},
                {'Name': 'updated_at', 'Type': 'timestamp'}
            ],
            'ticket_sales': [
                {'Name': 'sale_id', 'Type': 'string'},
                {'Name': 'concert_id', 'Type': 'string'},
                {'Name': 'price_tier', 'Type': 'string'},
                {'Name': 'quantity', 'Type': 'int'},
                {'Name': 'unit_price', 'Type': 'double'},
                {'Name': 'purchase_timestamp', 'Type': 'timestamp'},
                {'Name': 'customer_segment', 'Type': 'string'},
                {'Name': 'created_at', 'Type': 'timestamp'}
            ]
        }
        
        # Register each table
        for table_name, columns in tables.items():
            s3_location = f"s3://{s3_bucket}/{s3_prefix}/{table_name}/"
            
            result = self.lf_client.register_catalog_table(
                database_name=database_name,
                table_name=table_name,
                s3_location=s3_location,
                columns=columns
            )
            
            results[table_name] = result
            
            # Track lineage for catalog registration
            if result['success']:
                self.track_data_lineage(
                    source=s3_location,
                    target=f"{database_name}.{table_name}",
                    transformation='Catalog Registration'
                )
        
        logger.info(f"Registered {len(tables)} tables in catalog")
        return results
    
    def get_governance_summary(self) -> Dict[str, Any]:
        """
        Get summary of governance status.
        
        Returns:
            Dictionary with governance metrics
        """
        # Get recent audit activity
        recent_audits = self.get_access_audit_report(days=7)
        
        # Get permissions count
        all_permissions = self.lf_client.list_permissions()
        
        summary = {
            'audit_logs_last_7_days': len(recent_audits),
            'total_permissions': len(all_permissions),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("Generated governance summary")
        return summary
