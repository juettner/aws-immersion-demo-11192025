"""
AWS Lake Formation client for data governance and access control.

This module provides functionality for:
- Managing Lake Formation permissions and access policies
- Registering data catalog resources
- Implementing audit logging for data access operations
- Tracking data lineage

Requirements: 5.1, 5.4, 5.5
"""

import boto3
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class PermissionType(Enum):
    """Lake Formation permission types."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    DELETE = "DELETE"
    ALTER = "ALTER"
    DROP = "DROP"
    CREATE_TABLE = "CREATE_TABLE"
    DESCRIBE = "DESCRIBE"
    ALL = "ALL"


class ResourceType(Enum):
    """Lake Formation resource types."""
    DATABASE = "DATABASE"
    TABLE = "TABLE"
    DATA_LOCATION = "DATA_LOCATION"
    CATALOG = "CATALOG"


@dataclass
class AccessResult:
    """Result of access control operation."""
    success: bool
    principal: str
    resource: str
    permissions: List[str]
    message: str
    timestamp: datetime


@dataclass
class LineageResult:
    """Result of data lineage tracking operation."""
    success: bool
    source: str
    target: str
    transformation: str
    lineage_id: str
    timestamp: datetime


@dataclass
class AuditResult:
    """Result of audit logging operation."""
    success: bool
    audit_id: str
    user: str
    resource: str
    action: str
    timestamp: datetime
    details: Dict[str, Any]


class LakeFormationClient:
    """Client for AWS Lake Formation operations."""
    
    def __init__(
        self,
        region_name: str = 'us-east-1',
        profile_name: Optional[str] = None
    ):
        """
        Initialize Lake Formation client.
        
        Args:
            region_name: AWS region name
            profile_name: AWS profile name (optional)
        """
        session_kwargs = {'region_name': region_name}
        if profile_name:
            session_kwargs['profile_name'] = profile_name
            
        session = boto3.Session(**session_kwargs)
        self.lf_client = session.client('lakeformation')
        self.glue_client = session.client('glue')
        self.cloudwatch_client = session.client('logs')
        self.region_name = region_name
        
        # Initialize audit log group
        self.audit_log_group = '/aws/lakeformation/audit'
        self._ensure_log_group_exists()
        
        logger.info(f"Initialized Lake Formation client in region {region_name}")
    
    def _ensure_log_group_exists(self):
        """Ensure CloudWatch log group exists for audit logging."""
        try:
            self.cloudwatch_client.create_log_group(
                logGroupName=self.audit_log_group
            )
            logger.info(f"Created audit log group: {self.audit_log_group}")
        except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
            logger.debug(f"Audit log group already exists: {self.audit_log_group}")
        except Exception as e:
            logger.error(f"Error ensuring log group exists: {str(e)}")

    def register_data_location(
        self,
        s3_path: str,
        role_arn: str
    ) -> Dict[str, Any]:
        """
        Register an S3 location with Lake Formation.
        
        Args:
            s3_path: S3 path to register (e.g., s3://bucket/path/)
            role_arn: IAM role ARN for Lake Formation service
            
        Returns:
            Registration result
        """
        try:
            response = self.lf_client.register_resource(
                ResourceArn=s3_path,
                UseServiceLinkedRole=False,
                RoleArn=role_arn
            )
            
            logger.info(f"Registered data location: {s3_path}")
            
            # Audit log the registration
            self.audit_data_access(
                user='system',
                resource=s3_path,
                action='REGISTER_LOCATION',
                details={'role_arn': role_arn}
            )
            
            return {
                'success': True,
                'resource_arn': s3_path,
                'message': 'Data location registered successfully'
            }
            
        except Exception as e:
            logger.error(f"Error registering data location {s3_path}: {str(e)}")
            return {
                'success': False,
                'resource_arn': s3_path,
                'message': f'Registration failed: {str(e)}'
            }
    
    def deregister_data_location(self, s3_path: str) -> Dict[str, Any]:
        """
        Deregister an S3 location from Lake Formation.
        
        Args:
            s3_path: S3 path to deregister
            
        Returns:
            Deregistration result
        """
        try:
            response = self.lf_client.deregister_resource(
                ResourceArn=s3_path
            )
            
            logger.info(f"Deregistered data location: {s3_path}")
            
            # Audit log the deregistration
            self.audit_data_access(
                user='system',
                resource=s3_path,
                action='DEREGISTER_LOCATION',
                details={}
            )
            
            return {
                'success': True,
                'resource_arn': s3_path,
                'message': 'Data location deregistered successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deregistering data location {s3_path}: {str(e)}")
            return {
                'success': False,
                'resource_arn': s3_path,
                'message': f'Deregistration failed: {str(e)}'
            }
    
    def grant_table_access(
        self,
        principal: str,
        database_name: str,
        table_name: str,
        permissions: List[str],
        grantable: bool = False
    ) -> AccessResult:
        """
        Grant table-level permissions to a principal.
        
        Args:
            principal: IAM user/role ARN or principal identifier
            database_name: Glue database name
            table_name: Glue table name
            permissions: List of permissions to grant (SELECT, INSERT, etc.)
            grantable: Whether principal can grant these permissions to others
            
        Returns:
            AccessResult with operation details
        """
        try:
            # Validate permissions
            valid_permissions = [p.value for p in PermissionType]
            invalid_perms = [p for p in permissions if p not in valid_permissions]
            if invalid_perms:
                raise ValueError(f"Invalid permissions: {invalid_perms}")
            
            # Grant permissions
            response = self.lf_client.grant_permissions(
                Principal={'DataLakePrincipalIdentifier': principal},
                Resource={
                    'Table': {
                        'DatabaseName': database_name,
                        'Name': table_name
                    }
                },
                Permissions=permissions,
                PermissionsWithGrantOption=permissions if grantable else []
            )
            
            logger.info(
                f"Granted permissions {permissions} on {database_name}.{table_name} "
                f"to {principal}"
            )
            
            # Audit log the grant
            self.audit_data_access(
                user=principal,
                resource=f"{database_name}.{table_name}",
                action='GRANT_PERMISSIONS',
                details={
                    'permissions': permissions,
                    'grantable': grantable
                }
            )
            
            return AccessResult(
                success=True,
                principal=principal,
                resource=f"{database_name}.{table_name}",
                permissions=permissions,
                message='Permissions granted successfully',
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(
                f"Error granting permissions on {database_name}.{table_name}: {str(e)}"
            )
            return AccessResult(
                success=False,
                principal=principal,
                resource=f"{database_name}.{table_name}",
                permissions=permissions,
                message=f'Grant failed: {str(e)}',
                timestamp=datetime.utcnow()
            )
    
    def revoke_table_access(
        self,
        principal: str,
        database_name: str,
        table_name: str,
        permissions: List[str]
    ) -> AccessResult:
        """
        Revoke table-level permissions from a principal.
        
        Args:
            principal: IAM user/role ARN or principal identifier
            database_name: Glue database name
            table_name: Glue table name
            permissions: List of permissions to revoke
            
        Returns:
            AccessResult with operation details
        """
        try:
            response = self.lf_client.revoke_permissions(
                Principal={'DataLakePrincipalIdentifier': principal},
                Resource={
                    'Table': {
                        'DatabaseName': database_name,
                        'Name': table_name
                    }
                },
                Permissions=permissions
            )
            
            logger.info(
                f"Revoked permissions {permissions} on {database_name}.{table_name} "
                f"from {principal}"
            )
            
            # Audit log the revocation
            self.audit_data_access(
                user=principal,
                resource=f"{database_name}.{table_name}",
                action='REVOKE_PERMISSIONS',
                details={'permissions': permissions}
            )
            
            return AccessResult(
                success=True,
                principal=principal,
                resource=f"{database_name}.{table_name}",
                permissions=permissions,
                message='Permissions revoked successfully',
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(
                f"Error revoking permissions on {database_name}.{table_name}: {str(e)}"
            )
            return AccessResult(
                success=False,
                principal=principal,
                resource=f"{database_name}.{table_name}",
                permissions=permissions,
                message=f'Revoke failed: {str(e)}',
                timestamp=datetime.utcnow()
            )

    def grant_database_access(
        self,
        principal: str,
        database_name: str,
        permissions: List[str],
        grantable: bool = False
    ) -> AccessResult:
        """
        Grant database-level permissions to a principal.
        
        Args:
            principal: IAM user/role ARN or principal identifier
            database_name: Glue database name
            permissions: List of permissions to grant
            grantable: Whether principal can grant these permissions to others
            
        Returns:
            AccessResult with operation details
        """
        try:
            response = self.lf_client.grant_permissions(
                Principal={'DataLakePrincipalIdentifier': principal},
                Resource={
                    'Database': {
                        'Name': database_name
                    }
                },
                Permissions=permissions,
                PermissionsWithGrantOption=permissions if grantable else []
            )
            
            logger.info(
                f"Granted permissions {permissions} on database {database_name} "
                f"to {principal}"
            )
            
            # Audit log the grant
            self.audit_data_access(
                user=principal,
                resource=database_name,
                action='GRANT_DATABASE_PERMISSIONS',
                details={
                    'permissions': permissions,
                    'grantable': grantable
                }
            )
            
            return AccessResult(
                success=True,
                principal=principal,
                resource=database_name,
                permissions=permissions,
                message='Database permissions granted successfully',
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(
                f"Error granting database permissions on {database_name}: {str(e)}"
            )
            return AccessResult(
                success=False,
                principal=principal,
                resource=database_name,
                permissions=permissions,
                message=f'Grant failed: {str(e)}',
                timestamp=datetime.utcnow()
            )
    
    def list_permissions(
        self,
        principal: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List Lake Formation permissions.
        
        Args:
            principal: Filter by principal (optional)
            resource_type: Filter by resource type (optional)
            
        Returns:
            List of permission entries
        """
        try:
            kwargs = {}
            if principal:
                kwargs['Principal'] = {'DataLakePrincipalIdentifier': principal}
            if resource_type:
                kwargs['ResourceType'] = resource_type
            
            response = self.lf_client.list_permissions(**kwargs)
            permissions = response.get('PrincipalResourcePermissions', [])
            
            logger.info(f"Listed {len(permissions)} permission entries")
            
            return permissions
            
        except Exception as e:
            logger.error(f"Error listing permissions: {str(e)}")
            return []
    
    def register_catalog_table(
        self,
        database_name: str,
        table_name: str,
        s3_location: str,
        columns: List[Dict[str, str]],
        partition_keys: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Register a table in the Glue Data Catalog.
        
        Args:
            database_name: Glue database name
            table_name: Table name
            s3_location: S3 location of table data
            columns: List of column definitions [{'Name': 'col', 'Type': 'string'}]
            partition_keys: Optional partition key definitions
            
        Returns:
            Registration result
        """
        try:
            table_input = {
                'Name': table_name,
                'StorageDescriptor': {
                    'Columns': columns,
                    'Location': s3_location,
                    'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
                    'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
                    'SerdeInfo': {
                        'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
                    }
                }
            }
            
            if partition_keys:
                table_input['PartitionKeys'] = partition_keys
            
            response = self.glue_client.create_table(
                DatabaseName=database_name,
                TableInput=table_input
            )
            
            logger.info(f"Registered table {database_name}.{table_name} in catalog")
            
            # Audit log the registration
            self.audit_data_access(
                user='system',
                resource=f"{database_name}.{table_name}",
                action='REGISTER_TABLE',
                details={
                    's3_location': s3_location,
                    'columns': len(columns)
                }
            )
            
            return {
                'success': True,
                'database': database_name,
                'table': table_name,
                'message': 'Table registered successfully'
            }
            
        except self.glue_client.exceptions.AlreadyExistsException:
            logger.warning(f"Table {database_name}.{table_name} already exists")
            return {
                'success': True,
                'database': database_name,
                'table': table_name,
                'message': 'Table already exists'
            }
        except Exception as e:
            logger.error(f"Error registering table {database_name}.{table_name}: {str(e)}")
            return {
                'success': False,
                'database': database_name,
                'table': table_name,
                'message': f'Registration failed: {str(e)}'
            }
    
    def update_table_metadata(
        self,
        database_name: str,
        table_name: str,
        metadata: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Update table metadata in the Glue Data Catalog.
        
        Args:
            database_name: Glue database name
            table_name: Table name
            metadata: Metadata key-value pairs to update
            
        Returns:
            Update result
        """
        try:
            # Get current table definition
            response = self.glue_client.get_table(
                DatabaseName=database_name,
                Name=table_name
            )
            
            table_input = response['Table']
            
            # Remove read-only fields
            for field in ['DatabaseName', 'CreateTime', 'UpdateTime', 'CreatedBy', 
                         'IsRegisteredWithLakeFormation', 'CatalogId', 'VersionId']:
                table_input.pop(field, None)
            
            # Update parameters (metadata)
            if 'Parameters' not in table_input:
                table_input['Parameters'] = {}
            table_input['Parameters'].update(metadata)
            
            # Update table
            self.glue_client.update_table(
                DatabaseName=database_name,
                TableInput=table_input
            )
            
            logger.info(f"Updated metadata for {database_name}.{table_name}")
            
            # Audit log the update
            self.audit_data_access(
                user='system',
                resource=f"{database_name}.{table_name}",
                action='UPDATE_METADATA',
                details={'metadata_keys': list(metadata.keys())}
            )
            
            return {
                'success': True,
                'database': database_name,
                'table': table_name,
                'message': 'Metadata updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error updating metadata for {database_name}.{table_name}: {str(e)}")
            return {
                'success': False,
                'database': database_name,
                'table': table_name,
                'message': f'Update failed: {str(e)}'
            }

    def track_data_lineage(
        self,
        source: str,
        target: str,
        transformation: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LineageResult:
        """
        Track data lineage from source to target.
        
        Args:
            source: Source data identifier (table, file, etc.)
            target: Target data identifier
            transformation: Description of transformation applied
            metadata: Additional lineage metadata
            
        Returns:
            LineageResult with tracking details
        """
        try:
            lineage_id = f"{source}_{target}_{datetime.utcnow().isoformat()}"
            
            lineage_data = {
                'lineage_id': lineage_id,
                'source': source,
                'target': target,
                'transformation': transformation,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            # Store lineage in CloudWatch Logs
            log_stream_name = f"lineage/{datetime.utcnow().strftime('%Y/%m/%d')}"
            self._write_to_cloudwatch(
                log_stream_name,
                lineage_data
            )
            
            logger.info(f"Tracked lineage: {source} -> {target}")
            
            return LineageResult(
                success=True,
                source=source,
                target=target,
                transformation=transformation,
                lineage_id=lineage_id,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error tracking lineage: {str(e)}")
            return LineageResult(
                success=False,
                source=source,
                target=target,
                transformation=transformation,
                lineage_id='',
                timestamp=datetime.utcnow()
            )
    
    def audit_data_access(
        self,
        user: str,
        resource: str,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditResult:
        """
        Log data access for audit purposes.
        
        Args:
            user: User or principal performing the action
            resource: Resource being accessed
            action: Action being performed
            details: Additional audit details
            
        Returns:
            AuditResult with audit log details
        """
        try:
            audit_id = f"audit_{datetime.utcnow().timestamp()}"
            
            audit_data = {
                'audit_id': audit_id,
                'user': user,
                'resource': resource,
                'action': action,
                'timestamp': datetime.utcnow().isoformat(),
                'details': details or {}
            }
            
            # Store audit log in CloudWatch Logs
            log_stream_name = f"audit/{datetime.utcnow().strftime('%Y/%m/%d')}"
            self._write_to_cloudwatch(
                log_stream_name,
                audit_data
            )
            
            logger.info(f"Audit logged: {user} performed {action} on {resource}")
            
            return AuditResult(
                success=True,
                audit_id=audit_id,
                user=user,
                resource=resource,
                action=action,
                timestamp=datetime.utcnow(),
                details=audit_data
            )
            
        except Exception as e:
            logger.error(f"Error logging audit: {str(e)}")
            return AuditResult(
                success=False,
                audit_id='',
                user=user,
                resource=resource,
                action=action,
                timestamp=datetime.utcnow(),
                details={'error': str(e)}
            )
    
    def _write_to_cloudwatch(
        self,
        log_stream_name: str,
        log_data: Dict[str, Any]
    ):
        """
        Write log data to CloudWatch Logs.
        
        Args:
            log_stream_name: CloudWatch log stream name
            log_data: Data to log
        """
        try:
            # Create log stream if it doesn't exist
            try:
                self.cloudwatch_client.create_log_stream(
                    logGroupName=self.audit_log_group,
                    logStreamName=log_stream_name
                )
            except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Put log event
            import json
            self.cloudwatch_client.put_log_events(
                logGroupName=self.audit_log_group,
                logStreamName=log_stream_name,
                logEvents=[
                    {
                        'timestamp': int(datetime.utcnow().timestamp() * 1000),
                        'message': json.dumps(log_data)
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Error writing to CloudWatch: {str(e)}")
    
    def get_audit_logs(
        self,
        start_time: datetime,
        end_time: datetime,
        user: Optional[str] = None,
        resource: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs for a time period.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            user: Filter by user (optional)
            resource: Filter by resource (optional)
            
        Returns:
            List of audit log entries
        """
        try:
            import json
            
            # Query CloudWatch Logs
            response = self.cloudwatch_client.filter_log_events(
                logGroupName=self.audit_log_group,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                filterPattern='audit'
            )
            
            logs = []
            for event in response.get('events', []):
                try:
                    log_data = json.loads(event['message'])
                    
                    # Apply filters
                    if user and log_data.get('user') != user:
                        continue
                    if resource and log_data.get('resource') != resource:
                        continue
                    
                    logs.append(log_data)
                except json.JSONDecodeError:
                    continue
            
            logger.info(f"Retrieved {len(logs)} audit log entries")
            return logs
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {str(e)}")
            return []
    
    def get_data_lineage(
        self,
        resource: str,
        direction: str = 'both'
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get data lineage for a resource.
        
        Args:
            resource: Resource identifier
            direction: 'upstream', 'downstream', or 'both'
            
        Returns:
            Dictionary with upstream and/or downstream lineage
        """
        try:
            import json
            
            # Query CloudWatch Logs for lineage
            response = self.cloudwatch_client.filter_log_events(
                logGroupName=self.audit_log_group,
                filterPattern='lineage'
            )
            
            upstream = []
            downstream = []
            
            for event in response.get('events', []):
                try:
                    lineage_data = json.loads(event['message'])
                    
                    if direction in ['upstream', 'both']:
                        if lineage_data.get('target') == resource:
                            upstream.append(lineage_data)
                    
                    if direction in ['downstream', 'both']:
                        if lineage_data.get('source') == resource:
                            downstream.append(lineage_data)
                            
                except json.JSONDecodeError:
                    continue
            
            result = {}
            if direction in ['upstream', 'both']:
                result['upstream'] = upstream
            if direction in ['downstream', 'both']:
                result['downstream'] = downstream
            
            logger.info(
                f"Retrieved lineage for {resource}: "
                f"{len(upstream)} upstream, {len(downstream)} downstream"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving lineage: {str(e)}")
            return {'upstream': [], 'downstream': []}
