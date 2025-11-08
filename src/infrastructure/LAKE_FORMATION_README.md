# Lake Formation Data Governance Implementation

This implementation provides comprehensive data governance capabilities using AWS Lake Formation for the Data Readiness for AI demo platform.

## Overview

The Lake Formation governance implementation includes:

- **Access Control**: Fine-grained permissions for databases and tables
- **Data Catalog Management**: Registration and metadata management for data assets
- **Audit Logging**: Comprehensive logging of all data access operations
- **Data Lineage Tracking**: Track data flow from source to target
- **Compliance Checking**: Validate datasets against regulatory requirements

## Components

### 1. LakeFormationClient (`lake_formation_client.py`)

Low-level client for AWS Lake Formation operations.

**Key Features:**
- Grant/revoke table and database permissions
- Register data locations and catalog tables
- Track data lineage
- Audit data access operations
- Query audit logs and lineage information

**Example Usage:**
```python
from src.infrastructure.lake_formation_client import LakeFormationClient

# Initialize client
lf_client = LakeFormationClient(region_name='us-east-1')

# Grant table access
result = lf_client.grant_table_access(
    principal='arn:aws:iam::123456789012:role/DataScientist',
    database_name='concert_data',
    table_name='artists',
    permissions=['SELECT']
)

# Track data lineage
lineage = lf_client.track_data_lineage(
    source='raw_data.spotify_artists',
    target='concert_data.artists',
    transformation='ETL normalization'
)

# Audit data access
audit = lf_client.audit_data_access(
    user='analyst-user',
    resource='concert_data.artists',
    action='SELECT'
)
```

### 2. DataGovernanceService (`data_governance_service.py`)

High-level service for data governance operations.

**Key Features:**
- Simplified access control management
- Concert data catalog registration
- ETL lineage tracking
- Audit reporting
- Compliance checking
- Governance summaries

**Example Usage:**
```python
from src.services.data_governance_service import DataGovernanceService

# Initialize service
governance = DataGovernanceService(region_name='us-east-1')

# Set up permissions for concert data
results = governance.setup_concert_data_permissions(
    data_engineer_role='arn:aws:iam::123456789012:role/DataEngineer',
    data_scientist_role='arn:aws:iam::123456789012:role/DataScientist',
    analyst_role='arn:aws:iam::123456789012:role/Analyst'
)

# Register concert data catalog
catalog_results = governance.register_concert_data_catalog(
    database_name='concert_data',
    s3_bucket='my-concert-data-bucket'
)

# Track ETL lineage
lineage = governance.track_etl_lineage(
    source_table='raw_data.spotify_artists',
    target_table='concert_data.artists',
    etl_job_name='normalize_artist_data'
)

# Generate audit report
audit_logs = governance.get_access_audit_report(days=7)

# Check compliance
compliance = governance.check_compliance(
    dataset='concert_data.artists',
    regulations=['AUDIT_REQUIRED', 'ACCESS_CONTROL', 'LINEAGE_TRACKING']
)
```

## Requirements Coverage

This implementation satisfies the following requirements:

### Requirement 5.1
**"THE Data_Readiness_Platform SHALL implement AWS LakeFormation for data governance and access control"**

✓ Implemented via:
- `LakeFormationClient` for Lake Formation operations
- `grant_table_access()` and `grant_database_access()` methods
- `setup_concert_data_permissions()` for role-based access control

### Requirement 5.4
**"WHEN system errors occur, THE AgentCore_Services SHALL send automated alerts to administrators"**

✓ Implemented via:
- `audit_data_access()` for logging all operations
- CloudWatch Logs integration for centralized logging
- `get_access_audit_report()` for monitoring and alerting

### Requirement 5.5
**"THE Data_Readiness_Platform SHALL maintain data lineage tracking from source to AI model consumption"**

✓ Implemented via:
- `track_data_lineage()` for lineage tracking
- `track_etl_lineage()` for ETL-specific lineage
- `get_data_lineage()` for querying lineage information
- `get_lineage_report()` for lineage visualization

## Data Models

### AccessResult
Result of access control operations.
```python
@dataclass
class AccessResult:
    success: bool
    principal: str
    resource: str
    permissions: List[str]
    message: str
    timestamp: datetime
```

### LineageResult
Result of data lineage tracking.
```python
@dataclass
class LineageResult:
    success: bool
    source: str
    target: str
    transformation: str
    lineage_id: str
    timestamp: datetime
```

### AuditResult
Result of audit logging operations.
```python
@dataclass
class AuditResult:
    success: bool
    audit_id: str
    user: str
    resource: str
    action: str
    timestamp: datetime
    details: Dict[str, Any]
```

### ComplianceResult
Result of compliance checking.
```python
@dataclass
class ComplianceResult:
    success: bool
    dataset: str
    regulations: List[str]
    compliant: bool
    violations: List[str]
    timestamp: datetime
```

## Permission Types

The implementation supports the following Lake Formation permission types:

- `SELECT`: Read data from tables
- `INSERT`: Insert data into tables
- `DELETE`: Delete data from tables
- `ALTER`: Modify table structure
- `DROP`: Drop tables
- `CREATE_TABLE`: Create new tables in database
- `DESCRIBE`: View table metadata
- `ALL`: All permissions

## Concert Data Catalog Schema

The service automatically registers the following tables:

### artists
- artist_id (string)
- name (string)
- genre (array<string>)
- popularity_score (double)
- formation_date (date)
- spotify_id (string)
- created_at (timestamp)
- updated_at (timestamp)

### venues
- venue_id (string)
- name (string)
- city (string)
- state (string)
- country (string)
- capacity (int)
- venue_type (string)
- ticketmaster_id (string)
- created_at (timestamp)
- updated_at (timestamp)

### concerts
- concert_id (string)
- artist_id (string)
- venue_id (string)
- event_date (timestamp)
- total_attendance (int)
- revenue (double)
- status (string)
- created_at (timestamp)
- updated_at (timestamp)

### ticket_sales
- sale_id (string)
- concert_id (string)
- price_tier (string)
- quantity (int)
- unit_price (double)
- purchase_timestamp (timestamp)
- customer_segment (string)
- created_at (timestamp)

## Audit Logging

All data access operations are logged to CloudWatch Logs:

**Log Group:** `/aws/lakeformation/audit`

**Log Streams:**
- `audit/YYYY/MM/DD` - Audit logs
- `lineage/YYYY/MM/DD` - Lineage tracking logs

**Audit Log Format:**
```json
{
  "audit_id": "audit_1234567890.123",
  "user": "analyst-user",
  "resource": "concert_data.artists",
  "action": "SELECT",
  "timestamp": "2025-11-07T12:00:00Z",
  "details": {}
}
```

**Lineage Log Format:**
```json
{
  "lineage_id": "source_target_2025-11-07T12:00:00Z",
  "source": "raw_data.spotify_artists",
  "target": "concert_data.artists",
  "transformation": "ETL normalization",
  "timestamp": "2025-11-07T12:00:00Z",
  "metadata": {
    "records_processed": 10000,
    "records_output": 9500
  }
}
```

## Compliance Regulations

The implementation supports checking the following regulations:

- **AUDIT_REQUIRED**: Ensures audit logs exist for the dataset
- **ACCESS_CONTROL**: Verifies access controls are configured
- **LINEAGE_TRACKING**: Confirms lineage information is available

## AWS Permissions Required

To use this implementation, the following AWS permissions are required:

### Lake Formation Permissions
- `lakeformation:GrantPermissions`
- `lakeformation:RevokePermissions`
- `lakeformation:ListPermissions`
- `lakeformation:RegisterResource`
- `lakeformation:DeregisterResource`

### Glue Permissions
- `glue:CreateTable`
- `glue:UpdateTable`
- `glue:GetTable`
- `glue:GetDatabase`

### CloudWatch Logs Permissions
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`
- `logs:FilterLogEvents`

### IAM Permissions
- `iam:PassRole` (for Lake Formation service role)

## Example Workflows

### Setting Up New User Access
```python
governance = DataGovernanceService()

# Grant read access to analyst
result = governance.grant_table_access(
    user='arn:aws:iam::123456789012:user/new-analyst',
    table='concert_data.artists',
    permissions=['SELECT']
)

# Audit the grant
governance.audit_data_access(
    user='admin',
    resource='concert_data.artists',
    action='GRANT_ACCESS'
)
```

### Tracking ETL Pipeline
```python
governance = DataGovernanceService()

# Track each stage of ETL
governance.track_etl_lineage(
    source_table='raw_data.spotify_artists',
    target_table='staging.artists',
    etl_job_name='extract_artists'
)

governance.track_etl_lineage(
    source_table='staging.artists',
    target_table='concert_data.artists',
    etl_job_name='normalize_artists'
)

# Get full lineage
lineage = governance.get_lineage_report(
    resource='concert_data.artists',
    direction='upstream'
)
```

### Compliance Audit
```python
governance = DataGovernanceService()

# Check compliance for all tables
tables = ['artists', 'venues', 'concerts', 'ticket_sales']
for table in tables:
    result = governance.check_compliance(
        dataset=f'concert_data.{table}',
        regulations=['AUDIT_REQUIRED', 'ACCESS_CONTROL', 'LINEAGE_TRACKING']
    )
    
    if not result.compliant:
        print(f"Violations for {table}: {result.violations}")
```

## Testing

Run the validation script to verify the implementation:

```bash
python validate_governance_implementation.py
```

See `example_governance_usage.py` for comprehensive usage examples.

## Integration with Other Components

This governance implementation integrates with:

- **Glue ETL Jobs**: Track lineage for ETL transformations
- **Redshift**: Manage access to data warehouse tables
- **S3 Data Lake**: Register and govern data lake locations
- **CloudWatch**: Centralized audit logging and monitoring
- **IAM**: Role-based access control

## Best Practices

1. **Always audit access grants**: Log all permission changes
2. **Track lineage for all transformations**: Maintain complete data lineage
3. **Regular compliance checks**: Run compliance checks periodically
4. **Use role-based access**: Grant permissions to roles, not individual users
5. **Review audit logs**: Regularly review access patterns
6. **Document transformations**: Include detailed transformation metadata in lineage

## Troubleshooting

### Permission Denied Errors
- Verify IAM role has required Lake Formation permissions
- Check if Lake Formation is enabled for the region
- Ensure data location is registered with Lake Formation

### Audit Logs Not Appearing
- Verify CloudWatch Logs permissions
- Check log group exists: `/aws/lakeformation/audit`
- Allow time for log propagation (up to 1 minute)

### Lineage Not Tracking
- Ensure `track_data_lineage()` is called after transformations
- Verify CloudWatch Logs write permissions
- Check log stream creation permissions

## Future Enhancements

Potential improvements for future iterations:

- Integration with AWS Glue Data Quality
- Automated compliance reporting
- Data classification and tagging
- Integration with AWS Security Hub
- Real-time access monitoring dashboards
- Machine learning-based anomaly detection for access patterns
