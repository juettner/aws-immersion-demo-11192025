"""
Example usage of Data Governance Service with Lake Formation.

This demonstrates:
- Setting up Lake Formation permissions
- Registering data catalog tables
- Tracking data lineage
- Audit logging
- Compliance checking

Requirements: 5.1, 5.4, 5.5
"""

import logging
from datetime import datetime

from src.services.data_governance_service import DataGovernanceService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_setup_permissions():
    """Example: Set up Lake Formation permissions for concert data."""
    print("\n=== Setting Up Lake Formation Permissions ===\n")
    
    # Initialize service
    governance = DataGovernanceService(region_name='us-east-1')
    
    # Define role ARNs (replace with actual ARNs)
    data_engineer_role = 'arn:aws:iam::123456789012:role/DataEngineerRole'
    data_scientist_role = 'arn:aws:iam::123456789012:role/DataScientistRole'
    analyst_role = 'arn:aws:iam::123456789012:role/AnalystRole'
    
    # Set up standard permissions
    results = governance.setup_concert_data_permissions(
        data_engineer_role=data_engineer_role,
        data_scientist_role=data_scientist_role,
        analyst_role=analyst_role,
        database_name='concert_data'
    )
    
    # Display results
    for role, role_results in results.items():
        print(f"\n{role.upper()}:")
        for result in role_results:
            status = "✓" if result.success else "✗"
            print(f"  {status} {result.resource}: {result.permissions}")
    
    return results


def example_grant_table_access():
    """Example: Grant specific table access to a user."""
    print("\n=== Granting Table Access ===\n")
    
    governance = DataGovernanceService(region_name='us-east-1')
    
    # Grant SELECT permission on artists table
    result = governance.grant_table_access(
        user='arn:aws:iam::123456789012:user/analyst-user',
        table='concert_data.artists',
        permissions=['SELECT']
    )
    
    print(f"Grant Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Principal: {result.principal}")
    print(f"Resource: {result.resource}")
    print(f"Permissions: {result.permissions}")
    print(f"Message: {result.message}")
    
    return result


def example_register_catalog():
    """Example: Register concert data tables in Glue Data Catalog."""
    print("\n=== Registering Data Catalog Tables ===\n")
    
    governance = DataGovernanceService(region_name='us-east-1')
    
    # Register all concert data tables
    results = governance.register_concert_data_catalog(
        database_name='concert_data',
        s3_bucket='my-concert-data-bucket',
        s3_prefix='processed'
    )
    
    # Display results
    for table_name, result in results.items():
        status = "✓" if result['success'] else "✗"
        print(f"{status} {table_name}: {result['message']}")
    
    return results


def example_track_lineage():
    """Example: Track data lineage for ETL operations."""
    print("\n=== Tracking Data Lineage ===\n")
    
    governance = DataGovernanceService(region_name='us-east-1')
    
    # Track lineage for artist data transformation
    result = governance.track_etl_lineage(
        source_table='raw_data.spotify_artists',
        target_table='concert_data.artists',
        etl_job_name='normalize_artist_data',
        transformation_details={
            'operations': ['deduplicate', 'standardize_names', 'enrich_metadata'],
            'records_processed': 10000,
            'records_output': 9500
        }
    )
    
    print(f"Lineage Tracking: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Source: {result.source}")
    print(f"Target: {result.target}")
    print(f"Transformation: {result.transformation}")
    print(f"Lineage ID: {result.lineage_id}")
    
    # Track lineage for venue data
    result2 = governance.track_etl_lineage(
        source_table='raw_data.ticketmaster_venues',
        target_table='concert_data.venues',
        etl_job_name='normalize_venue_data',
        transformation_details={
            'operations': ['geocode', 'standardize_addresses', 'validate_capacity'],
            'records_processed': 5000,
            'records_output': 4950
        }
    )
    
    print(f"\nSecond Lineage Tracking: {'SUCCESS' if result2.success else 'FAILED'}")
    print(f"Source: {result2.source}")
    print(f"Target: {result2.target}")
    
    return [result, result2]


def example_audit_logging():
    """Example: Log data access for audit purposes."""
    print("\n=== Audit Logging ===\n")
    
    governance = DataGovernanceService(region_name='us-east-1')
    
    # Log various data access operations
    operations = [
        ('analyst-user', 'concert_data.artists', 'SELECT'),
        ('data-scientist', 'concert_data.concerts', 'SELECT'),
        ('data-engineer', 'concert_data.venues', 'INSERT'),
        ('ml-service', 'concert_data.ticket_sales', 'SELECT')
    ]
    
    results = []
    for user, resource, action in operations:
        result = governance.audit_data_access(
            user=user,
            resource=resource,
            action=action
        )
        results.append(result)
        
        status = "✓" if result.success else "✗"
        print(f"{status} Audited: {user} performed {action} on {resource}")
    
    return results


def example_get_audit_report():
    """Example: Generate audit report for recent activity."""
    print("\n=== Generating Audit Report ===\n")
    
    governance = DataGovernanceService(region_name='us-east-1')
    
    # Get audit logs for last 7 days
    logs = governance.get_access_audit_report(days=7)
    
    print(f"Total audit entries (last 7 days): {len(logs)}")
    
    if logs:
        print("\nRecent audit entries:")
        for log in logs[:5]:  # Show first 5
            print(f"  - {log.get('user')} performed {log.get('action')} "
                  f"on {log.get('resource')} at {log.get('timestamp')}")
    
    # Get filtered report for specific user
    user_logs = governance.get_access_audit_report(
        days=7,
        user='analyst-user'
    )
    
    print(f"\nAudit entries for 'analyst-user': {len(user_logs)}")
    
    return logs


def example_get_lineage_report():
    """Example: Get data lineage report for a table."""
    print("\n=== Data Lineage Report ===\n")
    
    governance = DataGovernanceService(region_name='us-east-1')
    
    # Get lineage for artists table
    lineage = governance.get_lineage_report(
        resource='concert_data.artists',
        direction='both'
    )
    
    print(f"Lineage for concert_data.artists:")
    print(f"  Upstream sources: {len(lineage.get('upstream', []))}")
    print(f"  Downstream targets: {len(lineage.get('downstream', []))}")
    
    if lineage.get('upstream'):
        print("\n  Upstream lineage:")
        for item in lineage['upstream'][:3]:  # Show first 3
            print(f"    - {item.get('source')} -> {item.get('target')}")
            print(f"      Transformation: {item.get('transformation')}")
    
    return lineage


def example_compliance_check():
    """Example: Check dataset compliance with regulations."""
    print("\n=== Compliance Checking ===\n")
    
    governance = DataGovernanceService(region_name='us-east-1')
    
    # Check compliance for artists table
    result = governance.check_compliance(
        dataset='concert_data.artists',
        regulations=['AUDIT_REQUIRED', 'ACCESS_CONTROL', 'LINEAGE_TRACKING']
    )
    
    print(f"Compliance Status: {'COMPLIANT' if result.compliant else 'NON-COMPLIANT'}")
    print(f"Dataset: {result.dataset}")
    print(f"Regulations Checked: {', '.join(result.regulations)}")
    
    if result.violations:
        print("\nViolations Found:")
        for violation in result.violations:
            print(f"  ✗ {violation}")
    else:
        print("\n✓ No violations found")
    
    return result


def example_governance_summary():
    """Example: Get overall governance summary."""
    print("\n=== Governance Summary ===\n")
    
    governance = DataGovernanceService(region_name='us-east-1')
    
    summary = governance.get_governance_summary()
    
    print(f"Audit logs (last 7 days): {summary['audit_logs_last_7_days']}")
    print(f"Total permissions configured: {summary['total_permissions']}")
    print(f"Report generated at: {summary['timestamp']}")
    
    return summary


def run_all_examples():
    """Run all governance examples."""
    print("=" * 60)
    print("DATA GOVERNANCE SERVICE EXAMPLES")
    print("=" * 60)
    
    try:
        # Note: These examples require actual AWS credentials and resources
        # Uncomment the examples you want to run
        
        # example_setup_permissions()
        # example_grant_table_access()
        # example_register_catalog()
        # example_track_lineage()
        # example_audit_logging()
        # example_get_audit_report()
        # example_get_lineage_report()
        # example_compliance_check()
        # example_governance_summary()
        
        print("\n" + "=" * 60)
        print("Examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error running examples: {str(e)}")
        raise


if __name__ == '__main__':
    # Run specific example
    print("To run examples, uncomment the desired function calls in run_all_examples()")
    print("\nAvailable examples:")
    print("  - example_setup_permissions()")
    print("  - example_grant_table_access()")
    print("  - example_register_catalog()")
    print("  - example_track_lineage()")
    print("  - example_audit_logging()")
    print("  - example_get_audit_report()")
    print("  - example_get_lineage_report()")
    print("  - example_compliance_check()")
    print("  - example_governance_summary()")
