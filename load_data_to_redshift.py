#!/usr/bin/env python3
"""
Load synthetic data from S3 into Redshift.
"""
import sys
import psycopg2
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redshift connection details from environment
REDSHIFT_HOST = os.getenv('AWS_REDSHIFT_HOST')
REDSHIFT_PORT = os.getenv('AWS_REDSHIFT_PORT', '5439')
REDSHIFT_DB = os.getenv('AWS_REDSHIFT_DATABASE', 'concerts')
REDSHIFT_USER = os.getenv('AWS_REDSHIFT_USER', 'admin')
REDSHIFT_PASSWORD = os.getenv('AWS_REDSHIFT_PASSWORD')
REDSHIFT_IAM_ROLE = os.getenv('REDSHIFT_IAM_ROLE_ARN')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# S3 paths
S3_BUCKET = 'concert-data-raw'
S3_PREFIX = 'synthetic-data'

def load_data():
    """Load data from S3 to Redshift using COPY command."""
    
    logger.info("=" * 60)
    logger.info("Loading Data from S3 to Redshift")
    logger.info("=" * 60)
    
    # Connect to Redshift
    logger.info(f"Connecting to Redshift at {REDSHIFT_HOST}...")
    conn = psycopg2.connect(
        host=REDSHIFT_HOST,
        port=REDSHIFT_PORT,
        database=REDSHIFT_DB,
        user=REDSHIFT_USER,
        password=REDSHIFT_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    logger.info("✓ Connected to Redshift")
    
    # Tables to load
    tables = {
        'artists': f's3://{S3_BUCKET}/synthetic-csv/artists.csv',
        'venues': f's3://{S3_BUCKET}/synthetic-csv/venues.csv',
        'concerts': f's3://{S3_BUCKET}/synthetic-csv/concerts.csv',
        'ticket_sales': f's3://{S3_BUCKET}/synthetic-csv/ticket_sales.csv'
    }
    
    for table, s3_path in tables.items():
        logger.info(f"\nLoading {table} from {s3_path}...")
        
        # Truncate existing data
        truncate_sql = f"TRUNCATE TABLE concert_dw.{table};"
        try:
            cursor.execute(truncate_sql)
            logger.info(f"  Truncated existing data in {table}")
        except Exception as e:
            logger.warning(f"  Could not truncate {table}: {e}")
        
        # COPY command
        copy_sql = f"""
        COPY concert_dw.{table}
        FROM '{s3_path}'
        IAM_ROLE '{REDSHIFT_IAM_ROLE}'
        CSV
        IGNOREHEADER 1
        REGION '{AWS_REGION}'
        TIMEFORMAT 'auto'
        DATEFORMAT 'auto';
        """
        
        try:
            cursor.execute(copy_sql)
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM concert_dw.{table};")
            count = cursor.fetchone()[0]
            logger.info(f"  ✓ Loaded {count:,} rows into {table}")
            
        except Exception as e:
            logger.error(f"  ✗ Failed to load {table}: {e}")
            continue
    
    # Verify data
    logger.info("\n" + "=" * 60)
    logger.info("Data Load Summary")
    logger.info("=" * 60)
    
    for table in tables.keys():
        cursor.execute(f"SELECT COUNT(*) FROM concert_dw.{table};")
        count = cursor.fetchone()[0]
        logger.info(f"  {table}: {count:,} rows")
    
    cursor.close()
    conn.close()
    
    logger.info("\n✓ Data loading completed!")

if __name__ == '__main__':
    if not REDSHIFT_HOST or not REDSHIFT_PASSWORD or not REDSHIFT_IAM_ROLE:
        logger.error("Missing required environment variables:")
        logger.error("  AWS_REDSHIFT_HOST")
        logger.error("  AWS_REDSHIFT_PASSWORD")
        logger.error("  REDSHIFT_IAM_ROLE_ARN")
        sys.exit(1)
    
    load_data()
