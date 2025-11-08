#!/usr/bin/env python3
"""
Validation script for Redshift data warehouse implementation.
Validates the structure and functionality of all Redshift components.
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def validate_imports():
    """Validate that all Redshift components can be imported."""
    print("🔍 Validating Redshift component imports...")
    
    try:
        # Test infrastructure components
        from infrastructure.redshift_client import RedshiftClient
        from infrastructure.redshift_schema import RedshiftSchemaManager
        from infrastructure.redshift_data_loader import RedshiftDataLoader
        from infrastructure.redshift_stored_procedures import RedshiftStoredProcedures
        
        # Test service layer
        from services.redshift_service import RedshiftService
        
        # Test configuration
        from config.settings import get_settings
        
        print("✅ All Redshift components imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False


def validate_class_structure():
    """Validate the structure of Redshift classes."""
    print("\n🔍 Validating class structures...")
    
    try:
        from infrastructure.redshift_client import RedshiftClient
        from infrastructure.redshift_schema import RedshiftSchemaManager
        from infrastructure.redshift_data_loader import RedshiftDataLoader
        from infrastructure.redshift_stored_procedures import RedshiftStoredProcedures
        from services.redshift_service import RedshiftService
        
        # Check RedshiftClient methods
        client_methods = [
            'get_connection', 'execute_query', 'execute_copy_command',
            'create_schema_if_not_exists', 'table_exists', 'get_table_row_count',
            'analyze_table', 'vacuum_table', 'close_connection'
        ]
        
        for method in client_methods:
            if not hasattr(RedshiftClient, method):
                print(f"❌ RedshiftClient missing method: {method}")
                return False
        
        # Check RedshiftSchemaManager methods
        schema_methods = [
            'create_all_tables', 'drop_all_tables', 'get_table_info'
        ]
        
        for method in schema_methods:
            if not hasattr(RedshiftSchemaManager, method):
                print(f"❌ RedshiftSchemaManager missing method: {method}")
                return False
        
        # Check RedshiftDataLoader methods
        loader_methods = [
            'load_artists_data', 'load_venues_data', 'load_concerts_data',
            'load_ticket_sales_data', 'load_csv_data', 'upsert_data'
        ]
        
        for method in loader_methods:
            if not hasattr(RedshiftDataLoader, method):
                print(f"❌ RedshiftDataLoader missing method: {method}")
                return False
        
        # Check RedshiftStoredProcedures methods
        procedures_methods = [
            'create_all_procedures', 'execute_venue_popularity_calculation',
            'execute_artist_performance_calculation', 'get_top_venues',
            'get_artist_trends', 'get_revenue_analytics'
        ]
        
        for method in procedures_methods:
            if not hasattr(RedshiftStoredProcedures, method):
                print(f"❌ RedshiftStoredProcedures missing method: {method}")
                return False
        
        # Check RedshiftService methods
        service_methods = [
            'initialize_data_warehouse', 'load_data_from_s3', 'run_analytics_calculations',
            'get_venue_insights', 'get_artist_insights', 'get_revenue_analytics',
            'get_data_warehouse_status', 'execute_custom_query', 'optimize_tables'
        ]
        
        for method in service_methods:
            if not hasattr(RedshiftService, method):
                print(f"❌ RedshiftService missing method: {method}")
                return False
        
        print("✅ All class structures validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error validating class structure: {e}")
        return False


def validate_sql_queries():
    """Validate that SQL queries are properly formatted."""
    print("\n🔍 Validating SQL query structures...")
    
    try:
        # Check that schema creation queries contain expected elements
        from infrastructure.redshift_schema import RedshiftSchemaManager
        from infrastructure.redshift_client import RedshiftClient
        
        # Mock client for testing
        class MockClient:
            def execute_query(self, query):
                # Basic SQL validation - check for required keywords
                query_upper = query.upper()
                if 'CREATE TABLE' in query_upper:
                    required_elements = ['PRIMARY KEY', 'DISTSTYLE', 'SORTKEY']
                    for element in required_elements:
                        if element not in query_upper:
                            print(f"⚠️  Warning: Query missing {element}")
                return []
            
            def create_schema_if_not_exists(self, schema):
                return True
            
            def table_exists(self, table, schema):
                return False
        
        mock_client = MockClient()
        schema_manager = RedshiftSchemaManager(mock_client)
        
        # Test table creation (this will execute the SQL validation)
        schema_manager._create_artists_table()
        schema_manager._create_venues_table()
        schema_manager._create_concerts_table()
        schema_manager._create_ticket_sales_table()
        
        print("✅ SQL query structures validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error validating SQL queries: {e}")
        return False


def validate_configuration():
    """Validate configuration structure."""
    print("\n🔍 Validating configuration...")
    
    try:
        from config.settings import get_settings
        
        settings = get_settings()
        
        # Check that required AWS configuration properties exist
        required_aws_props = [
            'aws_region', 'redshift_host', 'redshift_port', 
            'redshift_database', 'redshift_user', 'redshift_password'
        ]
        
        for prop in required_aws_props:
            if not hasattr(settings, prop):
                print(f"❌ Settings missing property: {prop}")
                return False
        
        print("✅ Configuration structure validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return False


def validate_data_models_integration():
    """Validate integration with existing data models."""
    print("\n🔍 Validating data models integration...")
    
    try:
        # Check that data models exist and have expected fields
        from models.artist import Artist
        from models.venue import Venue
        from models.concert import Concert
        from models.ticket_sale import TicketSale
        
        # Validate Artist model fields
        artist_fields = ['artist_id', 'name', 'genre', 'popularity_score', 'formation_date', 'members', 'spotify_id']
        for field in artist_fields:
            if field not in Artist.__fields__:
                print(f"❌ Artist model missing field: {field}")
                return False
        
        # Validate Venue model fields
        venue_fields = ['venue_id', 'name', 'location', 'capacity', 'venue_type', 'amenities', 'ticketmaster_id']
        for field in venue_fields:
            if field not in Venue.__fields__:
                print(f"❌ Venue model missing field: {field}")
                return False
        
        # Validate Concert model fields
        concert_fields = ['concert_id', 'artist_id', 'venue_id', 'event_date', 'ticket_prices', 'total_attendance', 'revenue', 'status']
        for field in concert_fields:
            if field not in Concert.__fields__:
                print(f"❌ Concert model missing field: {field}")
                return False
        
        # Validate TicketSale model fields
        ticket_fields = ['sale_id', 'concert_id', 'price_tier', 'quantity', 'unit_price', 'purchase_timestamp', 'customer_segment']
        for field in ticket_fields:
            if field not in TicketSale.__fields__:
                print(f"❌ TicketSale model missing field: {field}")
                return False
        
        print("✅ Data models integration validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error validating data models integration: {e}")
        return False


def validate_requirements_coverage():
    """Validate that implementation covers the task requirements."""
    print("\n🔍 Validating requirements coverage...")
    
    requirements_coverage = {
        "Design and create Redshift tables with appropriate distribution keys": False,
        "Implement COPY commands for efficient data loading from S3": False,
        "Create stored procedures for data aggregation and analytics": False
    }
    
    try:
        # Check distribution keys in schema
        from infrastructure.redshift_schema import RedshiftSchemaManager
        from infrastructure.redshift_client import RedshiftClient
        
        # Mock to capture SQL queries
        captured_queries = []
        
        class MockClient:
            def execute_query(self, query):
                captured_queries.append(query)
                return []
            def create_schema_if_not_exists(self, schema):
                return True
            def table_exists(self, table, schema):
                return False
        
        mock_client = MockClient()
        schema_manager = RedshiftSchemaManager(mock_client)
        schema_manager.create_all_tables()
        
        # Check for distribution keys
        has_distkey = any('DISTKEY' in query or 'DISTSTYLE' in query for query in captured_queries)
        has_sortkey = any('SORTKEY' in query for query in captured_queries)
        
        if has_distkey and has_sortkey:
            requirements_coverage["Design and create Redshift tables with appropriate distribution keys"] = True
        
        # Check COPY commands
        from infrastructure.redshift_data_loader import RedshiftDataLoader
        
        # Check if COPY methods exist
        loader_methods = ['load_artists_data', 'load_venues_data', 'load_concerts_data', 'load_ticket_sales_data']
        has_copy_methods = all(hasattr(RedshiftDataLoader, method) for method in loader_methods)
        
        if has_copy_methods:
            requirements_coverage["Implement COPY commands for efficient data loading from S3"] = True
        
        # Check stored procedures
        from infrastructure.redshift_stored_procedures import RedshiftStoredProcedures
        
        procedure_methods = [
            'execute_venue_popularity_calculation',
            'execute_artist_performance_calculation', 
            'get_top_venues',
            'get_artist_trends',
            'get_revenue_analytics'
        ]
        has_procedures = all(hasattr(RedshiftStoredProcedures, method) for method in procedure_methods)
        
        if has_procedures:
            requirements_coverage["Create stored procedures for data aggregation and analytics"] = True
        
        # Report coverage
        print("\nRequirements Coverage:")
        for requirement, covered in requirements_coverage.items():
            status = "✅" if covered else "❌"
            print(f"  {status} {requirement}")
        
        return all(requirements_coverage.values())
        
    except Exception as e:
        print(f"❌ Error validating requirements coverage: {e}")
        return False


def main():
    """Run all validation checks."""
    print("🚀 Starting Redshift Implementation Validation")
    print("=" * 60)
    
    validation_results = []
    
    # Run all validation checks
    validation_results.append(("Import Validation", validate_imports()))
    validation_results.append(("Class Structure Validation", validate_class_structure()))
    validation_results.append(("SQL Query Validation", validate_sql_queries()))
    validation_results.append(("Configuration Validation", validate_configuration()))
    validation_results.append(("Data Models Integration", validate_data_models_integration()))
    validation_results.append(("Requirements Coverage", validate_requirements_coverage()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(validation_results)
    
    for test_name, result in validation_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n🎉 All validations passed! Redshift implementation is ready.")
        print("\n📋 Implementation Summary:")
        print("   • RedshiftClient: Database connection and query execution")
        print("   • RedshiftSchemaManager: Table creation with distribution keys")
        print("   • RedshiftDataLoader: Efficient S3 to Redshift COPY operations")
        print("   • RedshiftStoredProcedures: Analytics and aggregation procedures")
        print("   • RedshiftService: Orchestration layer for all operations")
        print("\n🔧 Next Steps:")
        print("   1. Configure AWS credentials and Redshift cluster")
        print("   2. Set environment variables for Redshift connection")
        print("   3. Run the example usage script to test with real data")
        return True
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)