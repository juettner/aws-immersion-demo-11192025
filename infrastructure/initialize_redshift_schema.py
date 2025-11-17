#!/usr/bin/env python3
"""
Initialize Redshift schema and stored procedures.
This script sets up the complete data warehouse structure.
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.redshift_service import RedshiftService
from src.config.settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_configuration():
    """Validate that all required configuration is present."""
    logger.info("Validating configuration...")
    
    settings = Settings.from_env()
    
    # Check if we have Redshift host from environment
    redshift_host = os.getenv('AWS_REDSHIFT_HOST')
    
    required_settings = {
        'redshift_host': redshift_host,
        'redshift_database': settings.aws.redshift_database,
        'redshift_user': settings.aws.redshift_user,
        'redshift_password': settings.aws.redshift_password,
        'aws_region': settings.aws.region
    }
    
    missing = [key for key, value in required_settings.items() if not value]
    
    if missing:
        logger.error(f"Missing required configuration: {', '.join(missing)}")
        logger.error("Please set the following environment variables:")
        for key in missing:
            env_var = f"AWS_{key.upper()}"
            logger.error(f"  {env_var}")
        return False
    
    logger.info("✓ Configuration validated")
    return True


def initialize_schema():
    """Initialize the Redshift schema."""
    logger.info("Initializing Redshift data warehouse schema...")
    
    try:
        # Create service instance
        settings = Settings.from_env()
        redshift_service = RedshiftService(settings)
        
        # Initialize data warehouse
        logger.info("Creating schema, tables, and stored procedures...")
        results = redshift_service.initialize_data_warehouse()
        
        # Display results
        logger.info("\nInitialization Results:")
        for component, success in results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} {component}: {'Success' if success else 'Failed'}")
        
        if all(results.values()):
            logger.info("\n✓ Data warehouse initialized successfully!")
            
            # Get status
            logger.info("\nGetting data warehouse status...")
            status = redshift_service.get_data_warehouse_status()
            
            logger.info("\nTable Status:")
            for table_name, table_info in status.get('tables', {}).items():
                if 'error' in table_info:
                    logger.warning(f"  ✗ {table_name}: {table_info['error']}")
                else:
                    exists = "✓" if table_info.get('exists') else "✗"
                    logger.info(f"  {exists} {table_name}: {table_info.get('row_count', 0)} rows")
            
            return True
        else:
            logger.error("\n✗ Some components failed to initialize")
            return False
            
    except Exception as e:
        logger.error(f"Failed to initialize schema: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'redshift_service' in locals():
            redshift_service.close()


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Redshift Data Warehouse Schema Initialization")
    logger.info("=" * 60)
    
    # Validate configuration
    if not validate_configuration():
        logger.error("\nConfiguration validation failed. Exiting.")
        sys.exit(1)
    
    # Initialize schema
    if initialize_schema():
        logger.info("\n" + "=" * 60)
        logger.info("Schema initialization completed successfully!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Load data from S3 using RedshiftService.load_data_from_s3()")
        logger.info("2. Run analytics calculations using RedshiftService.run_analytics_calculations()")
        logger.info("3. Query insights using the various get_*_insights() methods")
        sys.exit(0)
    else:
        logger.error("\nSchema initialization failed. Please check the logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
